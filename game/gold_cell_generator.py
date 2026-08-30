import random
from game.game_config import MIN_GOLD_CELLS, MAX_GOLD_CELLS, GOLD_CELL_BOX_RADIUS

class GoldCellGenerator:

    def __init__(self, field):
        self.field = field
        self.radius = GOLD_CELL_BOX_RADIUS  # 2 -> короб 5x5

    def generate(self):
        count = random.randint(MIN_GOLD_CELLS, MAX_GOLD_CELLS)
        placed = 0
        attempts = 0
        max_attempts = count * 200
        while placed < count and attempts < max_attempts:
            attempts += 1
            if self._try_place_one():
                placed += 1
        return placed

    def _try_place_one(self):
        field = self.field
        r = self.radius
        min_coord = r
        max_x = field.width - 1 - r
        max_y = field.height - 1 - r
        if max_x < min_coord or max_y < min_coord:
            return False

        gx = random.randint(min_coord, max_x)
        gy = random.randint(min_coord, max_y)

        if not self._area_is_clear(gx, gy):
            return False

        segments = self._corner_segments(gx, gy)
        wall_cells = {cell for segment in segments for cell in segment}

        for cx, cy in wall_cells:
            field.obstacle_grid[cx][cy] = True
            field.obstacle_type[cx][cy] = 'wall'

        if not field.is_connected():
            for cx, cy in wall_cells:
                field.obstacle_grid[cx][cy] = False
                field.obstacle_type[cx][cy] = None
            return False

        field.wall_segments.extend(segments)
        field.add_gold_cell(gx, gy)
        return True

    def _area_is_clear(self, gx, gy):
        field = self.field
        r = self.radius
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