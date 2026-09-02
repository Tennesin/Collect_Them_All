import time
import pygame
from settings import *
from game.image_manager import ImageManager

_font_cache = {}

def get_font(size, name=FONT_NAME):
    """Общий кэш шрифтов для всех виджетов, чтобы не пересоздавать Font на каждый кадр."""
    key = (name, size)
    font = _font_cache.get(key)
    if font is None:
        font = pygame.font.SysFont(name, size)
        _font_cache[key] = font
    return font


def draw_wrapped_text_centered(surface, cx, y, text, color, font_size, max_width, line_spacing=4):
    """Перенос текста по словам с центровкой каждой строки вокруг cx."""
    font = get_font(font_size)
    words = text.split(" ")
    lines = []
    line = ""
    for word in words:
        candidate = f"{line} {word}".strip()
        if font.size(candidate)[0] > max_width and line:
            lines.append(line)
            line = word
        else:
            line = candidate
    if line:
        lines.append(line)

    line_y = y
    for line_text in lines:
        surf = font.render(line_text, True, color)
        surface.blit(surf, surf.get_rect(center=(cx, line_y + surf.get_height() // 2)))
        line_y += surf.get_height() + line_spacing
    return line_y

class Button:
    def __init__(self, rect, label, enabled=True):
        self.rect = pygame.Rect(rect)
        self.label = label
        self.enabled = enabled

    def draw(self, surface, mouse_pos, font_size=None, colors=None, icon_name=None, icon_base_dir=None):
        """icon_name — необязательная иконка, рисуется справа от текста (например,
        кубик рядом с подписью "Да" на попапе события)."""
        font_size = font_size or FONT_SIZE_BUTTON
        colors = colors or {
            "normal": BUTTON_COLOR, "hover": BUTTON_HOVER_COLOR,
            "disabled": BUTTON_DISABLED_COLOR, "text": BUTTON_TEXT_COLOR,
        }
        if not self.enabled:
            bg = colors["disabled"]
        elif self.rect.collidepoint(mouse_pos):
            bg = colors["hover"]
        else:
            bg = colors["normal"]

        pygame.draw.rect(surface, bg, self.rect, border_radius=4)
        txt_surf = get_font(font_size).render(self.label, True, colors["text"])

        if icon_name is None:
            surface.blit(txt_surf, txt_surf.get_rect(center=self.rect.center))
            return

        icon = ImageManager.get_scaled(icon_name, (font_size, font_size), base_dir=icon_base_dir)
        gap = 6
        total_w = txt_surf.get_width() + gap + icon.get_width()
        start_x = self.rect.centerx - total_w // 2

        text_rect = txt_surf.get_rect(midleft=(start_x, self.rect.centery))
        icon_rect = icon.get_rect(midleft=(text_rect.right + gap, self.rect.centery))

        surface.blit(txt_surf, text_rect)
        surface.blit(icon, icon_rect)

    def collidepoint(self, *args):
        return self.enabled and self.rect.collidepoint(*args)


class TextInputBox:
    def __init__(self, rect, value="", max_len=24, digits_only=False, placeholder=""):
        self.rect = pygame.Rect(rect)
        self.text = value
        self.max_len = max_len
        self.digits_only = digits_only
        self.placeholder = placeholder
        self.focused = False
        self._cursor_visible = True
        self._last_blink = time.time()

    def try_focus(self, pos):
        hit = self.rect.collidepoint(pos)
        self.focused = hit
        return hit

    def handle_keydown(self, event):
        if not self.focused:
            return False
        if event.key == pygame.K_BACKSPACE:
            self.text = self.text[:-1]
            return True
        if event.unicode and event.unicode.isprintable() and len(self.text) < self.max_len:
            ch = event.unicode
            if self.digits_only and not ch.isdigit():
                return False
            self.text += ch
            return True
        return False

    def draw(self, surface, font_size=None, valid=True):
        font = get_font(font_size or FONT_SIZE_LABEL)
        now = time.time()
        if now - self._last_blink >= 0.5:
            self._last_blink = now
            self._cursor_visible = not self._cursor_visible

        bg = INPUT_BG_COLOR_FOCUS if self.focused else INPUT_BG_COLOR
        if not valid:
            border = INPUT_BORDER_COLOR_ERROR
        elif self.focused:
            border = INPUT_BORDER_COLOR_FOCUS
        else:
            border = INPUT_BORDER_COLOR
        pygame.draw.rect(surface, bg, self.rect, border_radius=4)
        pygame.draw.rect(surface, border, self.rect, 1, border_radius=4)

        text_x = self.rect.x + 8
        cy = self.rect.centery

        if self.text:
            txt_surf = font.render(self.text, True, INPUT_TEXT_COLOR)
            surface.blit(txt_surf, txt_surf.get_rect(midleft=(text_x, cy)))
            cursor_x = text_x + txt_surf.get_width() + 2
        else:
            if self.placeholder:
                ph_surf = font.render(self.placeholder, True, INPUT_HINT_COLOR)
                surface.blit(ph_surf, ph_surf.get_rect(midleft=(text_x, cy)))
            cursor_x = text_x

        if self.focused and self._cursor_visible:
            pygame.draw.line(surface, INPUT_TEXT_COLOR,
                             (cursor_x, self.rect.y + 6), (cursor_x, self.rect.bottom - 6), 1)


class Slider:
    def __init__(self, rect, value=0.5, min_value=0.0, max_value=1.0, step=0.05):
        self.rect = pygame.Rect(rect)
        self.min_value = min_value
        self.max_value = max_value
        self.step = step
        self.value = max(min_value, min(max_value, value))
        self.dragging = False

    def set_from_mouse(self, mouse_x):
        if self.rect.width <= 0:
            return
        ratio = (mouse_x - self.rect.x) / self.rect.width
        ratio = max(0.0, min(1.0, ratio))
        raw_value = self.min_value + ratio * (self.max_value - self.min_value)
        steps = round((raw_value - self.min_value) / self.step)
        value = self.min_value + steps * self.step
        self.value = round(max(self.min_value, min(self.max_value, value)), 2)

    def draw(self, surface, fill_color=SLIDER_FILL_COLOR, bg_color=SLIDER_BG_COLOR, border_color=SLIDER_BORDER_COLOR):
        pygame.draw.rect(surface, bg_color, self.rect, border_radius=4)
        span = self.max_value - self.min_value
        ratio = (self.value - self.min_value) / span if span > 0 else 0.0
        fill_w = max(4, int(self.rect.width * ratio))
        fill_rect = pygame.Rect(self.rect.x, self.rect.y, fill_w, self.rect.height)
        pygame.draw.rect(surface, fill_color, fill_rect, border_radius=4)
        pygame.draw.rect(surface, border_color, self.rect, 1, border_radius=4)

        handle_rect = pygame.Rect(0, 0, 4, self.rect.height + 6)
        handle_rect.center = (self.rect.x + fill_w, self.rect.centery)
        pygame.draw.rect(surface, (240, 240, 240), handle_rect, border_radius=2)


class ScrollArea:
    """Пока не используется ни в одной сцене — пригодится, когда список
    игроков/ботов на экране настроек перестанет помещаться целиком."""

    def __init__(self):
        self.offset = 0
        self.max_scroll = 0

    def update_bounds(self, content_height, visible_height):
        self.max_scroll = max(0, content_height - visible_height)
        self.offset = max(0, min(self.offset, self.max_scroll))

    def scroll_by_wheel(self, wheel_y, speed=DEFAULT_SCROLL_SPEED):
        self.offset -= wheel_y * speed
        self.offset = max(0, min(self.offset, self.max_scroll))

    def draw_scrollbar(self, surface, rect):
        if self.max_scroll <= 0:
            return
        track_rect = pygame.Rect(rect.right - 4, rect.y, 4, rect.height)
        pygame.draw.rect(surface, (30, 30, 30), track_rect)
        content_height = rect.height + self.max_scroll
        thumb_h = max(20, int(rect.height * rect.height / content_height))
        thumb_y = rect.y + int((rect.height - thumb_h) * (self.offset / self.max_scroll))
        pygame.draw.rect(surface, (150, 150, 150), (track_rect.x, thumb_y, 4, thumb_h))