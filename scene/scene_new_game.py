import pygame
from settings import *
from widgets import Button, Slider, TextInputBox, get_font
from game.game_config import (
    GameSettings, MAP_SIZE_PRESETS,
    MIN_MAP_SIZE, MAX_MAP_SIZE,
    MIN_OBSTACLE_PERCENT, MAX_OBSTACLE_PERCENT,
    MIN_PLAYERS, MAX_PLAYERS,
    MIN_WIN_GOLD, MAX_WIN_GOLD, WIN_GOLD_STEP,
    MIN_WIN_SILVER, MAX_WIN_SILVER, WIN_SILVER_STEP,
    MIN_GOLD_CELLS, MAX_GOLD_CELLS,
    FINISH_MODE_INSTANT, FINISH_MODE_RANKED,
    MIN_TURN_MOVES, MAX_TURN_MOVES,
)
from scene.scenes import Scene


class NewGameScene(Scene):
    """Экран настройки одной партии: карта, игроки, экономика победы, режим финиша."""

    def __init__(self, manager):
        super().__init__(manager)
        self.settings = GameSettings()
        self.custom_mode = False

        cx_left = 200
        cx_right = 600

        self.back_button = Button((20, 20, 90, 32), "Назад")

        # ================= ЛЕВАЯ КОЛОНКА: карта, игроки, препятствия =================

        preset_w, preset_h, gap = 80, 36, 8
        total_w = preset_w * 4 + gap * 3
        start_x = cx_left - total_w // 2
        self.preset_buttons = []
        for i, (label, w, h) in enumerate(MAP_SIZE_PRESETS):
            rect = (start_x + i * (preset_w + gap), 94, preset_w, preset_h)
            self.preset_buttons.append((Button(rect, label), w, h))
        custom_rect = (start_x + 3 * (preset_w + gap), 94, preset_w, preset_h)
        self.custom_button = Button(custom_rect, "Свой")

        input_w, input_h = 70, 36
        self.width_input = TextInputBox(
            (cx_left - input_w - 5, 140, input_w, input_h),
            value=str(self.settings.map_width), max_len=2, digits_only=True,
            placeholder=f"{MIN_MAP_SIZE}-{MAX_MAP_SIZE}",
        )
        self.height_input = TextInputBox(
            (cx_left + 5, 140, input_w, input_h),
            value=str(self.settings.map_height), max_len=2, digits_only=True,
            placeholder=f"{MIN_MAP_SIZE}-{MAX_MAP_SIZE}",
        )

        self.player_minus_button = Button((cx_left - 76, 214, 32, 32), "-")
        self.player_plus_button = Button((cx_left + 44, 214, 32, 32), "+")

        slider_w = 340
        self.obstacle_slider = Slider(
            (cx_left - slider_w // 2, 286, slider_w, 18),
            value=self.settings.obstacle_percent,
            min_value=MIN_OBSTACLE_PERCENT, max_value=MAX_OBSTACLE_PERCENT, step=1,
        )

        # ================= ПРАВАЯ КОЛОНКА: условия победы и финиш =================

        self.gold_win_slider = Slider(
            (cx_right - slider_w // 2, 94, slider_w, 18),
            value=self.settings.win_gold_required,
            min_value=MIN_WIN_GOLD, max_value=MAX_WIN_GOLD, step=WIN_GOLD_STEP,
        )
        self.silver_win_slider = Slider(
            (cx_right - slider_w // 2, 166, slider_w, 18),
            value=self.settings.win_silver_required,
            min_value=MIN_WIN_SILVER, max_value=MAX_WIN_SILVER, step=WIN_SILVER_STEP,
        )

        self.gold_cells_minus_button = Button((cx_right - 76, 238, 32, 32), "-")
        self.gold_cells_plus_button = Button((cx_right + 44, 238, 32, 32), "+")

        finish_btn_w, finish_btn_h, finish_gap = 160, 40, 10
        finish_total_w = finish_btn_w * 2 + finish_gap
        finish_start_x = cx_right - finish_total_w // 2
        self.finish_instant_button = Button(
            (finish_start_x, 308, finish_btn_w, finish_btn_h), "Первый у цели"
        )
        self.finish_ranked_button = Button(
            (finish_start_x + finish_btn_w + finish_gap, 308, finish_btn_w, finish_btn_h), "До последнего"
        )

        # ================= НИЖНЯЯ СТРОКА: длительность черёда =================

        self.moves_minus_button = Button((SCREEN_WIDTH // 2 - 76, 390, 32, 32), "-")
        self.moves_plus_button = Button((SCREEN_WIDTH // 2 + 44, 390, 32, 32), "+")

        # ================= СТАРТ =================

        start_w, start_h = 240, 56
        self.start_button = Button((SCREEN_WIDTH // 2 - start_w // 2, 460, start_w, start_h), "Начать игру")

    # --- Валидация custom-ввода ---

    @staticmethod
    def _is_valid_size(text):
        try:
            value = int(text)
        except ValueError:
            return False
        return MIN_MAP_SIZE <= value <= MAX_MAP_SIZE

    def _custom_inputs_valid(self):
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
            if self.gold_win_slider.dragging:
                self.gold_win_slider.set_from_mouse(event.pos[0])
            if self.silver_win_slider.dragging:
                self.silver_win_slider.set_from_mouse(event.pos[0])
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self.obstacle_slider.dragging = False
            self.gold_win_slider.dragging = False
            self.silver_win_slider.dragging = False
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

        if self.gold_win_slider.rect.collidepoint(pos):
            self.gold_win_slider.dragging = True
            self.gold_win_slider.set_from_mouse(pos[0])
            return

        if self.silver_win_slider.rect.collidepoint(pos):
            self.silver_win_slider.dragging = True
            self.silver_win_slider.set_from_mouse(pos[0])
            return

        if self.player_minus_button.collidepoint(pos):
            self.settings.player_count = max(MIN_PLAYERS, self.settings.player_count - 1)
            return
        if self.player_plus_button.collidepoint(pos):
            self.settings.player_count = min(MAX_PLAYERS, self.settings.player_count + 1)
            return

        if self.gold_cells_minus_button.collidepoint(pos):
            self.settings.gold_cell_count = max(MIN_GOLD_CELLS, self.settings.gold_cell_count - 1)
            return
        if self.gold_cells_plus_button.collidepoint(pos):
            self.settings.gold_cell_count = min(MAX_GOLD_CELLS, self.settings.gold_cell_count + 1)
            return

        if self.finish_instant_button.collidepoint(pos):
            self.settings.finish_mode = FINISH_MODE_INSTANT
            return
        if self.finish_ranked_button.collidepoint(pos):
            self.settings.finish_mode = FINISH_MODE_RANKED
            return

        if self.moves_minus_button.collidepoint(pos):
            self.settings.moves_per_turn = max(MIN_TURN_MOVES, self.settings.moves_per_turn - 1)
            return
        if self.moves_plus_button.collidepoint(pos):
            self.settings.moves_per_turn = min(MAX_TURN_MOVES, self.settings.moves_per_turn + 1)
            return

        if self.start_button.collidepoint(pos):
            self._start_game()

    def _start_game(self):
        if self.custom_mode:
            self.settings.map_width = int(self.width_input.text)
            self.settings.map_height = int(self.height_input.text)
        self.settings.obstacle_percent = int(round(self.obstacle_slider.value))
        self.settings.win_gold_required = int(round(self.gold_win_slider.value))
        self.settings.win_silver_required = int(round(self.silver_win_slider.value))
        self.settings.clamp()  # здесь же произойдёт финальное ограничение gold_cell_count под размер карты

        from scene.scene_gameplay import GameplayScene
        self.manager.push(GameplayScene(self.manager, self.settings))

    # --- Отрисовка ---

    def draw(self, screen):
        screen.fill(MENU_BG_COLOR)
        mouse_pos = pygame.mouse.get_pos()
        label_font = get_font(FONT_SIZE_LABEL)
        hint_font = get_font(FONT_SIZE_HINT)

        title_surf = get_font(FONT_SIZE_TITLE - 16).render("Настройки игры", True, TEXT_COLOR)
        screen.blit(title_surf, title_surf.get_rect(center=(SCREEN_WIDTH // 2, 40)))

        self.back_button.draw(screen, mouse_pos)

        cx_left = 200
        cx_right = 600

        # --- Левая колонка ---
        self._draw_label(screen, hint_font, "Размер карты", (cx_left, 76))
        for button, w, h in self.preset_buttons:
            button.draw(screen, mouse_pos, font_size=FONT_SIZE_HINT)
            if not self.custom_mode and self.settings.map_width == w and self.settings.map_height == h:
                pygame.draw.rect(screen, SELECTED_BORDER_COLOR, button.rect, 3, border_radius=4)
        self.custom_button.draw(screen, mouse_pos, font_size=FONT_SIZE_HINT)
        if self.custom_mode:
            pygame.draw.rect(screen, SELECTED_BORDER_COLOR, self.custom_button.rect, 3, border_radius=4)
            width_valid = self._is_valid_size(self.width_input.text)
            height_valid = self._is_valid_size(self.height_input.text)
            self.width_input.draw(screen, valid=width_valid)
            self.height_input.draw(screen, valid=height_valid)
            x_surf = label_font.render("x", True, TEXT_COLOR)
            screen.blit(x_surf, x_surf.get_rect(center=(cx_left, 158)))

        self._draw_label(screen, hint_font, "Игроков", (cx_left, 196))
        self.player_minus_button.draw(screen, mouse_pos)
        count_surf = label_font.render(str(self.settings.player_count), True, TEXT_COLOR)
        screen.blit(count_surf, count_surf.get_rect(center=(cx_left, 230)))
        self.player_plus_button.draw(screen, mouse_pos)

        self._draw_label(screen, hint_font, "Доля стен и камней", (cx_left, 266))
        self.obstacle_slider.draw(screen)
        percent_text = f"{int(round(self.obstacle_slider.value))}%"
        self._draw_label(screen, hint_font, percent_text, (cx_left, 316))

        # --- Правая колонка ---
        self._draw_label(screen, hint_font, "Золото для победы", (cx_right, 76))
        self.gold_win_slider.draw(screen)
        self._draw_label(screen, hint_font, f"{int(round(self.gold_win_slider.value))}", (cx_right, 124))

        self._draw_label(screen, hint_font, "Серебро для победы", (cx_right, 148))
        self.silver_win_slider.draw(screen)
        self._draw_label(screen, hint_font, f"{int(round(self.silver_win_slider.value))}", (cx_right, 196))

        self._draw_label(screen, hint_font, "Золотых клеток", (cx_right, 220))
        self.gold_cells_minus_button.draw(screen, mouse_pos)
        cells_surf = label_font.render(str(self.settings.gold_cell_count), True, TEXT_COLOR)
        screen.blit(cells_surf, cells_surf.get_rect(center=(cx_right, 254)))
        self.gold_cells_plus_button.draw(screen, mouse_pos)

        self._draw_label(screen, hint_font, "Финиш", (cx_right, 290))
        self.finish_instant_button.draw(screen, mouse_pos, font_size=FONT_SIZE_HINT)
        self.finish_ranked_button.draw(screen, mouse_pos, font_size=FONT_SIZE_HINT)
        if self.settings.finish_mode == FINISH_MODE_INSTANT:
            pygame.draw.rect(screen, SELECTED_BORDER_COLOR, self.finish_instant_button.rect, 3, border_radius=4)
        else:
            pygame.draw.rect(screen, SELECTED_BORDER_COLOR, self.finish_ranked_button.rect, 3, border_radius=4)

        # --- Нижняя строка ---
        self._draw_label(screen, hint_font, "Ходов за черёд", (SCREEN_WIDTH // 2, 372))
        self.moves_minus_button.draw(screen, mouse_pos)
        moves_surf = label_font.render(str(self.settings.moves_per_turn), True, TEXT_COLOR)
        screen.blit(moves_surf, moves_surf.get_rect(center=(SCREEN_WIDTH // 2, 406)))
        self.moves_plus_button.draw(screen, mouse_pos)

        self.start_button.enabled = self._custom_inputs_valid()
        self.start_button.draw(screen, mouse_pos)

    @staticmethod
    def _draw_label(screen, font, text, center, offset_x=0):
        surf = font.render(text, True, TEXT_COLOR)
        rect = surf.get_rect(center=(center[0] + offset_x, center[1]))
        screen.blit(surf, rect)