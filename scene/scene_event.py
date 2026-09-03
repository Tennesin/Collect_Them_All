import random
import pygame
from settings import *
from widgets import Button, get_font, draw_wrapped_text_centered
from game.image_manager import ImageManager
from game.game_config import EFFECT_HALF_INCOME, EFFECT_LABELS_RU
from scene.scenes import Scene

STAGE_PROMPT = "prompt"    # текст события + кнопки "Да"/"Нет"
STAGE_ROLLING = "rolling"  # кубик крутится
STAGE_FROZEN = "frozen"    # кубик остановился, 1 секунда показа итоговой грани
STAGE_RESULT = "result"    # текст исхода + награды/штрафы + кнопка "Продолжить"

# Стадии, в которых внешнее время хода замораживается ("процесс броска кубика").
_TIMER_FROZEN_STAGES = (STAGE_ROLLING, STAGE_FROZEN)


class EventScene(Scene):
    """Оверлей одного случайного события: подтверждение -> бросок кубика -> результат."""

    def __init__(self, manager, gameplay_scene, player, event_definition):
        super().__init__(manager)
        self.gameplay_scene = gameplay_scene
        self.player = player
        self.event = event_definition

        self.stage = STAGE_PROMPT
        self.roll_timer = 0.0
        self.face_change_timer = 0.0
        self.freeze_timer = 0.0
        self.current_face = random.randint(1, 6)
        self.final_roll = None

        cx = SCREEN_WIDTH // 2
        btn_w, btn_h = 200, 52
        gap = 20
        self.yes_button = Button((cx - btn_w - gap // 2, 480, btn_w, btn_h), "Да")
        self.no_button = Button((cx + gap // 2, 480, btn_w, btn_h), "Нет")
        self.stop_button = Button((cx - btn_w // 2, 480, btn_w, btn_h), "Стоп")
        self.continue_button = Button((cx - 120, 500, 240, btn_h), "Продолжить")

    def on_enter(self):
        self.gameplay_scene.turn_manager.moves_trigger_suppressed = True

    def on_exit(self):
        self.gameplay_scene.turn_manager.moves_trigger_suppressed = False

    # --- события ввода ---

    def handle_event(self, event):
        if event.type != pygame.MOUSEBUTTONDOWN or event.button != 1:
            return

        if self.stage == STAGE_PROMPT:
            if self.yes_button.collidepoint(event.pos):
                self._start_rolling()
            elif self.no_button.collidepoint(event.pos):
                self.manager.pop()
        elif self.stage == STAGE_ROLLING:
            if self.stop_button.collidepoint(event.pos):
                self._freeze_roll()
        elif self.stage == STAGE_RESULT:
            if self.continue_button.collidepoint(event.pos):
                self._apply_outcome()
                if self.manager.current is self:
                    self.manager.pop()
        # STAGE_FROZEN: клики игнорируются, ждём истечения таймера показа грани.

    # --- обновление ---

    def update(self, dt):
        if self.stage not in _TIMER_FROZEN_STAGES:
            self.gameplay_scene.turn_manager.update(dt)

        if self.stage == STAGE_ROLLING:
            self._update_rolling(dt)
        elif self.stage == STAGE_FROZEN:
            self._update_frozen(dt)

    def _update_rolling(self, dt):
        self.roll_timer += dt
        if self.roll_timer >= DICE_ROLL_MAX_DURATION:
            self._freeze_roll()
            return
        self.face_change_timer += dt
        if self.face_change_timer >= DICE_ROLL_INTERVAL:
            self.face_change_timer = 0.0
            self.current_face = random.randint(1, 6)

    def _update_frozen(self, dt):
        self.freeze_timer += dt
        if self.freeze_timer >= DICE_RESULT_FREEZE_DURATION:
            self.stage = STAGE_RESULT

    def _start_rolling(self):
        self.stage = STAGE_ROLLING
        self.roll_timer = 0.0
        self.face_change_timer = 0.0

    def _freeze_roll(self):
        self.final_roll = self.current_face
        self.stage = STAGE_FROZEN
        self.freeze_timer = 0.0

    def _apply_outcome(self):
        outcome = self.event.get_outcome(self.final_roll)
        self.player.gold = max(0, self.player.gold + outcome.gold_delta)
        self.player.silver = max(0, self.player.silver + outcome.silver_delta)
        if outcome.moves_delta:
            self.gameplay_scene.turn_manager.adjust_moves(outcome.moves_delta)
        if outcome.displacement_cells:
            self.gameplay_scene.displace_player_randomly(self.player, outcome.displacement_cells)
        if outcome.effect_type:
            self.player.add_effect(outcome.effect_type, outcome.effect_duration)

    # --- отрисовка ---

    def draw(self, screen):
        self.gameplay_scene.draw(screen)

        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill(EVENT_POPUP_BG_COLOR)
        screen.blit(overlay, (0, 0))

        mouse_pos = pygame.mouse.get_pos()
        if self.stage == STAGE_PROMPT:
            self._draw_prompt(screen, mouse_pos)
        elif self.stage in (STAGE_ROLLING, STAGE_FROZEN):
            self._draw_dice(screen, mouse_pos)
        elif self.stage == STAGE_RESULT:
            self._draw_result(screen)

    def _draw_prompt(self, screen, mouse_pos):
        cx = SCREEN_WIDTH // 2
        icon = ImageManager.get_scaled(
            self.event.icon_file, (EVENT_ICON_SIZE, EVENT_ICON_SIZE), base_dir=self.event.icon_dir
        )
        screen.blit(icon, icon.get_rect(center=(cx, 160)))

        draw_wrapped_text_centered(
            screen, cx, 240, self.event.prompt_text,
            TEXT_COLOR, FONT_SIZE_LABEL, EVENT_TEXT_MAX_WIDTH,
        )

        self.yes_button.draw(screen, mouse_pos, icon_name=DICE_FACE_ICONS[6])
        self.no_button.draw(screen, mouse_pos)

    def _draw_dice(self, screen, mouse_pos):
        cx = SCREEN_WIDTH // 2
        shown_face = self.current_face if self.stage == STAGE_ROLLING else self.final_roll
        icon = ImageManager.get_scaled(DICE_FACE_ICONS[shown_face], (DICE_ICON_SIZE, DICE_ICON_SIZE))
        screen.blit(icon, icon.get_rect(center=(cx, 280)))

        if self.stage == STAGE_ROLLING:
            self.stop_button.draw(screen, mouse_pos)

    def _draw_result(self, screen):
        cx = SCREEN_WIDTH // 2
        outcome = self.event.get_outcome(self.final_roll)

        y = draw_wrapped_text_centered(
            screen, cx, 130, outcome.text,
            TEXT_COLOR, FONT_SIZE_LABEL, EVENT_TEXT_MAX_WIDTH,
        )

        y += 30
        for label, value in (
                ("Золото", outcome.gold_delta),
                ("Серебро", outcome.silver_delta),
                ("Ходы", outcome.moves_delta),
        ):
            if value == 0:
                continue
            sign = "+" if value > 0 else ""
            color = WARNING_TEXT_COLOR if value < 0 else TEXT_COLOR
            surf = get_font(FONT_SIZE_LABEL + 4).render(f"{label}: {sign}{value}", True, color)
            screen.blit(surf, surf.get_rect(center=(cx, y)))
            y += 34

        if outcome.displacement_cells:
            surf = get_font(FONT_SIZE_LABEL + 4).render(
                f"Смещение: {outcome.displacement_cells} кл.", True, WARNING_TEXT_COLOR,
            )
            screen.blit(surf, surf.get_rect(center=(cx, y)))
            y += 34

        if outcome.effect_type:
            label = EFFECT_LABELS_RU.get(outcome.effect_type, outcome.effect_type)
            color = WARNING_TEXT_COLOR if outcome.effect_type == EFFECT_HALF_INCOME else TEXT_COLOR
            turns = outcome.effect_duration
            turns_word = "черёд" if turns == 1 else "черёда" if turns < 5 else "черёдов"
            surf = get_font(FONT_SIZE_LABEL + 4).render(
                f"{label}: {turns} {turns_word}", True, color,
            )
            screen.blit(surf, surf.get_rect(center=(cx, y)))
            y += 34

        self.continue_button.draw(screen, pygame.mouse.get_pos())