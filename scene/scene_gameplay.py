import pygame
from settings import *
from widgets import get_font
from game.game_config import FINISH_MODE_RANKED
from game.rendering.camera import Camera
from game.world import GameWorld
from game.tween import Tween, ease_out_cubic
from game.input_handler import InputHandler
from game.rendering.renderer import Renderer
from game.ui import PlayerPanel
from scene.scenes import Scene

class GameplayScene(Scene):
    """Слой представления: камера, ввод, отрисовка, оверлеи. Правила живут в GameWorld."""

    def __init__(self, manager, settings):
        super().__init__(manager)
        self.settings = settings
        self._victory_alpha = 0
        self._victory_fade = None
        screen = self.manager.app.screen

        self.world = GameWorld(settings, player_speed=PLAYER_SPEED, color_keys=PLAYER_COLOR_ORDER)

        # Алиасы, чтобы остальной код (Renderer, EventScene, панель) не менялся.
        self.field = self.world.field
        self.players = self.world.players
        self.turn_manager = self.world.turn_manager
        self.resource_manager = self.world.resource_manager
        self.event_manager = self.world.event_manager
        self.fog_of_war = self.world.fog_of_war

        self.camera = Camera(GAME_AREA_WIDTH, SCREEN_HEIGHT, settings.map_width, settings.map_height,
                             INITIAL_SCALE, MAX_SCALE, smooth_speed=CAMERA_SMOOTH_SPEED)
        for player in self.players:
            player.on_move = self.camera.center_on

        self.world.on_event_triggered = self._on_event_triggered
        self.world.on_turn_changed = self._on_turn_changed
        self.world.on_player_teleported = self._on_player_teleported

        self.input_handler = InputHandler(self.camera, self.field, self.turn_manager)
        self.renderer = Renderer(
            screen, self.camera, self.field, self.players,
            self.turn_manager, self.input_handler, self.resource_manager,
            self.event_manager,
        )
        self.player_panel = PlayerPanel(self.turn_manager, self.resource_manager)

        self.camera.center_on(self.players[0].pos_x, self.players[0].pos_y, instant=True)

    # --- Реакции на события мира ---

    def _on_event_triggered(self, player, event):
        self.input_handler.clear_preview()
        from scene.scene_event import EventScene
        self.manager.push(EventScene(self.manager, self, player, event))

    def _on_turn_changed(self, new_player):
        self.input_handler.clear_preview()
        self.camera.center_on(new_player.pos_x, new_player.pos_y)
        self._cancel_active_event_if_any()

    def _on_player_teleported(self, player):
        if player is self.turn_manager.current_player:
            self.camera.center_on(player.pos_x, player.pos_y)

    def _cancel_active_event_if_any(self):
        """Если время хода истекло при открытом попапе события — закрываем его
        без применения исхода (эквивалент кнопки "Нет")."""
        from scene.scene_event import EventScene
        current = self.manager.current
        if isinstance(current, EventScene) and current.gameplay_scene is self:
            self.manager.pop()

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
        self.camera.update(dt)
        self.world.update(dt)

    # --- Отрисовка ---

    def draw(self, screen):
        self.renderer.draw()
        self.player_panel.draw(screen)
        if self.world.winner is not None:
            self._draw_victory_overlay(screen)

    def _draw_victory_overlay(self, screen):
        winner = self.world.winner
        content = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        content.fill(PAUSE_OVERLAY_COLOR)

        if self.settings.finish_mode == FINISH_MODE_RANKED and len(self.world.placements) > 1:
            self._draw_placements(content)
        else:
            name = PLAYER_NAMES_RU[winner.color_key]
            title_surf = get_font(FONT_SIZE_TITLE - 8).render(f"Победил игрок: {name}", True, winner.color)
            content.blit(title_surf, title_surf.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 20)))

        hint_surf = get_font(FONT_SIZE_HINT + 4).render("Esc — выйти в меню", True, TEXT_COLOR)
        content.blit(hint_surf, hint_surf.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 140)))

        content.set_alpha(int(self._victory_alpha))
        screen.blit(content, (0, 0))

    def _draw_placements(self, screen):
        title_surf = get_font(FONT_SIZE_TITLE - 14).render("Итоговые места", True, TEXT_COLOR)
        screen.blit(title_surf, title_surf.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 130)))

        start_y = SCREEN_HEIGHT // 2 - 70
        for i, place_player in enumerate(self.world.placements):
            name = PLAYER_NAMES_RU[place_player.color_key]
            surf = get_font(FONT_SIZE_LABEL + 4).render(f"{i + 1}. {name}", True, place_player.color)
            screen.blit(surf, surf.get_rect(center=(SCREEN_WIDTH // 2, start_y + i * 34)))