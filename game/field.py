from collections import deque

class Field:
    """Хранит сетку препятствий и умеет искать путь. Не знает, как эти препятствия генерируются."""

    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.obstacle_grid = [[False] * height for _ in range(width)]
        self.obstacle_type = [[None] * height for _ in range(width)]
        self.color_variants = [[None] * height for _ in range(width)]
        self.wall_segments = []
        self._obstacle_count = 0

        # Победная клетка — всегда правый нижний угол поля.
        self.win_cell = (width - 1, height - 1)
        self.start_cell = (0, 0)

        self.gold_cell_positions = []
        self.reserved_cells = {self.win_cell, self.start_cell}
        self._finish_distances = None   # кэш BFS от финиша (препятствия статичны после генерации)

    def reserve_cell(self, x, y):
        self.reserved_cells.add((x, y))

    def add_gold_cell(self, x, y):
        self.gold_cell_positions.append((x, y))
        self.reserve_cell(x, y)

    def in_bounds(self, x, y):
        return 0 <= x < self.width and 0 <= y < self.height

    def is_free(self, x, y):
        return not self.obstacle_grid[x][y]

    def set_obstacle(self, x, y, value, kind=None):
        """Единая точка изменения препятствий."""
        current = self.obstacle_grid[x][y]
        self.obstacle_grid[x][y] = value
        self.obstacle_type[x][y] = kind if value else None
        if current != value:
            self._obstacle_count += 1 if value else -1

    def count_obstacles(self):
        return self._obstacle_count

    def is_connected(self):
        """Проверяет, что все свободные клетки поля образуют одну связную область."""
        if self.obstacle_grid[0][0]:
            return False
        visited = [[False] * self.height for _ in range(self.width)]
        queue = deque([(0, 0)])
        visited[0][0] = True
        free_count = 0
        total_free = self.width * self.height - self._obstacle_count
        while queue:
            cx, cy = queue.popleft()
            free_count += 1
            for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nx, ny = cx + dx, cy + dy
                if self.in_bounds(nx, ny) and not self.obstacle_grid[nx][ny] and not visited[nx][ny]:
                    visited[nx][ny] = True
                    queue.append((nx, ny))
        return free_count == total_free

    def get_neighbors(self, x, y, ignore_obstacles=False):
        neighbors = []
        for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nx, ny = x + dx, y + dy
            if self.in_bounds(nx, ny) and (ignore_obstacles or self.is_free(nx, ny)):
                neighbors.append((nx, ny))
        return neighbors

    def find_path(self, start, goal, allowed_cells=None, ignore_obstacles=False):
        if start == goal:
            return []
        if not ignore_obstacles and not self.is_free(*goal):
            return []
        if allowed_cells is not None and goal not in allowed_cells:
            return []

        queue = deque([start])
        visited = {start: None}
        while queue:
            current = queue.popleft()
            if current == goal:
                break
            for neighbor in self.get_neighbors(*current, ignore_obstacles=ignore_obstacles):
                if allowed_cells is not None and neighbor not in allowed_cells:
                    continue
                if neighbor not in visited:
                    visited[neighbor] = current
                    queue.append(neighbor)
        if goal not in visited:
            return []
        return self._restore_path(visited, start, goal)

    @staticmethod
    def _restore_path(visited, start, goal):
        path = []
        current = goal
        while current != start:
            path.append(current)
            current = visited[current]
        path.reverse()
        return path

    def find_path_optimistic(self, start, goal, known_cells):
        """Как find_path, но клетки вне known_cells считаются проходимыми: реальные
        препятствия учитываются только там, где актор их уже видел. Не раскрывает
        боту неисследованную часть карты; при обнаружении блока путь перестраивают."""
        if start == goal:
            return []
        if goal in known_cells and not self.is_free(*goal):
            return []
        queue = deque([start])
        visited = {start: None}
        while queue:
            current = queue.popleft()
            if current == goal:
                break
            cx, cy = current
            for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nxt = (cx + dx, cy + dy)
                if not self.in_bounds(*nxt) or nxt in visited:
                    continue
                if nxt in known_cells and not self.is_free(*nxt):
                    continue
                visited[nxt] = current
                queue.append(nxt)
        if goal not in visited:
            return []
        return self._restore_path(visited, start, goal)

    def optimistic_tree(self, start, known_cells, avoid=None):
        """Один BFS от start с оптимистичным допущением (как find_path_optimistic):
        неизвестные клетки проходимы, известные препятствия нет. avoid - клетки,
        которые нельзя проходить насквозь. Возвращает (расстояния, родители)."""
        distances = {start: 0}
        parents = {start: None}
        queue = deque([start])
        while queue:
            current = queue.popleft()
            cx, cy = current
            next_distance = distances[current] + 1
            for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                nxt = (cx + dx, cy + dy)
                if nxt in distances or not self.in_bounds(*nxt):
                    continue
                if avoid and nxt in avoid:
                    continue
                if nxt in known_cells and not self.is_free(*nxt):
                    continue
                distances[nxt] = next_distance
                parents[nxt] = current
                queue.append(nxt)
        return distances, parents

    def path_from_tree(self, parents, start, goal):
        """Путь до goal по дереву родителей из optimistic_tree (пустой, если цель недостижима)."""
        if goal not in parents:
            return []
        return self._restore_path(parents, start, goal)

    def bfs_distances(self, source):
        """Расстояния (в шагах) от source до всех достижимых свободных клеток: {клетка: расстояние}."""
        distances = {source: 0}
        queue = deque([source])
        while queue:
            current = queue.popleft()
            next_distance = distances[current] + 1
            for neighbor in self.get_neighbors(*current):
                if neighbor not in distances:
                    distances[neighbor] = next_distance
                    queue.append(neighbor)
        return distances

    def distances_to_finish(self):
        """Карта расстояний до финиша. Считается один раз, вызывать только после генерации поля."""
        if self._finish_distances is None:
            self._finish_distances = self.bfs_distances(self.win_cell)
        return self._finish_distances

    def nearest_free_cell(self, x, y):
        """BFS до ближайшей свободной клетки — используется, чтобы вытолкнуть игрока
        со стены/блока, если эффект прохода сквозь препятствия истёк прямо на них."""
        if self.is_free(x, y):
            return (x, y)
        visited = {(x, y)}
        queue = deque([(x, y)])
        while queue:
            cx, cy = queue.popleft()
            for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nx, ny = cx + dx, cy + dy
                if not self.in_bounds(nx, ny) or (nx, ny) in visited:
                    continue
                visited.add((nx, ny))
                if self.is_free(nx, ny):
                    return (nx, ny)
                queue.append((nx, ny))
        return (x, y)  # запасной вариант, теоретически не должен сработать