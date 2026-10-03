import random

from game.clock import WorldClock
from game.effects.effect_context import EffectContext
from game.effects.effect_reader import EffectReader
from game.event_manager import EventManager
from game.event_resolver import EventResolver
from game.field import Field
from game.fog_of_war import FogOfWar
from game.game_config import (
    PLAYER_BASE_SPEED, GOLD_YIELD_INTERVAL,
    SILVER_RESPAWN_INTERVAL, EVENT_RESPAWN_INTERVAL,
)
from game.generation.field_texture import FieldTextureGenerator
from game.generation.gold_cell_generator import GoldCellGenerator
from game.generation.obstacle_generator import ObstacleGenerator
from game.player import Player
from game.resource_manager import ResourceManager

class GameWorld:
    """Игровой мир без отрисовки: поле, акторы, менеджеры, часы и правила партии."""

    def __init__(self, settings, player_palette):
        """player_palette: список (color_key, rgb) по порядку игроков."""
        self.settings = settings
        self.winner = None
        self.on_event_triggered = None  # (player, event_definition)

        self._pending_event_players = []  # игроки, которых телепортировало на клетку с событием

        self.clock = WorldClock()
        self.effect_context = EffectContext(self)
        self.event_resolver = EventResolver(self)

        self.field = Field(settings.map_width, settings.map_height)
        self._generate_field()

        self.resource_manager = ResourceManager(
            self.field, settings.player_count,
            settings.win_gold_required, settings.win_silver_required,
        )
        self.fog_of_war = FogOfWar(self.field, settings.vision_radius)
        self.players = self._create_players(player_palette)
        self.human = self.players[0]

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

        self.clock.every(GOLD_YIELD_INTERVAL, self.resource_manager.tick_gold_deposits)
        self.clock.every(SILVER_RESPAWN_INTERVAL, self.resource_manager.respawn_silver)
        self.clock.every(EVENT_RESPAWN_INTERVAL, self.event_manager.respawn)

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

    def _create_players(self, player_palette):
        players = []
        for i in range(self.settings.player_count):
            color_key, color = player_palette[i]
            player = Player(
                self.field, start_cell=self.field.start_cell, base_speed=PLAYER_BASE_SPEED,
                color_key=color_key, color=color,
            )
            player.on_cell_reached = self._make_cell_reached_handler(player)
            self.fog_of_war.update_player(player)
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
        self.clock.update(dt)

        for player in self.players:
            EffectReader.update(player, dt, self.effect_context)
            EffectReader.tick(player, dt, self.effect_context)
            player.trim_blocked_path()
            player.update(dt)

        self._refresh_dirty_vision()
        self._check_finish()
        self._flush_pending_events()

        for player in self.players:
            player.warning_message = self.resource_manager.missing_requirements_message(player)

    def _refresh_dirty_vision(self):
        for player in self.players:
            if player.vision_dirty:
                player.vision_dirty = False
                self.fog_of_war.update_player(player)

    def _check_finish(self):
        for player in self.players:
            if self.resource_manager.check_win(player):
                player.path = []
                self.winner = player
                return

    def _flush_pending_events(self):
        """Открывает событие под игроком, которого телепортировало на его клетку.
        Откладываем, чтобы попап не открывался поверх другого попапа."""
        while self._pending_event_players:
            player = self._pending_event_players.pop(0)
            event = self.event_manager.consume_at(player.grid_x, player.grid_y)
            if event is not None:
                self._trigger_event(player, event)
                return

    # --- Обработка клетки ---

    def _make_cell_reached_handler(self, player):
        def handler():
            self._arrive_at_cell(player)
        return handler

    def _arrive_at_cell(self, player, defer_events=False):
        """Единая обработка прихода на клетку (шаг или телепорт)."""
        self.fog_of_war.update_player(player)
        self.resource_manager.collect_at(player)
        EffectReader.notify_cell_reached(player, self.effect_context)

        pos = (player.grid_x, player.grid_y)
        if defer_events:
            if self.event_manager.get_event_at(pos) is not None and player not in self._pending_event_players:
                self._pending_event_players.append(player)
            return
        event = self.event_manager.consume_at(*pos)
        if event is not None:
            self._trigger_event(player, event)

    def _trigger_event(self, player, event):
        """Обрывает маршрут и просит слой представления показать событие."""
        player.path = []
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
        self._arrive_at_cell(player, defer_events=True)

    def relocate_player_to_nearest_free_cell(self, player):
        cell = (player.grid_x, player.grid_y)
        if self.field.is_free(*cell):
            return
        self._teleport_player_to(player, self.field.nearest_free_cell(*cell))