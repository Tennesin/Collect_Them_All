import math
from settings import PLAYER_COLORS
from game.game_config import STARTING_GOLD, STARTING_SILVER

class Player:
    """Отвечает только за собственное состояние: позицию, цвет и движение по пути."""

    def __init__(self, field, start_cell=(0, 0), speed=5.0, color_key="red"):
        self.field = field
        self.grid_x, self.grid_y = start_cell
        self.pos_x = self.grid_x + 0.5
        self.pos_y = self.grid_y + 0.5
        self.path = []
        self.moving = False
        self.speed = speed

        self.color_key = color_key
        self.color = PLAYER_COLORS[color_key]

        # Личный бюджет игрока — собирается по всей карте.
        self.gold = STARTING_GOLD
        self.silver = STARTING_SILVER

        # Текст предупреждения ("Недостаточно N золота...").
        self.warning_message = None

        # Туман войны.
        self.visible_cells = set()
        self.explored_cells = set()

        # Внешний наблюдатель (например, Camera.center_on), вызывается при каждом изменении позиции.
        self.on_move = None
        self.on_cell_reached = None

    def follow_path(self, path):
        """Идёт по уже готовому (возможно, обрезанному снаружи) пути."""
        if not path:
            return False
        self.path = list(path)
        self.moving = True
        self._notify_move()
        return True

    def stop_movement(self):
        """Немедленно прерывает движение по нажатию SPACE."""
        if not self.moving:
            return False
        self.path = []
        self.moving = False
        self.pos_x = self.grid_x + 0.5
        self.pos_y = self.grid_y + 0.5
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
            self._notify_cell_reached()
        else:
            self.pos_x += dx / dist * step
            self.pos_y += dy / dist * step
        self._notify_move()

    def _notify_move(self):
        if self.on_move:
            self.on_move(self.pos_x, self.pos_y)

    def _notify_cell_reached(self):
        if self.on_cell_reached:
            self.on_cell_reached()