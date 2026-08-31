import pygame
import time
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
    MIN_TURN_TIME, MAX_TURN_TIME, TURN_TIME_STEP,
    MIN_VISION_RADIUS, MAX_VISION_RADIUS,
    max_gold_cells_for_map,
)
from scene.scenes import Scene

class NewGameScene(Scene):
    """Экран настройки одной партии."""

    CX_LEFT = 190
    CX_RIGHT = 590
    DIVIDER_WIDTH = 210
    SLIDER_WIDTH = 300

    def __init__(self, manager):
        super().__init__(manager)
        self.settings = GameSettings()
        self.custom_mode = False

        self.back_button = Button((20, 20, 90, 32), "Назад")

        # ================= ЛЕВАЯ КОЛОНКА =================
        # --- Раздел "Карта" ---
        preset_w, preset_h, gap = 78, 34, 8
        total_w = preset_w * 4 + gap * 3
        start_x = self.CX_LEFT - total_w // 2
        self.preset_buttons = []
        for i, (label, w, h) in enumerate(MAP_SIZE_PRESETS):
            rect = (start_x + i * (preset_w + gap), 110, preset_w, preset_h)
            self.preset_buttons.append((Button(rect, label), w, h))
        custom_rect = (start_x + 3 * (preset_w + gap), 110, preset_w, preset_h)
        self.custom_button = Button(custom_rect, "Свой")

        input_w, input_h = 70, 34
        self.width_input = TextInputBox(
            (self.CX_LEFT - input_w - 5, 150, input_w, input_h),
            value=str(self.settings.map_width), max_len=2, digits_only=True,
            placeholder=f"{MIN_MAP_SIZE}-{MAX_MAP_SIZE}",
        )
        self.height_input = TextInputBox(
            (self.CX_LEFT + 5, 150, input_w, input_h),
            value=str(self.settings.map_height), max_len=2, digits_only=True,
            placeholder=f"{MIN_MAP_SIZE}-{MAX_MAP_SIZE}",
        )

        self.obstacle_slider = Slider(
            (self.CX_LEFT - self.SLIDER_WIDTH // 2, 218, self.SLIDER_WIDTH, 16),
            value=self.settings.obstacle_percent,
            min_value=MIN_OBSTACLE_PERCENT, max_value=MAX_OBSTACLE_PERCENT, step=1,
        )

        # --- Раздел "Игроки" ---
        self.player_minus_button = Button((self.CX_LEFT - 76, 312, 32, 32), "-")
        self.player_plus_button = Button((self.CX_LEFT + 44, 312, 32, 32), "+")

        # --- Раздел "Видимость" (новое) ---
        self.vision_minus_button = Button((self.CX_LEFT - 76, 422, 32, 32), "-")
        self.vision_plus_button = Button((self.CX_LEFT + 44, 422, 32, 32), "+")

        # ================= ПРАВАЯ КОЛОНКА =================
        # --- Раздел "Победа" ---
        self.gold_win_slider = Slider(
            (self.CX_RIGHT - self.SLIDER_WIDTH // 2, 112, self.SLIDER_WIDTH, 16),
            value=self.settings.win_gold_required,
            min_value=MIN_WIN_GOLD, max_value=MAX_WIN_GOLD, step=WIN_GOLD_STEP,
        )
        self.silver_win_slider = Slider(
            (self.CX_RIGHT - self.SLIDER_WIDTH // 2, 162, self.SLIDER_WIDTH, 16),
            value=self.settings.win_silver_required,
            min_value=MIN_WIN_SILVER, max_value=MAX_WIN_SILVER, step=WIN_SILVER_STEP,
        )
        self.gold_cells_minus_button = Button((self.CX_RIGHT - 76, 216, 32, 32), "-")
        self.gold_cells_plus_button = Button((self.CX_RIGHT + 44, 216, 32, 32), "+")

        # --- Раздел "Финиш" ---
        finish_btn_w, finish_btn_h, finish_gap = 156, 38, 10
        finish_total_w = finish_btn_w * 2 + finish_gap
        finish_start_x = self.CX_RIGHT - finish_total_w // 2
        self.finish_instant_button = Button(
            (finish_start_x, 308, finish_btn_w, finish_btn_h), "Первый у цели"
        )
        self.finish_ranked_button = Button(
            (finish_start_x + finish_btn_w + finish_gap, 308, finish_btn_w, finish_btn_h), "До последнего"
        )

        # --- Раздел "Черёд" ---
        self.moves_minus_button = Button((self.CX_RIGHT - 76, 424, 32, 32), "-")
        self.moves_plus_button = Button((self.CX_RIGHT + 44, 424, 32, 32), "+")

        self.time_slider = Slider(
            (self.CX_RIGHT - self.SLIDER_WIDTH // 2, 488, self.SLIDER_WIDTH, 16),
            value=self.settings.turn_time_seconds,
            min_value=MIN_TURN_TIME, max_value=MAX_TURN_TIME, step=TURN_TIME_STEP,
        )
        self._gold_cells_flash_until = 0.0

        # ================= СТАРТ =================
        start_w, start_h = 240, 48
        self.start_button = Button((SCREEN_WIDTH // 2 - start_w // 2, 542, start_w, start_h), "Начать игру")

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

    def _clamp_gold_cells_to_map(self):
        """При смене размера карты не даём количеству золотых клеток остаться выше нового максимума."""
        max_cells = max_gold_cells_for_map(self.settings.map_width, self.settings.map_height)
        if self.settings.gold_cell_count > max_cells:
            self.settings.gold_cell_count = max_cells

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
            if self.time_slider.dragging:
                self.time_slider.set_from_mouse(event.pos[0])
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self.obstacle_slider.dragging = False
            self.gold_win_slider.dragging = False
            self.silver_win_slider.dragging = False
            self.time_slider.dragging = False
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

        # --- Карта ---
        for button, w, h in self.preset_buttons:
            if button.collidepoint(pos):
                self.custom_mode = False
                self.settings.map_width = w
                self.settings.map_height = h
                self.width_input.focused = False
                self.height_input.focused = False
                self._clamp_gold_cells_to_map()
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

        # --- Игроки ---
        if self.player_minus_button.collidepoint(pos):
            self.settings.player_count = max(MIN_PLAYERS, self.settings.player_count - 1)
            return
        if self.player_plus_button.collidepoint(pos):
            self.settings.player_count = min(MAX_PLAYERS, self.settings.player_count + 1)
            return

        # --- Видимость ---
        if self.vision_minus_button.collidepoint(pos):
            self.settings.vision_radius = max(MIN_VISION_RADIUS, self.settings.vision_radius - 1)
            return
        if self.vision_plus_button.collidepoint(pos):
            self.settings.vision_radius = min(MAX_VISION_RADIUS, self.settings.vision_radius + 1)
            return

        # --- Победа ---
        if self.gold_win_slider.rect.collidepoint(pos):
            self.gold_win_slider.dragging = True
            self.gold_win_slider.set_from_mouse(pos[0])
            return
        if self.silver_win_slider.rect.collidepoint(pos):
            self.silver_win_slider.dragging = True
            self.silver_win_slider.set_from_mouse(pos[0])
            return
        if self.gold_cells_minus_button.collidepoint(pos):
            self.settings.gold_cell_count = max(MIN_GOLD_CELLS, self.settings.gold_cell_count - 1)
            return
        if self.gold_cells_minus_button.collidepoint(pos):
            self.settings.gold_cell_count = max(MIN_GOLD_CELLS, self.settings.gold_cell_count - 1)
            return
        if self.gold_cells_plus_button.collidepoint(pos):
            max_cells = max_gold_cells_for_map(self.settings.map_width, self.settings.map_height)
            if self.settings.gold_cell_count >= max_cells:
                self._gold_cells_flash_until = time.time() + 0.6
            else:
                self.settings.gold_cell_count += 1
            return

        # --- Финиш ---
        if self.finish_instant_button.collidepoint(pos):
            self.settings.finish_mode = FINISH_MODE_INSTANT
            return
        if self.finish_ranked_button.collidepoint(pos):
            self.settings.finish_mode = FINISH_MODE_RANKED
            return

        # --- Черёд ---
        if self.moves_minus_button.collidepoint(pos):
            self.settings.moves_per_turn = max(MIN_TURN_MOVES, self.settings.moves_per_turn - 1)
            return
        if self.moves_plus_button.collidepoint(pos):
            self.settings.moves_per_turn = min(MAX_TURN_MOVES, self.settings.moves_per_turn + 1)
            return
        if self.time_slider.rect.collidepoint(pos):
            self.time_slider.dragging = True
            self.time_slider.set_from_mouse(pos[0])
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
        self.settings.turn_time_seconds = int(round(self.time_slider.value))
        self.settings.clamp()

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

        # Разделительная линия между колонками
        pygame.draw.line(screen, PANEL_BORDER_COLOR, (SCREEN_WIDTH // 2, 60), (SCREEN_WIDTH // 2, 510), 1)

        cx_left, cx_right = self.CX_LEFT, self.CX_RIGHT

        # ============ ЛЕВАЯ КОЛОНКА ============

        self._draw_section_header(screen, "КАРТА", cx_left, 64)
        self._draw_label(screen, hint_font, "Размер карты", (cx_left, 92))
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
            screen.blit(x_surf, x_surf.get_rect(center=(cx_left, 167)))
        obstacle_pct = int(round(self.obstacle_slider.value))
        self._draw_label(screen, hint_font, f"Доля стен и камней: {obstacle_pct}%", (cx_left, 198))
        self.obstacle_slider.draw(screen)

        self._draw_divider(screen, cx_left, 254)
        self._draw_section_header(screen, "ИГРОКИ", cx_left, 266)
        self._draw_label(screen, hint_font, "Количество игроков", (cx_left, 294))
        self.player_minus_button.draw(screen, mouse_pos)
        count_surf = label_font.render(str(self.settings.player_count), True, TEXT_COLOR)
        screen.blit(count_surf, count_surf.get_rect(center=(cx_left, 328)))
        self.player_plus_button.draw(screen, mouse_pos)

        self._draw_divider(screen, cx_left, 364)
        self._draw_section_header(screen, "ВИДИМОСТЬ", cx_left, 376)
        self._draw_label(screen, hint_font, "Дальность обзора", (cx_left, 404))
        self.vision_minus_button.draw(screen, mouse_pos)
        vision_surf = label_font.render(str(self.settings.vision_radius), True, TEXT_COLOR)
        screen.blit(vision_surf, vision_surf.get_rect(center=(cx_left, 438)))
        self.vision_plus_button.draw(screen, mouse_pos)

        # ============ ПРАВАЯ КОЛОНКА ============

        self._draw_section_header(screen, "ПОБЕДА", cx_right, 64)
        gold_val = int(round(self.gold_win_slider.value))
        self._draw_label(screen, hint_font, f"Золото для победы: {gold_val}", (cx_right, 92))
        self.gold_win_slider.draw(screen)
        silver_val = int(round(self.silver_win_slider.value))
        self._draw_label(screen, hint_font, f"Серебро для победы: {silver_val}", (cx_right, 142))
        self.silver_win_slider.draw(screen)
        self._draw_label(screen, hint_font, "Золотых клеток", (cx_right, 198))
        self.gold_cells_minus_button.draw(screen, mouse_pos)
        cells_color = WARNING_TEXT_COLOR if time.time() < self._gold_cells_flash_until else TEXT_COLOR
        cells_surf = label_font.render(str(self.settings.gold_cell_count), True, cells_color)
        screen.blit(cells_surf, cells_surf.get_rect(center=(cx_right, 232)))
        self.gold_cells_plus_button.draw(screen, mouse_pos)

        self._draw_divider(screen, cx_right, 268)
        self._draw_section_header(screen, "ФИНИШ", cx_right, 280)
        self.finish_instant_button.draw(screen, mouse_pos, font_size=FONT_SIZE_HINT)
        self.finish_ranked_button.draw(screen, mouse_pos, font_size=FONT_SIZE_HINT)
        if self.settings.finish_mode == FINISH_MODE_INSTANT:
            pygame.draw.rect(screen, SELECTED_BORDER_COLOR, self.finish_instant_button.rect, 3, border_radius=4)
        else:
            pygame.draw.rect(screen, SELECTED_BORDER_COLOR, self.finish_ranked_button.rect, 3, border_radius=4)

        self._draw_divider(screen, cx_right, 366)
        self._draw_section_header(screen, "ЧЕРЁД", cx_right, 378)
        self._draw_label(screen, hint_font, "Ходов за черёд", (cx_right, 406))
        self.moves_minus_button.draw(screen, mouse_pos)
        moves_surf = label_font.render(str(self.settings.moves_per_turn), True, TEXT_COLOR)
        screen.blit(moves_surf, moves_surf.get_rect(center=(cx_right, 440)))
        self.moves_plus_button.draw(screen, mouse_pos)
        time_val = int(round(self.time_slider.value))
        self._draw_label(screen, hint_font, f"Время на действие: {time_val} с", (cx_right, 470))
        self.time_slider.draw(screen)

        # ============ СТАРТ ============
        self.start_button.enabled = self._custom_inputs_valid()
        self.start_button.draw(screen, mouse_pos)

    @staticmethod
    def _draw_label(screen, font, text, center, offset_x=0):
        surf = font.render(text, True, TEXT_COLOR)
        rect = surf.get_rect(center=(center[0] + offset_x, center[1]))
        screen.blit(surf, rect)

    @staticmethod
    def _draw_section_header(screen, text, cx, y):
        """Заголовок раздела: акцентный цвет + короткое подчёркивание."""
        surf = get_font(FONT_SIZE_HINT + 4).render(text, True, SELECTED_BORDER_COLOR)
        screen.blit(surf, surf.get_rect(center=(cx, y)))
        underline_y = y + 15
        pygame.draw.line(
            screen, SELECTED_BORDER_COLOR,
            (cx - 70, underline_y), (cx + 70, underline_y), 2,
        )

    @staticmethod
    def _draw_divider(screen, cx, y):
        """Тонкая линия-разделитель между разделами одной колонки."""
        half = NewGameScene.DIVIDER_WIDTH // 2
        pygame.draw.line(screen, PANEL_BORDER_COLOR, (cx - half, y), (cx + half, y), 1)