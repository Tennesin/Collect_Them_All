import pygame
from settings import *
from widgets import get_font

class PlayerPanel:
    """Правая панель интерфейса. Размер (PANEL_WIDTH x SCREEN_HEIGHT) фиксирован
    и не зависит от размера или состояния игрового поля — панель знает только
    про TurnManager, откуда берёт данные для отображения."""

    def __init__(self, turn_manager):
        self.turn_manager = turn_manager
        self.rect = pygame.Rect(GAME_AREA_WIDTH, 0, PANEL_WIDTH, SCREEN_HEIGHT)

    def draw(self, screen):
        pygame.draw.rect(screen, PANEL_BG_COLOR, self.rect)
        pygame.draw.line(screen, PANEL_BORDER_COLOR, (self.rect.x, 0), (self.rect.x, SCREEN_HEIGHT), 2)

        player = self.turn_manager.current_player
        padding = 18
        x = self.rect.x + padding
        y = 24

        y = self._draw_line(screen, x, y, "Текущий ход:", HINT_TEXT_COLOR, FONT_SIZE_HINT)
        y = self._draw_line(screen, x, y + 2, PLAYER_NAMES_RU[player.color_key], player.color, FONT_SIZE_LABEL + 4)
        y += 26

        y = self._draw_line(screen, x, y, "Ходы", HINT_TEXT_COLOR, FONT_SIZE_HINT)
        y = self._draw_line(
            screen, x, y + 2,
            f"{self.turn_manager.moves_left}/{self.turn_manager.max_moves}",
            TEXT_COLOR, FONT_SIZE_LABEL + 2,
        )
        y += 20

        y = self._draw_line(screen, x, y, "Время", HINT_TEXT_COLOR, FONT_SIZE_HINT)
        self._draw_line(
            screen, x, y + 2,
            f"{self.turn_manager.time_left:.1f} с",
            TEXT_COLOR, FONT_SIZE_LABEL + 2,
        )

    @staticmethod
    def _draw_line(screen, x, y, text, color, font_size):
        surf = get_font(font_size).render(text, True, color)
        screen.blit(surf, (x, y))
        return y + surf.get_height()