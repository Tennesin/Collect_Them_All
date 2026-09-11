import random
from game.game_config import GOLD_CELL_BOX_RADIUS, GOLD_CELL_BUFFER

class GoldCellGenerator:

    def __init__(self, field, count):
        self.field = field
        self.count = count
        self.radius = GOLD_CELL_BOX_RADIUS
        self.buffer = GOLD_CELL_BUFFER

    def generate(self):
        placed = 0
        attempts = 0
        max_attempts = max(200, self.count * 200)
        while placed < self.count and attempts < max_attempts:
            attempts += 1
            if self._try_place_one():
                placed += 1
        return placed

    def _try_place_one(self):
        field = self.field
        r = self.radius
        buffer = self.buffer
        min_coord = r + buffer
        max_x = field.width - 1 - r - buffer
        max_y = field.height - 1 - r - buffer
        if max_x < min_coord or max_y < min_coord:
            return False

        gx = random.randint(min_coord, max_x)
        gy = random.randint(min_coord, max_y)

        if not self._area_is_clear(gx, gy):
            return False

        segments = self._corner_segments(gx, gy)
        wall_cells = {cell for segment in segments for cell in segment}

        for cx, cy in wall_cells:
            field.set_obstacle(cx, cy, True, 'wall')

        if not field.is_connected():
            for cx, cy in wall_cells:
                field.set_obstacle(cx, cy, False)
            return False

        field.wall_segments.extend(segments)
        field.add_gold_cell(gx, gy)
        self._reserve_box(gx, gy)
        return True

    def _area_is_clear(self, gx, gy):
        field = self.field
        r = self.radius + self.buffer
        for dx in range(-r, r + 1):
            for dy in range(-r, r + 1):
                x, y = gx + dx, gy + dy
                if not field.in_bounds(x, y):
                    return False
                if field.obstacle_grid[x][y] or (x, y) in field.reserved_cells:
                    return False
        return True

    def _corner_segments(self, gx, gy):
        r = self.radius
        segments = []
        for sign_x, sign_y in [(-1, -1), (1, -1), (-1, 1), (1, 1)]:
            corner_x, corner_y = gx + sign_x * r, gy + sign_y * r
            arm_x = (gx + sign_x * (r - 1), corner_y)
            arm_y = (corner_x, gy + sign_y * (r - 1))
            segments.append([arm_x, (corner_x, corner_y), arm_y])
        return segments

    def _reserve_box(self, gx, gy):
        field = self.field
        outer = self.radius + self.buffer
        for dx in range(-outer, outer + 1):
            for dy in range(-outer, outer + 1):
                x, y = gx + dx, gy + dy
                if field.in_bounds(x, y):
                    field.reserve_cell(x, y)