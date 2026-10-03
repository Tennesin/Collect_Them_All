import pygame
from settings import *
from widgets import get_font, wrap_text
from game.rendering.image_manager import ImageManager

class PlayerPanel:

    def __init__(self, player, resource_manager, clock):
        self.player = player
        self.resource_manager = resource_manager
        self.clock = clock
        self.rect = pygame.Rect(GAME_AREA_WIDTH, 0, PANEL_WIDTH, SCREEN_HEIGHT)

    def draw(self, screen):
        pygame.draw.rect(screen, PANEL_BG_COLOR, self.rect)
        pygame.draw.line(screen, PANEL_BORDER_COLOR, (self.rect.x, 0), (self.rect.x, SCREEN_HEIGHT), 2)

        player = self.player
        padding = 18
        x = self.rect.x + padding
        right_x = self.rect.x + self.rect.width // 2 + 6
        max_text_width = self.rect.width - padding * 2
        y = 24

        y = self._draw_line(screen, x, y, PLAYER_NAMES_RU[player.color_key], player.color, FONT_SIZE_LABEL + 4)
        y += 26

        section_top = y

        # --- Левая колонка: Скорость и Время партии ---
        multiplier = player.speed_multiplier
        if multiplier < 1.0:
            speed_color = WARNING_TEXT_COLOR
        elif multiplier > 1.0:
            speed_color = SELECTED_BORDER_COLOR
        else:
            speed_color = TEXT_COLOR

        left_y = self._draw_line(screen, x, section_top, "Скорость", HINT_TEXT_COLOR, FONT_SIZE_HINT)
        left_y = self._draw_icon_line(
            screen, x, left_y + 2, ICON_MOVE, f"x{multiplier:.2f}", speed_color, FONT_SIZE_LABEL + 2,
        )
        left_y += 20

        left_y = self._draw_line(screen, x, left_y, "Время партии", HINT_TEXT_COLOR, FONT_SIZE_HINT)
        left_y = self._draw_icon_line(
            screen, x, left_y + 2, ICON_TIME, self._format_time(self.clock.match_time),
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
            y = self._draw_wrapped_text(
                screen, x, y, player.warning_message,
                WARNING_TEXT_COLOR, FONT_SIZE_HINT, max_text_width,
            )

        if player.active_effects:
            y += 22
            self._draw_active_effects(screen, x, y, player)

    @staticmethod
    def _format_time(seconds):
        total = int(seconds)
        return f"{total // 60}:{total % 60:02d}"

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
        for line in wrap_text(font, text, max_width):
            surf = font.render(line, True, color)
            screen.blit(surf, (x, y))
            y += surf.get_height() + 2
        return y

    @staticmethod
    def _draw_active_effects(screen, x, y, player):
        for effect in player.active_effects:
            color = WARNING_TEXT_COLOR if effect.warning else TEXT_COLOR
            remaining = max(0.0, effect.duration_seconds)
            surf = get_font(FONT_SIZE_HINT).render(f"{effect.label}: {remaining:.1f} с", True, color)
            screen.blit(surf, (x, y))
            y += surf.get_height() + 2

class NotificationFeed:
    """Короткие сообщения в левом верхнем углу игрового поля (например, «бот открыл сундук»)."""

    MAX_ITEMS = 4

    def __init__(self):
        self._items = []   # [текст, цвет, осталось секунд]

    def add(self, text, color, duration=NOTIFICATION_DURATION):
        self._items.append([text, color, duration])
        del self._items[:-self.MAX_ITEMS]

    def update(self, dt):
        for item in self._items:
            item[2] -= dt
        self._items = [item for item in self._items if item[2] > 0]

    def draw(self, screen):
        font = get_font(FONT_SIZE_HINT)
        pad = 6
        y = 10
        for text, color, remaining in self._items:
            surf = font.render(text, True, color)
            box = pygame.Surface((surf.get_width() + pad * 2, surf.get_height() + pad * 2), pygame.SRCALPHA)
            box.fill(NOTIFICATION_BG_COLOR)
            box.blit(surf, (pad, pad))
            fade = min(1.0, remaining / NOTIFICATION_FADE)
            box.set_alpha(int(255 * fade))
            screen.blit(box, (10, y))
            y += box.get_height() + 4