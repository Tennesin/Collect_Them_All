import random

class ObstacleGenerator:

    def __init__(self, field, max_obstacle_cells):
        self.field = field
        self.max_obstacle_cells = max_obstacle_cells

    def generate(self):
        occupied = 0
        attempts = 0
        max_attempts = 5000
        while occupied < self.max_obstacle_cells and attempts < max_attempts:
            attempts += 1
            if random.random() < 0.5:
                w = random.randint(1, 3)
                h = random.randint(1, 3)
                if self._try_place_rectangle(w, h, 'block'):
                    occupied += w * h
            else:
                length = random.randint(3, 9)
                if self._generate_wall(length):
                    occupied += length

    # --- Прямоугольные блоки ---

    def _try_place_rectangle(self, w, h, kind):
        field = self.field
        if field.count_obstacles() + w * h > self.max_obstacle_cells:
            return False
        max_x = field.width - w
        max_y = field.height - h
        if max_x < 0 or max_y < 0:
            return False
        for _ in range(50):
            x = random.randint(0, max_x)
            y = random.randint(0, max_y)
            if self._rect_occupied(x, y, w, h):
                continue
            self._set_rect(x, y, w, h, True, kind)
            if field.is_connected():
                return True
            self._set_rect(x, y, w, h, False, None)
        return False

    def _rect_occupied(self, x, y, w, h):
        field = self.field
        for dx in range(w):
            for dy in range(h):
                cx, cy = x + dx, y + dy
                if field.obstacle_grid[cx][cy] or (cx, cy) in field.reserved_cells:
                    return True
        return False

    def _set_rect(self, x, y, w, h, value, kind):
        field = self.field
        for dx in range(w):
            for dy in range(h):
                field.set_obstacle(x + dx, y + dy, value, kind)

    # --- Стены ---

    def _generate_wall(self, length):
        field = self.field
        if field.count_obstacles() + length > self.max_obstacle_cells:
            return False
        shape = random.choice(['straight', 'L', 'zigzag'])
        for _ in range(100):
            start_x = random.randint(0, field.width - 1)
            start_y = random.randint(0, field.height - 1)
            if field.obstacle_grid[start_x][start_y] or (start_x, start_y) in field.reserved_cells:
                continue

            cells = self._build_wall_cells(shape, start_x, start_y, length)
            if cells is None or len(cells) != length:
                continue
            if self._wall_too_close(cells):
                continue

            for cx, cy in cells:
                field.set_obstacle(cx, cy, True, 'wall')

            if field.is_connected():
                field.wall_segments.append(cells)
                return True

            for cx, cy in cells:
                field.set_obstacle(cx, cy, False)
        return False

    def _build_wall_cells(self, shape, start_x, start_y, length):
        if shape == 'straight':
            return self._build_straight(start_x, start_y, length)
        if shape == 'L':
            return self._build_l_shape(start_x, start_y, length)
        if shape == 'zigzag':
            return self._build_zigzag(start_x, start_y, length)
        return None

    def _blocked(self, x, y, cells):
        field = self.field
        return (
            not field.in_bounds(x, y)
            or field.obstacle_grid[x][y]
            or (x, y) in field.reserved_cells
            or (x, y) in cells
        )

    def _build_straight(self, start_x, start_y, length):
        direction = random.choice([(1, 0), (-1, 0), (0, 1), (0, -1)])
        cells = [(start_x, start_y)]
        cx, cy = start_x, start_y
        for _ in range(length - 1):
            nx, ny = cx + direction[0], cy + direction[1]
            if self._blocked(nx, ny, cells):
                break
            cells.append((nx, ny))
            cx, cy = nx, ny
        return cells

    def _build_l_shape(self, start_x, start_y, length):
        first_dir = random.choice([(1, 0), (-1, 0), (0, 1), (0, -1)])
        second_dirs = [(1, 0), (-1, 0)] if first_dir[0] == 0 else [(0, 1), (0, -1)]
        second_dir = random.choice(second_dirs)
        split = random.randint(1, length - 2)

        cells = [(start_x, start_y)]
        cx, cy = start_x, start_y
        for _ in range(split):
            nx, ny = cx + first_dir[0], cy + first_dir[1]
            if self._blocked(nx, ny, cells):
                return cells
            cells.append((nx, ny))
            cx, cy = nx, ny
        if len(cells) != split + 1:
            return cells

        for _ in range(length - split - 1):
            nx, ny = cx + second_dir[0], cy + second_dir[1]
            if self._blocked(nx, ny, cells):
                return cells
            cells.append((nx, ny))
            cx, cy = nx, ny
        return cells

    def _build_zigzag(self, start_x, start_y, length):
        direction = random.choice([(1, 0), (-1, 0), (0, 1), (0, -1)])
        cells = [(start_x, start_y)]
        cx, cy = start_x, start_y
        remaining = length - 1

        while remaining > 0:
            segment_len = 2 if remaining >= 2 else 1
            blocked = False
            for _ in range(segment_len):
                nx, ny = cx + direction[0], cy + direction[1]
                if self._blocked(nx, ny, cells):
                    blocked = True
                    break
                cells.append((nx, ny))
                cx, cy = nx, ny
                remaining -= 1

            if blocked:
                break
            if remaining > 0:
                direction = random.choice([(0, 1), (0, -1)] if direction[0] != 0 else [(1, 0), (-1, 0)])

        return cells

    def _wall_too_close(self, cells):
        field = self.field
        for x, y in cells:
            for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nx, ny = x + dx, y + dy
                if field.in_bounds(nx, ny) and field.obstacle_grid[nx][ny] and field.obstacle_type[nx][ny] == 'wall':
                    if (nx, ny) not in cells:
                        return True
        return False