import pygame
from settings import *
from widgets import Button, get_font
from scenes import Scene

class MainMenuScene(Scene):
    """Главное меню: 'Играть' ведёт на экран настроек, 'Выйти' закрывает приложение."""

    def __init__(self, manager):
        super().__init__(manager)
        cx = SCREEN_WIDTH // 2
        btn_w, btn_h = 220, 56
        self.play_button = Button((cx - btn_w // 2, 260, btn_w, btn_h), "Играть")
        self.quit_button = Button((cx - btn_w // 2, 340, btn_w, btn_h), "Выйти")

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.play_button.collidepoint(event.pos):
                # Локальный импорт — избегаем цикла scene_main_menu <-> new_game_scene
                from scene_new_game import NewGameScene
                self.manager.push(NewGameScene(self.manager))
            elif self.quit_button.collidepoint(event.pos):
                self.manager.app.quit()

    def draw(self, screen):
        screen.fill(MENU_BG_COLOR)

        title_font = get_font(FONT_SIZE_TITLE)
        title_surf = title_font.render(GAME_TITLE, True, TEXT_COLOR)
        screen.blit(title_surf, title_surf.get_rect(center=(SCREEN_WIDTH // 2, 150)))

        mouse_pos = pygame.mouse.get_pos()
        self.play_button.draw(screen, mouse_pos)
        self.quit_button.draw(screen, mouse_pos)