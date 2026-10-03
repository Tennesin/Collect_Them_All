import pygame
from settings import *
from widgets import get_font
from game.rendering.camera import Camera
from game.world import GameWorld
from game.tween import Tween, ease_out_cubic
from game.input_handler import InputHandler
from game.rendering.renderer import Renderer
from game.ui import PlayerPanel, NotificationFeed
from scene.scenes import Scene
from bot.bot_factory import create_bot_controller

class GameplayScene(Scene):
    """Слой представления: камера, ввод, отрисовка, оверлеи. Правила живут в GameWorld."""

    def __init__(self, manager, settings):
        super().__init__(manager)
        self.settings = settings
        self._victory_alpha = 0
        self._victory_fade = None
        screen = self.manager.app.screen

        palette = [(key, PLAYER_COLORS[key]) for key in PLAYER_COLOR_ORDER]
        self.world = GameWorld(settings, palette, controller_factory=create_bot_controller)
        self.human = self.world.human

        # Алиасы, чтобы Renderer и сцены-оверлеи не менялись
        self.field = self.world.field
        self.players = self.world.players
        self.resource_manager = self.world.resource_manager
        self.event_manager = self.world.event_manager

        self.camera = Camera(GAME_AREA_WIDTH, SCREEN_HEIGHT, settings.map_width, settings.map_height,
                             INITIAL_SCALE, MAX_SCALE, smooth_speed=CAMERA_SMOOTH_SPEED)
        self.world.on_event_triggered = self._on_event_triggered
        self.notifications = NotificationFeed()
        self.world.on_bot_event = self._on_bot_event

        self.input_handler = InputHandler(self.camera, self.field, self.human)
        self.renderer = Renderer(
            screen, self.camera, self.field, self.players, self.human,
            self.input_handler, self.resource_manager, self.event_manager,
        )
        self.player_panel = PlayerPanel(self.human, self.resource_manager, self.world.clock)

        self.camera.center_on(self.human.pos_x, self.human.pos_y, instant=True)

    def _on_event_triggered(self, player, event):
        from scene.scene_event import EventScene
        self.manager.push(EventScene(self.manager, self, player, event))

    def _on_bot_event(self, player, event, outcome):
        """Показываем только то, что человек видит своими глазами."""
        if (player.grid_x, player.grid_y) not in self.human.visible_cells:
            return
        parts = []
        if outcome.gold_delta:
            parts.append(f"{outcome.gold_delta:+d} зол.")
        if outcome.silver_delta:
            parts.append(f"{outcome.silver_delta:+d} сер.")
        if outcome.displacement_cells:
            parts.append("отброшен")
        title = EVENT_TITLES_RU.get(event.id, event.id)
        result = ", ".join(parts) if parts else "без добычи"
        self.notifications.add(f"{PLAYER_NAMES_RU[player.color_key]}: {title} ({result})", player.color)

    # --- Жизненный цикл сцены ---

    def on_pause(self):
        # MOUSEBUTTONUP уйдёт в другую сцену, поэтому драг сбрасываем здесь (п. 3.8)
        self.input_handler.dragging = False

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            if self.world.winner is not None:
                from scene.scene_main_menu import MainMenuScene
                self.manager.switch_to(MainMenuScene(self.manager))
            else:
                from scene.scene_pause import PauseScene
                self.manager.push(PauseScene(self.manager, self))
            return
        if self.world.winner is not None:
            return
        self.input_handler.handle_event(event)

    def update(self, dt):
        if self.world.winner is not None:
            if self._victory_fade is None:
                self._victory_fade = Tween(0, 255, VICTORY_FADE_DURATION, ease_out_cubic)
            self._victory_alpha = self._victory_fade.update(dt)
            return

        self.input_handler.process_held_keys()
        self.update_world_only(dt)

    def update_world_only(self, dt):
        """Шаг мира и камеры без обработки ввода. Его же вызывают оверлеи
        (окно события), чтобы время в мире не останавливалось."""
        if self.world.winner is not None:
            return
        self.world.update(dt)
        self.notifications.update(dt)
        if self.camera.follow:
            self.camera.center_on(self.human.pos_x, self.human.pos_y)
        self.camera.update(dt)

    # --- Отрисовка ---

    def draw(self, screen):
        self.renderer.draw()
        self.notifications.draw(screen)
        self.player_panel.draw(screen)
        if self.world.winner is not None:
            self._draw_victory_overlay(screen)

    def _draw_victory_overlay(self, screen):
        winner = self.world.winner
        content = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        content.fill(PAUSE_OVERLAY_COLOR)

        name = PLAYER_NAMES_RU[winner.color_key]
        kind = "бот" if winner.is_bot else "игрок"
        title_surf = get_font(FONT_SIZE_TITLE - 8).render(f"Победил {kind}: {name}", True, winner.color)
        content.blit(title_surf, title_surf.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 20)))

        hint_surf = get_font(FONT_SIZE_HINT + 4).render("Esc — выйти в меню", True, TEXT_COLOR)
        content.blit(hint_surf, hint_surf.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 140)))

        content.set_alpha(int(self._victory_alpha))
        screen.blit(content, (0, 0))