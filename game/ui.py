import pygame
from settings import *
from widgets import get_font
from game.image_manager import ImageManager
from game.game_config import EFFECT_LABELS_RU, EFFECT_HALF_INCOME

class PlayerPanel:

    def __init__(self, turn_manager, resource_manager):
        self.turn_manager = turn_manager
        self.resource_manager = resource_manager
        self.rect = pygame.Rect(GAME_AREA_WIDTH, 0, PANEL_WIDTH, SCREEN_HEIGHT)

    def draw(self, screen):
        pygame.draw.rect(screen, PANEL_BG_COLOR, self.rect)
        pygame.draw.line(screen, PANEL_BORDER_COLOR, (self.rect.x, 0), (self.rect.x, SCREEN_HEIGHT), 2)

        player = self.turn_manager.current_player
        padding = 18
        x = self.rect.x + padding
        right_x = self.rect.x + self.rect.width // 2 + 6
        max_text_width = self.rect.width - padding * 2
        y = 24

        y = self._draw_line(screen, x, y, "Текущий ход:", HINT_TEXT_COLOR, FONT_SIZE_HINT)
        y = self._draw_line(screen, x, y + 2, PLAYER_NAMES_RU[player.color_key], player.color, FONT_SIZE_LABEL + 4)
        y += 26

        section_top = y

        # --- Левая колонка: Ходы и Время ---
        left_y = self._draw_line(screen, x, section_top, "Ходы", HINT_TEXT_COLOR, FONT_SIZE_HINT)
        left_y = self._draw_icon_line(
            screen, x, left_y + 2, ICON_MOVE,
            f"{self.turn_manager.moves_left}/{self.turn_manager.max_moves}",
            TEXT_COLOR, FONT_SIZE_LABEL + 2,
        )
        left_y += 20

        left_y = self._draw_line(screen, x, left_y, "Время", HINT_TEXT_COLOR, FONT_SIZE_HINT)
        left_y = self._draw_icon_line(
            screen, x, left_y + 2, ICON_TIME,
            f"{self.turn_manager.time_left:.1f} с",
            TEXT_COLOR, FONT_SIZE_LABEL + 2,
        )

        # --- Правая колонка: Цель ---
        right_y = self._draw_line(screen, right_x, section_top, "Цель", HINT_TEXT_COLOR, FONT_SIZE_HINT)
        right_y = self._draw_icon_line(
            screen, right_x, right_y + 2, ICON_GOLD,
            str(self.resource_manager.win_gold_required),
            TEXT_COLOR, FONT_SIZE_LABEL + 2,
        )
        right_y = self._draw_icon_line(
            screen, right_x, right_y + 4, ICON_SILVER,
            str(self.resource_manager.win_silver_required),
            TEXT_COLOR, FONT_SIZE_LABEL + 2,
        )

        y = max(left_y, right_y) + 26

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

        if player.active_effects:
            y += 22
            self._draw_active_effects(screen, x, y, player)

    @staticmethod
    def _draw_line(screen, x, y, text, color, font_size):
        surf = get_font(font_size).render(text, True, color)
        screen.blit(surf, (x, y))
        return y + surf.get_height()

    @staticmethod
    def _draw_icon_line(screen, x, y, icon_name, text, color, font_size):
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

    @staticmethod
    def _draw_active_effects(screen, x, y, player):
        for effect_type, remaining in player.active_effects.items():
            label = EFFECT_LABELS_RU.get(effect_type, effect_type)
            color = WARNING_TEXT_COLOR if effect_type == EFFECT_HALF_INCOME else TEXT_COLOR
            turns_word = "черёд" if remaining == 1 else "черёда" if remaining < 5 else "черёдов"
            surf = get_font(FONT_SIZE_HINT).render(f"{label}: {remaining} {turns_word}", True, color)
            screen.blit(surf, (x, y))
            y += surf.get_height() + 2