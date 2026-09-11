import pygame
from settings import *
from widgets import Button, get_font
from scene.scenes import Scene
from game.tween import Tween, ease_out_cubic

class PauseScene(Scene):
    """Оверлей паузы"""

    def __init__(self, manager, gameplay_scene):
        super().__init__(manager)
        self.gameplay_scene = gameplay_scene

        cx = SCREEN_WIDTH // 2
        btn_w, btn_h = 260, 56
        self.resume_button = Button((cx - btn_w // 2, 240, btn_w, btn_h), "Продолжить")
        self.exit_button = Button((cx - btn_w // 2, 320, btn_w, btn_h), "Выйти в меню")

        self._alpha = 0
        self._fade = Tween(0, 255, FADE_POPUP_IN_DURATION, ease_out_cubic)
        self._closing = False
        self._pending_action = None  # callable, вызывается после завершения fade-out

    def on_enter(self):
        self._fade = Tween(0, 255, FADE_POPUP_IN_DURATION, ease_out_cubic)
        self._closing = False

    def _start_closing(self, action):
        """Запускает fade-out и откладывает реальный переход (pop/switch_to)
        до его завершения — чтобы попап не исчезал рывком."""
        if self._closing:
            return
        self._closing = True
        self._pending_action = action
        self._fade = Tween(self._alpha, 0, FADE_POPUP_OUT_DURATION, ease_out_cubic)

    def update(self, dt):
        self._alpha = self._fade.update(dt)
        if self._closing and self._fade.finished:
            action = self._pending_action
            self._pending_action = None
            if action:
                action()

    def handle_event(self, event):
        if self._closing:
            return
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self._start_closing(self.manager.pop)
            return
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.resume_button.collidepoint(event.pos):
                self._start_closing(self.manager.pop)
            elif self.exit_button.collidepoint(event.pos):
                def _go_to_menu():
                    from scene.scene_main_menu import MainMenuScene
                    self.manager.switch_to(MainMenuScene(self.manager))
                self._start_closing(_go_to_menu)

    def draw(self, screen):
        self.gameplay_scene.draw(screen)

        content = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        content.fill(PAUSE_OVERLAY_COLOR)

        title_surf = get_font(FONT_SIZE_TITLE - 12).render("Пауза", True, TEXT_COLOR)
        content.blit(title_surf, title_surf.get_rect(center=(SCREEN_WIDTH // 2, 160)))

        mouse_pos = pygame.mouse.get_pos()
        self.resume_button.draw(content, mouse_pos)
        self.exit_button.draw(content, mouse_pos)

        content.set_alpha(int(self._alpha))
        screen.blit(content, (0, 0))