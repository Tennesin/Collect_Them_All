import random
import pygame
from settings import *
from widgets import Button, get_font, draw_wrapped_text_centered
from game.rendering.image_manager import ImageManager
from game.tween import Tween, ease_out_cubic
from scene.scenes import Scene

STAGE_PROMPT = "prompt"    # текст события + кнопки "Да"/"Нет"
STAGE_ROLLING = "rolling"  # кубик крутится
STAGE_FROZEN = "frozen"    # кубик остановился, 1 секунда показа итоговой грани
STAGE_RESULT = "result"    # текст исхода + награды/штрафы + кнопка "Продолжить"

class EventScene(Scene):
    """Оверлей одного случайного события: подтверждение -> бросок кубика -> результат."""

    def __init__(self, manager, gameplay_scene, player, event_definition):
        super().__init__(manager)
        self.gameplay_scene = gameplay_scene
        self.world = gameplay_scene.world
        self.player = player
        self.event = event_definition

        self.stage = STAGE_PROMPT
        self.roll_timer = 0.0
        self.face_change_timer = 0.0
        self.freeze_timer = 0.0
        self.current_face = random.randint(1, 6)
        self.final_roll = None
        self._outcome_applied = False
        self._result_lines = []   # [(текст, цвет)] — строится один раз при применении исхода
        self._outcome = None          # исход, полученный в _apply_outcome
        self._pending_effect = None   # эффект создан, но ещё не наложен
        self._committed = False       # отложенная часть исхода уже применена (или отменена)

        self._alpha = 0
        self._fade = Tween(0, 255, FADE_POPUP_IN_DURATION, ease_out_cubic)
        self._closing = False
        self._pending_action = None

        cx = SCREEN_WIDTH // 2
        btn_w, btn_h = 200, 52
        gap = 20
        self.yes_button = Button((cx - btn_w - gap // 2, 480, btn_w, btn_h), "Да")
        self.no_button = Button((cx + gap // 2, 480, btn_w, btn_h), "Нет")
        self.stop_button = Button((cx - btn_w // 2, 480, btn_w, btn_h), "Стоп")
        self.continue_button = Button((cx - 120, 500, 240, btn_h), "Продолжить")

    def on_enter(self):
        self._fade = Tween(0, 255, FADE_POPUP_IN_DURATION, ease_out_cubic)
        self._closing = False
        self.world.event_popup_open = True

    def on_exit(self):
        self.world.event_popup_open = False

    def _start_closing(self, action):
        if self._closing:
            return
        self._closing = True
        self._pending_action = action
        self._fade = Tween(self._alpha, 0, FADE_POPUP_OUT_DURATION, ease_out_cubic)

    def _commit_and_close(self):
        """Окно закрыто игроком: теперь запускаем эффект и смещение."""
        if not self._committed and self._outcome is not None:
            self._committed = True
            self.world.event_resolver.commit(self.player, self._outcome, self._pending_effect)
        self.manager.pop()

    # --- события ввода ---

    def handle_event(self, event):
        if self._closing:
            return
        if event.type != pygame.MOUSEBUTTONDOWN or event.button != 1:
            return

        if self.stage == STAGE_PROMPT:
            if self.yes_button.collidepoint(event.pos):
                self._start_rolling()
            elif self.no_button.collidepoint(event.pos):
                self._start_closing(self.manager.pop)
        elif self.stage == STAGE_ROLLING:
            if self.stop_button.collidepoint(event.pos):
                self._freeze_roll()
        elif self.stage == STAGE_RESULT:
            if self.continue_button.collidepoint(event.pos):
                if self.manager.current is self:
                    self._start_closing(self._commit_and_close)

    # --- обновление ---

    def update(self, dt):
        self._alpha = self._fade.update(dt)

        if self._closing and self._fade.finished:
            action = self._pending_action
            self._pending_action = None
            if action:
                action()
            return

        self.gameplay_scene.update_world_only(dt)

        # Партия закончилась, пока окно было открыто: закрываем без применения исхода.
        if self.world.winner is not None and not self._closing:
            self._committed = True
            self._start_closing(self.manager.pop)
            return

        if self._closing:
            return
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
            self.current_face = self._next_different_face(self.current_face)

    @staticmethod
    def _next_different_face(previous):
        """Гарантирует, что новая грань отличается от предыдущей."""
        return random.choice([face for face in range(1, 7) if face != previous])

    def _update_frozen(self, dt):
        self.freeze_timer += dt
        if self.freeze_timer >= DICE_RESULT_FREEZE_DURATION:
            self.stage = STAGE_RESULT
            if not self._outcome_applied:
                self._outcome_applied = True
                self._apply_outcome()

    def _start_rolling(self):
        self.stage = STAGE_ROLLING
        self.roll_timer = 0.0
        self.face_change_timer = 0.0
        self.final_roll = self.world.event_resolver.roll()

    def _freeze_roll(self):
        self.current_face = self.final_roll
        self.stage = STAGE_FROZEN
        self.freeze_timer = 0.0

    def _apply_outcome(self):
        outcome, effect = self.world.event_resolver.resolve(self.player, self.event, self.final_roll)
        self._outcome = outcome
        self._pending_effect = effect
        lines = []
        for label, value in (("Золото", outcome.gold_delta), ("Серебро", outcome.silver_delta)):
            if value:
                sign = "+" if value > 0 else ""
                lines.append((f"{label}: {sign}{value}", WARNING_TEXT_COLOR if value < 0 else TEXT_COLOR))
        if outcome.displacement_cells:
            lines.append((f"Смещение: {outcome.displacement_cells} кл.", WARNING_TEXT_COLOR))
        if effect is not None:
            color = WARNING_TEXT_COLOR if effect.warning else TEXT_COLOR
            lines.append((f"{effect.label}: {effect.duration_seconds:g} с", color))
        self._result_lines = lines

    # --- отрисовка ---

    def draw(self, screen):
        self.gameplay_scene.draw(screen)

        content = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        content.fill(EVENT_POPUP_BG_COLOR)

        mouse_pos = pygame.mouse.get_pos()
        if self.stage == STAGE_PROMPT:
            self._draw_prompt(content, mouse_pos)
        elif self.stage in (STAGE_ROLLING, STAGE_FROZEN):
            self._draw_dice(content, mouse_pos)
        elif self.stage == STAGE_RESULT:
            self._draw_result(content, mouse_pos)

        content.set_alpha(int(self._alpha))
        screen.blit(content, (0, 0))

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

    def _draw_result(self, screen, mouse_pos):
        cx = SCREEN_WIDTH // 2
        outcome = self.event.get_outcome(self.final_roll)

        y = draw_wrapped_text_centered(
            screen, cx, 130, outcome.text,
            TEXT_COLOR, FONT_SIZE_LABEL, EVENT_TEXT_MAX_WIDTH,
        )

        y += 30
        font = get_font(FONT_SIZE_LABEL + 4)
        for text, color in self._result_lines:
            surf = font.render(text, True, color)
            screen.blit(surf, surf.get_rect(center=(cx, y)))
            y += 34

        self.continue_button.draw(screen, mouse_pos)