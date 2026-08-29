import pygame
from settings import *
from widgets import Button, Slider, TextInputBox, get_font
from game.game_config import (
    GameSettings, MAP_SIZE_PRESETS,
    MIN_MAP_SIZE, MAX_MAP_SIZE,
    MIN_OBSTACLE_PERCENT, MAX_OBSTACLE_PERCENT,
    MIN_PLAYERS, MAX_PLAYERS,
)
from scene.scenes import Scene


class NewGameScene(Scene):
    """Экран настройки одной партии: размер карты, доля препятствий, число игроков."""

    def __init__(self, manager):
        super().__init__(manager)
        self.settings = GameSettings()
        self.custom_mode = False

        cx = SCREEN_WIDTH // 2

        self.back_button = Button((20, 20, 90, 36), "Назад")

        # --- Размер карты: пресеты + "свой размер" ---
        preset_w, preset_h, gap = 130, 44, 12
        total_w = preset_w * 4 + gap * 3
        start_x = cx - total_w // 2
        self.preset_buttons = []
        for i, (label, w, h) in enumerate(MAP_SIZE_PRESETS):
            rect = (start_x + i * (preset_w + gap), 140, preset_w, preset_h)
            self.preset_buttons.append((Button(rect, label), w, h))
        custom_rect = (start_x + 3 * (preset_w + gap), 140, preset_w, preset_h)
        self.custom_button = Button(custom_rect, "Свой размер")

        input_w, input_h = 90, 40
        self.width_input = TextInputBox(
            (cx - input_w - 10, 200, input_w, input_h),
            value=str(self.settings.map_width), max_len=2, digits_only=True,
            placeholder=f"{MIN_MAP_SIZE}-{MAX_MAP_SIZE}",
        )
        self.height_input = TextInputBox(
            (cx + 10, 200, input_w, input_h),
            value=str(self.settings.map_height), max_len=2, digits_only=True,
            placeholder=f"{MIN_MAP_SIZE}-{MAX_MAP_SIZE}",
        )

        # --- Доля препятствий ---
        slider_w = 400
        self.obstacle_slider = Slider(
            (cx - slider_w // 2, 320, slider_w, 20),
            value=self.settings.obstacle_percent,
            min_value=MIN_OBSTACLE_PERCENT, max_value=MAX_OBSTACLE_PERCENT, step=1,
        )

        # --- Количество игроков (пока заглушка) ---
        self.player_minus_button = Button((cx - 80, 400, 36, 36), "-")
        self.player_plus_button = Button((cx + 44, 400, 36, 36), "+")

        # --- Старт партии ---
        start_w, start_h = 240, 56
        self.start_button = Button((cx - start_w // 2, 500, start_w, start_h), "Начать игру")

    # --- Валидация custom-ввода ---

    @staticmethod
    def _is_valid_size(text):
        try:
            value = int(text)
        except ValueError:
            return False
        return MIN_MAP_SIZE <= value <= MAX_MAP_SIZE

    def _custom_inputs_valid(self):
        """True, если можно стартовать партию: либо выбран пресет,
        либо оба custom-поля содержат корректное число в допустимых границах."""
        if not self.custom_mode:
            return True
        return self._is_valid_size(self.width_input.text) and self._is_valid_size(self.height_input.text)

    # --- События ---

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self._handle_click(event.pos)
        elif event.type == pygame.MOUSEMOTION:
            if self.obstacle_slider.dragging:
                self.obstacle_slider.set_from_mouse(event.pos[0])
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self.obstacle_slider.dragging = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                from scene.scene_main_menu import MainMenuScene
                self.manager.switch_to(MainMenuScene(self.manager))
                return
            self.width_input.handle_keydown(event)
            self.height_input.handle_keydown(event)

    def _handle_click(self, pos):
        if self.back_button.collidepoint(pos):
            from scene.scene_main_menu import MainMenuScene
            self.manager.switch_to(MainMenuScene(self.manager))
            return

        for button, w, h in self.preset_buttons:
            if button.collidepoint(pos):
                self.custom_mode = False
                self.settings.map_width = w
                self.settings.map_height = h
                self.width_input.focused = False
                self.height_input.focused = False
                return

        if self.custom_button.collidepoint(pos):
            self.custom_mode = True
            return

        if self.custom_mode:
            self.width_input.try_focus(pos)
            self.height_input.try_focus(pos)

        if self.obstacle_slider.rect.collidepoint(pos):
            self.obstacle_slider.dragging = True
            self.obstacle_slider.set_from_mouse(pos[0])
            return

        if self.player_minus_button.collidepoint(pos):
            self.settings.player_count = max(MIN_PLAYERS, self.settings.player_count - 1)
            return
        if self.player_plus_button.collidepoint(pos):
            self.settings.player_count = min(MAX_PLAYERS, self.settings.player_count + 1)
            return

        # Кнопка неактивна (enabled=False), пока custom-ввод некорректен —
        # collidepoint сам вернёт False, дополнительная проверка не нужна.
        if self.start_button.collidepoint(pos):
            self._start_game()

    def _start_game(self):
        if self.custom_mode:
            self.settings.map_width = int(self.width_input.text)
            self.settings.map_height = int(self.height_input.text)
        self.settings.obstacle_percent = int(round(self.obstacle_slider.value))
        self.settings.clamp()

        from scene.scene_gameplay import GameplayScene
        self.manager.push(GameplayScene(self.manager, self.settings))

    # --- Отрисовка ---

    def draw(self, screen):
        screen.fill(MENU_BG_COLOR)
        mouse_pos = pygame.mouse.get_pos()
        label_font = get_font(FONT_SIZE_LABEL)

        title_surf = get_font(FONT_SIZE_TITLE - 12).render("Настройки игры", True, TEXT_COLOR)
        screen.blit(title_surf, title_surf.get_rect(center=(SCREEN_WIDTH // 2, 60)))

        self.back_button.draw(screen, mouse_pos)

        self._draw_label(screen, label_font, "Размер карты", (SCREEN_WIDTH // 2, 110))
        for button, w, h in self.preset_buttons:
            button.draw(screen, mouse_pos)
            if not self.custom_mode and self.settings.map_width == w and self.settings.map_height == h:
                pygame.draw.rect(screen, SELECTED_BORDER_COLOR, button.rect, 3, border_radius=4)
        self.custom_button.draw(screen, mouse_pos)
        if self.custom_mode:
            pygame.draw.rect(screen, SELECTED_BORDER_COLOR, self.custom_button.rect, 3, border_radius=4)
            width_valid = self._is_valid_size(self.width_input.text)
            height_valid = self._is_valid_size(self.height_input.text)
            self.width_input.draw(screen, valid=width_valid)
            self.height_input.draw(screen, valid=height_valid)
            x_surf = label_font.render("x", True, TEXT_COLOR)
            screen.blit(x_surf, x_surf.get_rect(center=(SCREEN_WIDTH // 2, 220)))

        self._draw_label(screen, label_font, "Доля стен и камней", (SCREEN_WIDTH // 2, 290))
        self.obstacle_slider.draw(screen)
        percent_text = f"{int(round(self.obstacle_slider.value))}%"
        self._draw_label(screen, label_font, percent_text, (SCREEN_WIDTH // 2, 360))

        self._draw_label(screen, label_font, "Игроков", (SCREEN_WIDTH // 2, 400 + 18), offset_x=-140)
        self.player_minus_button.draw(screen, mouse_pos)
        count_surf = label_font.render(str(self.settings.player_count), True, TEXT_COLOR)
        screen.blit(count_surf, count_surf.get_rect(center=(SCREEN_WIDTH // 2, 400 + 18)))
        self.player_plus_button.draw(screen, mouse_pos)

        self.start_button.enabled = self._custom_inputs_valid()
        self.start_button.draw(screen, mouse_pos)

    @staticmethod
    def _draw_label(screen, font, text, center, offset_x=0):
        surf = font.render(text, True, TEXT_COLOR)
        rect = surf.get_rect(center=(center[0] + offset_x, center[1]))
        screen.blit(surf, rect)