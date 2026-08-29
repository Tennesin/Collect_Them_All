import pygame
from settings import *
from widgets import Button, get_font
from scene.scenes import Scene

class PauseScene(Scene):
    """Оверлей паузы"""

    def __init__(self, manager, gameplay_scene):
        super().__init__(manager)
        self.gameplay_scene = gameplay_scene

        cx = SCREEN_WIDTH // 2
        btn_w, btn_h = 260, 56
        self.resume_button = Button((cx - btn_w // 2, 240, btn_w, btn_h), "Продолжить")
        self.exit_button = Button((cx - btn_w // 2, 320, btn_w, btn_h), "Выйти в меню")

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.manager.pop()
            return
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.resume_button.collidepoint(event.pos):
                self.manager.pop()
            elif self.exit_button.collidepoint(event.pos):
                from scene.scene_main_menu import MainMenuScene
                self.manager.switch_to(MainMenuScene(self.manager))

    def draw(self, screen):
        self.gameplay_scene.draw(screen)

        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill(PAUSE_OVERLAY_COLOR)
        screen.blit(overlay, (0, 0))

        title_surf = get_font(FONT_SIZE_TITLE - 12).render("Пауза", True, TEXT_COLOR)
        screen.blit(title_surf, title_surf.get_rect(center=(SCREEN_WIDTH // 2, 160)))

        mouse_pos = pygame.mouse.get_pos()
        self.resume_button.draw(screen, mouse_pos)
        self.exit_button.draw(screen, mouse_pos)