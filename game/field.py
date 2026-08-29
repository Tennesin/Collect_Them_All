from collections import deque


class Field:
    """Хранит сетку препятствий и умеет искать путь. Не знает, как эти препятствия генерируются."""

    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.obstacle_grid = [[False] * height for _ in range(width)]
        self.obstacle_type = [[None] * height for _ in range(width)]
        self.wall_segments = []

        # Победная клетка — всегда правый нижний угол поля.
        self.win_cell = (width - 1, height - 1)

        # Позиции золотых клеток; заполняются GoldCellGenerator'ом снаружи —
        # Field ничего не знает про то, КАК их расставляют.
        self.gold_cell_positions = []

        # Клетки, которые генераторы препятствий никогда не должны занимать:
        # победная клетка + центры уже расставленных золотых клеток.
        self.reserved_cells = {self.win_cell}

    def reserve_cell(self, x, y):
        self.reserved_cells.add((x, y))

    def add_gold_cell(self, x, y):
        """Регистрирует клетку (x, y) как золотую и сразу резервирует её,
        чтобы следующие золотые клетки и обычные препятствия её не перекрыли."""
        self.gold_cell_positions.append((x, y))
        self.reserve_cell(x, y)

    def in_bounds(self, x, y):
        return 0 <= x < self.width and 0 <= y < self.height

    def is_free(self, x, y):
        return not self.obstacle_grid[x][y]

    def count_obstacles(self):
        return sum(sum(row) for row in self.obstacle_grid)

    def is_connected(self):
        """Проверяет, что все свободные клетки поля образуют одну связную область."""
        if self.obstacle_grid[0][0]:
            return False
        visited = [[False] * self.height for _ in range(self.width)]
        queue = deque([(0, 0)])
        visited[0][0] = True
        free_count = 0
        total_free = sum(
            1
            for x in range(self.width)
            for y in range(self.height)
            if not self.obstacle_grid[x][y]
        )
        while queue:
            cx, cy = queue.popleft()
            free_count += 1
            for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nx, ny = cx + dx, cy + dy
                if self.in_bounds(nx, ny) and not self.obstacle_grid[nx][ny] and not visited[nx][ny]:
                    visited[nx][ny] = True
                    queue.append((nx, ny))
        return free_count == total_free

    def get_neighbors(self, x, y):
        neighbors = []
        for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nx, ny = x + dx, y + dy
            if self.in_bounds(nx, ny) and self.is_free(nx, ny):
                neighbors.append((nx, ny))
        return neighbors

    def find_path(self, start, goal):
        if start == goal:
            return []
        if not self.is_free(*goal):
            return []
        queue = deque([start])
        visited = {start: None}
        while queue:
            current = queue.popleft()
            if current == goal:
                break
            for neighbor in self.get_neighbors(*current):
                if neighbor not in visited:
                    visited[neighbor] = current
                    queue.append(neighbor)
        if goal not in visited:
            return []
        path = []
        current = goal
        while current != start:
            path.append(current)
            current = visited[current]
        path.reverse()
        return path