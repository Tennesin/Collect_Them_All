import pygame
from settings import *
from widgets import get_font
from game.image_manager import ImageManager


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
        max_text_width = self.rect.width - padding * 2
        y = 24

        y = self._draw_line(screen, x, y, "Текущий ход:", HINT_TEXT_COLOR, FONT_SIZE_HINT)
        y = self._draw_line(screen, x, y + 2, PLAYER_NAMES_RU[player.color_key], player.color, FONT_SIZE_LABEL + 4)
        y += 26

        y = self._draw_line(screen, x, y, "Ходы", HINT_TEXT_COLOR, FONT_SIZE_HINT)
        y = self._draw_icon_line(
            screen, x, y + 2, ICON_MOVE,
            f"{self.turn_manager.moves_left}/{self.turn_manager.max_moves}",
            TEXT_COLOR, FONT_SIZE_LABEL + 2,
        )
        y += 20

        y = self._draw_line(screen, x, y, "Время", HINT_TEXT_COLOR, FONT_SIZE_HINT)
        y = self._draw_icon_line(
            screen, x, y + 2, ICON_TIME,
            f"{self.turn_manager.time_left:.1f} с",
            TEXT_COLOR, FONT_SIZE_LABEL + 2,
        )
        y += 26

        y = self._draw_line(screen, x, y, "Бюджет", HINT_TEXT_COLOR, FONT_SIZE_HINT)
        y = self._draw_icon_line(
            screen, x, y + 2, ICON_GOLD, str(player.gold), TEXT_COLOR, FONT_SIZE_LABEL + 2,
        )
        y = self._draw_icon_line(
            screen, x, y + 4, ICON_SILVER, str(player.silver), TEXT_COLOR, FONT_SIZE_LABEL + 2,
        )

        if player.warning_message:
            y += 18
            self._draw_wrapped_text(
                screen, x, y, player.warning_message,
                WARNING_TEXT_COLOR, FONT_SIZE_HINT, max_text_width,
            )

    @staticmethod
    def _draw_line(screen, x, y, text, color, font_size):
        surf = get_font(font_size).render(text, True, color)
        screen.blit(surf, (x, y))
        return y + surf.get_height()

    @staticmethod
    def _draw_icon_line(screen, x, y, icon_name, text, color, font_size):
        """Рисует иконку (см. ImageManager) и текст рядом с ней по вертикальному
        центру одной строки. Возвращает y нижней границы строки."""
        icon = ImageManager.get_scaled(icon_name, (PANEL_ICON_SIZE, PANEL_ICON_SIZE))
        surf = get_font(font_size).render(text, True, color)
        line_height = max(icon.get_height(), surf.get_height())

        icon_rect = icon.get_rect(midleft=(x, y + line_height // 2))
        screen.blit(icon, icon_rect)

        text_rect = surf.get_rect(midleft=(icon_rect.right + 8, y + line_height // 2))
        screen.blit(surf, text_rect)

        return y + line_height

    @staticmethod
    def _draw_wrapped_text(screen, x, y, text, color, font_size, max_width):
        """Переносит текст по словам, чтобы длинное предупреждение не вылезало
        за границу узкой панели — сообщение о нехватке ресурсов может содержать
        оба ресурса сразу ('и'), и на маленьких размерах шрифта это не всегда
        влезает в одну строку."""
        font = get_font(font_size)
        words = text.split(" ")
        line = ""
        line_y = y
        for word in words:
            candidate = f"{line} {word}".strip()
            if font.size(candidate)[0] > max_width and line:
                surf = font.render(line, True, color)
                screen.blit(surf, (x, line_y))
                line_y += surf.get_height() + 2
                line = word
            else:
                line = candidate
        if line:
            surf = font.render(line, True, color)
            screen.blit(surf, (x, line_y))
            line_y += surf.get_height()
        return line_y