import random

from game.effects.effect_context import EffectContext
from game.effects.effect_reader import EffectReader
from game.event_manager import EventManager
from game.field import Field
from game.fog_of_war import FogOfWar
from game.game_config import FINISH_MODE_INSTANT
from game.generation.field_texture import FieldTextureGenerator
from game.generation.gold_cell_generator import GoldCellGenerator
from game.generation.obstacle_generator import ObstacleGenerator
from game.player import Player
from game.resource_manager import ResourceManager
from game.turn_manager import TurnManager

class GameWorld:
    """Игровой мир без отрисовки: поле, акторы, менеджеры и правила партии.
    Сцена лишь вызывает update(dt) и подписывается на колбэки."""

    def __init__(self, settings, player_speed, color_keys):
        self.settings = settings
        self.winner = None
        self.placements = []

        # Колбэки для слоя представления (сцена). Все необязательные.
        self.on_event_triggered = None     # (player, event_definition)
        self.on_turn_changed = None        # (new_player)
        self.on_player_teleported = None   # (player)

        self._pending_event_players = set()

        self.field = Field(settings.map_width, settings.map_height)
        self._generate_field()

        self.resource_manager = ResourceManager(
            self.field, settings.player_count,
            settings.win_gold_required, settings.win_silver_required,
        )
        self.fog_of_war = FogOfWar(self.field, settings.vision_radius)
        self.players = self._create_players(player_speed, color_keys)

        self.event_manager = EventManager(
            self.field, settings.player_count, settings.event_density_fraction
        )
        self.event_manager.bind_dynamic_providers(
            occupied_provider=self._occupied_cells,
            currency_provider=self._currency_cells,
            visible_provider=self._visible_cells_union,
        )
        self.event_manager.respawn()  # первичная раскладка событий

        self.resource_manager.bind_dynamic_providers(
            visible_provider=self._visible_cells_union,
            event_provider=self._active_event_cells,
            occupied_provider=self._occupied_cells,
        )

        self.turn_manager = TurnManager(
            self.players, max_moves=settings.moves_per_turn, turn_time=settings.turn_time_seconds
        )
        self.turn_manager.on_turn_change = self._on_turn_change
        self.turn_manager.on_cycle_complete = self._on_cycle_complete
        self.turn_manager.on_player_turn_end = self._on_player_turn_end

    # --- Построение ---

    def _generate_field(self):
        settings = self.settings
        placed = GoldCellGenerator(self.field, settings.gold_cell_count).generate()
        if placed < settings.gold_cell_count:
            print(
                f"[GameWorld] Не удалось разместить все золотые клетки: "
                f"запрошено {settings.gold_cell_count}, размещено {placed}."
            )
        total_cells = settings.map_width * settings.map_height
        max_obstacle_cells = int(total_cells * settings.obstacle_fraction)
        ObstacleGenerator(self.field, max_obstacle_cells).generate()
        FieldTextureGenerator(self.field).generate()

    def _create_players(self, player_speed, color_keys):
        players = []
        for i in range(self.settings.player_count):
            player = Player(
                self.field, start_cell=self.field.start_cell,
                speed=player_speed, color_key=color_keys[i],
            )
            player.on_cell_reached = self._make_cell_reached_handler(player)
            self.fog_of_war.update_player(player)  # видимость на старте
            players.append(player)
        return players

    # --- Провайдеры для менеджеров ---

    def _occupied_cells(self):
        return {(p.grid_x, p.grid_y) for p in self.players}

    def _currency_cells(self):
        gold_cells = {pos for pos, amount in self.resource_manager.gold_deposits.items() if amount > 0}
        return gold_cells | set(self.resource_manager.silver_cells)

    def _active_event_cells(self):
        return set(self.event_manager.active_events)

    def _visible_cells_union(self):
        visible = set()
        for p in self.players:
            visible |= p.visible_cells
        return visible

    # --- Кадр ---

    def update(self, dt):
        if self.winner is not None:
            return
        self.turn_manager.update(dt)
        current = self.turn_manager.current_player
        if current.moving:
            current.update(dt)
        self._flush_pending_events()

    def _flush_pending_events(self):
        """Открывает отложенное событие, когда его владелец стал текущим игроком и стоит на месте."""
        current = self.turn_manager.current_player
        if current not in self._pending_event_players or current.moving:
            return
        self._pending_event_players.discard(current)
        event = self.event_manager.consume_at(current.grid_x, current.grid_y)
        if event is not None:
            self._trigger_event(current, event)

    # --- Цикл ходов ---

    def _on_cycle_complete(self):
        self.resource_manager.on_cycle_complete()
        self.event_manager.on_cycle_complete()

    def _on_turn_change(self, new_player):
        if self.on_turn_changed:
            self.on_turn_changed(new_player)

    def _on_player_turn_end(self, player):
        """Черёд завершился: тикаем эффекты и сразу пересчитываем обзор (п. 3.2)."""
        player.tick_effects(EffectContext(self))
        self.fog_of_war.update_player(player)

    # --- Обработка клетки ---

    def _make_cell_reached_handler(self, player):
        def handler():
            if self._arrive_at_cell(player):
                return
            self.turn_manager.consume_move()
            player.warning_message = self.resource_manager.missing_requirements_message(player)
        return handler

    def _arrive_at_cell(self, player, defer_events=False):
        """Единая обработка прихода актора на клетку (шаг или телепорт).
        Возвращает True, если игрок финишировал."""
        self.fog_of_war.update_player(player)
        self.resource_manager.collect_at(player)
        EffectReader.notify_cell_reached(player, EffectContext(self))

        if self.winner is None and player not in self.placements and self.resource_manager.check_win(player):
            self._handle_player_finish(player)
            return True

        pos = (player.grid_x, player.grid_y)
        if defer_events:
            if self.event_manager.get_event_at(pos) is not None:
                self._pending_event_players.add(player)
            return False

        event = self.event_manager.consume_at(*pos)
        if event is not None:
            self._trigger_event(player, event)
        return False

    def _trigger_event(self, player, event):
        """Мгновенно обрывает путь и просит слой представления показать событие."""
        player.path = []
        player.moving = False
        if self.on_event_triggered:
            self.on_event_triggered(player, event)

    # --- Перемещения ---

    def displace_player_randomly(self, player, distance):
        directions = [(1, 0), (-1, 0), (0, 1), (0, -1)]
        random.shuffle(directions)
        for dx, dy in directions:
            landing = self._farthest_free_cell(player.grid_x, player.grid_y, dx, dy, distance)
            if landing != (player.grid_x, player.grid_y):
                self._teleport_player_to(player, landing)
                return landing
        return (player.grid_x, player.grid_y)

    def _farthest_free_cell(self, x, y, dx, dy, distance):
        cx, cy = x, y
        for _ in range(distance):
            nx, ny = cx + dx, cy + dy
            if not self.field.in_bounds(nx, ny) or not self.field.is_free(nx, ny):
                break
            cx, cy = nx, ny
        return (cx, cy)

    def _teleport_player_to(self, player, cell):
        player.grid_x, player.grid_y = cell
        player.pos_x = cell[0] + 0.5
        player.pos_y = cell[1] + 0.5
        player.path = []
        player.moving = False
        self._arrive_at_cell(player, defer_events=True)  # п. 3.6
        player.warning_message = self.resource_manager.missing_requirements_message(player)
        if self.on_player_teleported:
            self.on_player_teleported(player)

    def relocate_player_to_nearest_free_cell(self, player):
        cell = (player.grid_x, player.grid_y)
        if self.field.is_free(*cell):
            return
        self._teleport_player_to(player, self.field.nearest_free_cell(*cell))

    def refresh_effects_immediately(self, player):
        self.fog_of_war.update_player(player)
        if player is self.turn_manager.current_player:
            self.turn_manager.recompute_moves_cap()

    # --- Финиш ---

    def _handle_player_finish(self, player):
        player.moving = False
        player.path = []
        self.placements.append(player)

        if self.settings.finish_mode == FINISH_MODE_INSTANT:
            self.winner = player
            return

        self.turn_manager.eliminate(player)
        active_players = [p for p in self.players if p not in self.placements]
        if len(active_players) <= 1:
            if active_players:
                self.placements.append(active_players[0])
            self.winner = self.placements[0]
            return
        self.turn_manager.end_turn_early()