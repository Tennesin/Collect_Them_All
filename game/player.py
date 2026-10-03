import math
from game.game_config import (
    STARTING_GOLD, STARTING_SILVER, PLAYER_BASE_SPEED,
    MIN_SPEED_MULTIPLIER, MAX_SPEED_MULTIPLIER,
)

class Player:
    """Отвечает за собственное состояние: позицию, движение по пути, ресурсы и эффекты."""

    def __init__(self, field, start_cell=(0, 0), base_speed=PLAYER_BASE_SPEED,
                 color_key="red", color=(255, 255, 255), is_bot=False):
        self.field = field
        self.grid_x, self.grid_y = start_cell   # последняя достигнутая клетка
        self.pos_x = self.grid_x + 0.5
        self.pos_y = self.grid_y + 0.5
        self.path = []                           # path[0] - клетка, к которой игрок идёт прямо сейчас
        self.base_speed = base_speed

        self.color_key = color_key
        self.color = color
        self.is_bot = is_bot
        self.controller = None   # у бота: объект с методом update(dt); у человека None (ввод идёт через InputHandler)

        self.gold = STARTING_GOLD
        self.silver = STARTING_SILVER

        self.warning_message = None
        self.active_effects = []   # список экземпляров Effect

        self.visible_cells = set()
        self.explored_cells = set()
        self.known_cells = self.explored_cells   # что игрок "знает" сейчас: explored (+вся карта при полной видимости)
        self.vision_dirty = False  # True -> мир пересчитает обзор в ближайшем кадре

        self.on_cell_reached = None

    # --- Состояние движения ---

    @property
    def moving(self):
        return bool(self.path)

    @property
    def anchor_cell(self):
        """Клетка, от которой надо строить новый маршрут: ближайшая цель
        текущего движения либо текущая клетка, если игрок стоит."""
        return self.path[0] if self.path else (self.grid_x, self.grid_y)

    @property
    def ignores_obstacles(self):
        return any(getattr(effect, "ignores_obstacles", False) for effect in self.active_effects)

    @property
    def speed_multiplier(self):
        value = 1.0
        for effect in self.active_effects:
            value *= getattr(effect, "speed_multiplier", 1.0)
        return max(MIN_SPEED_MULTIPLIER, min(MAX_SPEED_MULTIPLIER, value))

    @property
    def speed(self):
        return self.base_speed * self.speed_multiplier

    # --- Команды ---

    def follow_path(self, path):
        """path строится от anchor_cell. Если игрок уже идёт, он доходит до
        anchor_cell и дальше следует новому маршруту (без отката назад)."""
        if self.path:
            self.path = [self.path[0]] + list(path)
        else:
            self.path = list(path)

    def stop_movement(self):
        """Дотормаживает до центра ближайшей клетки маршрута."""
        if not self.path:
            return False
        self.path = self.path[:1]
        return True

    def trim_blocked_path(self):
        """Если эффект «проход сквозь стены» закончился, обрезает маршрут перед
        первой непроходимой клеткой."""
        if self.ignores_obstacles or not self.path:
            return
        for i, (x, y) in enumerate(self.path):
            if not self.field.is_free(x, y):
                self.path = self.path[:i]
                if i == 0:  # шли в стену, остановились между клетками - возвращаем в центр
                    self.pos_x = self.grid_x + 0.5
                    self.pos_y = self.grid_y + 0.5
                return

    # --- Кадр ---

    def update(self, dt):
        if not self.path:
            return
        budget = self.speed * dt
        while self.path and budget > 0:
            next_cell = self.path[0]
            target_x = next_cell[0] + 0.5
            target_y = next_cell[1] + 0.5
            dx = target_x - self.pos_x
            dy = target_y - self.pos_y
            dist = math.hypot(dx, dy)
            if dist <= budget:
                budget -= dist
                self.pos_x = target_x
                self.pos_y = target_y
                self.grid_x, self.grid_y = next_cell
                self.path.pop(0)
                # обработчик может оборвать маршрут (событие, телепорт, финиш)
                if self.on_cell_reached:
                    self.on_cell_reached()
            else:
                self.pos_x += dx / dist * budget
                self.pos_y += dy / dist * budget
                budget = 0

    # --- Временные эффекты ---

    def add_effect(self, effect):
        """Эффект с тем же key не накладывается второй раз, а сливается с действующим (см. Effect.absorb)."""
        if effect is None or effect.duration_seconds <= 0:
            return
        from game.effects.effect_reader import EffectReader
        for existing in self.active_effects:
            if existing.key == effect.key:
                existing.absorb(effect)
                EffectReader.notify_effect_applied(self, effect)
                self.vision_dirty = True
                return
        EffectReader.notify_effect_applied(self, effect)
        self.active_effects.append(effect)
        self.vision_dirty = True