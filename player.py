import math

class Player:
    def __init__(self, game):
        self.game = game
        self.grid_x = 0
        self.grid_y = 0
        self.pos_x = 0.5
        self.pos_y = 0.5
        self.path = []
        self.moving = False
        self.speed = 5.0

    def set_goal(self, goal_cell):
        start = (self.grid_x, self.grid_y)
        self.path = self.game.field.find_path(start, goal_cell)
        if self.path:
            self.moving = True
            self.game.center_on_player()

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