import pygame
from settings import *
from widgets import get_font
from game.game_config import TURN_MAX_MOVES, TURN_TIME_SECONDS
from game.camera import Camera
from game.field import Field
from game.obstacle_generator import ObstacleGenerator
from game.gold_cell_generator import GoldCellGenerator
from game.resource_manager import ResourceManager
from game.player import Player
from game.turn_manager import TurnManager
from game.input_handler import InputHandler
from game.renderer import Renderer
from game.ui import PlayerPanel
from scene.scenes import Scene

class GameplayScene(Scene):
    """Сборка и цикл собственно игры на поле. Создаёт нужное количество
    игроков (Красный, Синий, Жёлтый, Оранжевый, Розовый — по очереди),
    ботов пока нет: каждым по очереди управляет один и тот же человек."""

    def __init__(self, manager, settings):
        super().__init__(manager)
        self.settings = settings
        self.paused = False
        self.winner = None
        screen = self.manager.app.screen

        self.field = Field(settings.map_width, settings.map_height)

        # Золотые клетки расставляем ДО обычных препятствий: их короба сразу
        # резервируют себе место (Field.reserved_cells), и ObstacleGenerator
        # их уже не тронет.
        GoldCellGenerator(self.field).generate()

        total_cells = settings.map_width * settings.map_height
        max_obstacle_cells = int(total_cells * settings.obstacle_fraction)
        ObstacleGenerator(self.field, max_obstacle_cells).generate()

        # Динамика ресурсов (накопленное золото, текущее серебро) — отдельно от Field.
        self.resource_manager = ResourceManager(self.field)

        # Камере отдаём только ширину игровой зоны (без панели справа) —
        # так поле не залезает под PlayerPanel.
        self.camera = Camera(GAME_AREA_WIDTH, SCREEN_HEIGHT, settings.map_width, settings.map_height,
                              INITIAL_SCALE, MAX_SCALE)

        # --- Игроки: все стартуют в одной клетке, поэтому сразу видно "слои" ---
        start_cell = (0, 0)
        self.players = []
        for i in range(settings.player_count):
            color_key = PLAYER_COLOR_ORDER[i]
            player = Player(self.field, start_cell=start_cell, speed=PLAYER_SPEED, color_key=color_key)
            player.on_move = self.camera.center_on
            player.on_cell_reached = self._make_cell_reached_handler(player)
            self.players.append(player)

        # --- Очередь ходов ---
        self.turn_manager = TurnManager(self.players, max_moves=TURN_MAX_MOVES, turn_time=TURN_TIME_SECONDS)
        self.turn_manager.on_turn_change = self._on_turn_change
        self.turn_manager.on_cycle_complete = self.resource_manager.on_cycle_complete

        self.input_handler = InputHandler(self.camera, self.field, self.turn_manager)
        self.renderer = Renderer(
            screen, self.camera, self.field, self.players,
            self.turn_manager, self.input_handler, self.resource_manager,
        )
        self.player_panel = PlayerPanel(self.turn_manager)

        self.camera.center_on(self.players[0].pos_x, self.players[0].pos_y)

    def _make_cell_reached_handler(self, player):
        """Собирает воедино всё, что должно произойти при входе игрока в
        новую клетку: списание хода, сбор ресурсов и проверку победы."""
        def handler():
            self.turn_manager.consume_move()
            self.resource_manager.collect_at(player)
            if self.winner is None and self.resource_manager.check_win(player):
                self.winner = player
        return handler

    def _on_turn_change(self, new_player):
        """Колбэк TurnManager'а: очищаем чужой предпросмотр пути и переносим
        камеру на игрока, чей ход начался."""
        self.input_handler.clear_preview()
        self.camera.center_on(new_player.pos_x, new_player.pos_y)

    def on_pause(self):
        """Сцена уходит под паузу (например, поверх положили PauseScene):
        явно останавливаем игровое время и движение игрока."""
        self.paused = True

    def on_resume(self):
        """Сцена снова становится верхней после снятия паузы."""
        self.paused = False

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            if self.winner is not None:
                from scene.scene_main_menu import MainMenuScene
                self.manager.switch_to(MainMenuScene(self.manager))
            else:
                from scene.scene_pause import PauseScene
                self.manager.push(PauseScene(self.manager, self))
            return
        if self.winner is not None:
            return
        self.input_handler.handle_event(event)

    def update(self, dt):
        if self.paused or self.winner is not None:
            return
        self.input_handler.process_held_keys()
        self.turn_manager.update(dt)

        current = self.turn_manager.current_player
        if current.moving:
            current.update(dt)

    def draw(self, screen):
        self.renderer.draw()
        self.player_panel.draw(screen)
        if self.winner is not None:
            self._draw_victory_overlay(screen)

    def _draw_victory_overlay(self, screen):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill(PAUSE_OVERLAY_COLOR)
        screen.blit(overlay, (0, 0))

        name = PLAYER_NAMES_RU[self.winner.color_key]
        title_surf = get_font(FONT_SIZE_TITLE - 8).render(f"Победил игрок: {name}", True, self.winner.color)
        screen.blit(title_surf, title_surf.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 20)))

        hint_surf = get_font(FONT_SIZE_HINT + 4).render("Esc — выйти в меню", True, TEXT_COLOR)
        screen.blit(hint_surf, hint_surf.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 30)))