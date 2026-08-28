import math


class Player:
    """Отвечает только за собственное состояние: позицию и движение по пути.
    Ничего не знает ни про Game, ни про pygame, ни про камеру напрямую."""

    def __init__(self, field, start_cell=(0, 0), speed=5.0):
        self.field = field
        self.grid_x, self.grid_y = start_cell
        self.pos_x = self.grid_x + 0.5
        self.pos_y = self.grid_y + 0.5
        self.path = []
        self.moving = False
        self.speed = speed

        # Внешний наблюдатель (например, Camera.center_on), вызывается при каждом изменении позиции.
        self.on_move = None

    def set_goal(self, goal_cell):
        """Пытается проложить путь к goal_cell. Возвращает True, если движение началось."""
        path = self.field.find_path((self.grid_x, self.grid_y), goal_cell)
        if not path:
            return False
        self.path = path
        self.moving = True
        self._notify_move()
        return True

    def update(self, dt):
        if not self.moving or not self.path:
            self.moving = False
            return
        next_cell = self.path[0]
        target_wx = next_cell[0] + 0.5
        target_wy = next_cell[1] + 0.5
        dx = target_wx - self.pos_x
        dy = target_wy - self.pos_y
        dist = math.hypot(dx, dy)
        step = self.speed * dt
        if dist <= step:
            self.pos_x = target_wx
            self.pos_y = target_wy
            self.grid_x, self.grid_y = next_cell
            self.path.pop(0)
            if not self.path:
                self.moving = False
        else:
            self.pos_x += dx / dist * step
            self.pos_y += dy / dist * step
        self._notify_move()

    def _notify_move(self):
        if self.on_move:
            self.on_move(self.pos_x, self.pos_y)