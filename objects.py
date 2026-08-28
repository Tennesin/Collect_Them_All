import random
from collections import deque
from settings import *

class Field:
    def __init__(self, width, height, max_obstacle_cells):
        self.width = width
        self.height = height
        self.max_obstacle_cells = max_obstacle_cells
        self.obstacle_grid = [[False] * height for _ in range(width)]
        self.obstacle_type = [[None] * height for _ in range(width)]
        self.wall_segments = []
        self.generate_obstacles()

    def generate_obstacles(self):
        occupied = 0
        attempts = 0
        max_attempts = 5000
        while occupied < self.max_obstacle_cells and attempts < max_attempts:
            attempts += 1
            if random.random() < 0.5:
                w = random.randint(1, 3)
                h = random.randint(1, 3)
                kind = 'block'
                if self._try_place_rectangle(w, h, kind):
                    occupied += w * h
            else:
                length = random.randint(3, 9)
                if self._generate_wall(length):
                    occupied += length
            attempts += 1

    def _try_place_rectangle(self, w, h, kind):
        if self._count_obstacles() + w * h > self.max_obstacle_cells:
            return False
        max_x = self.width - w
        max_y = self.height - h
        if max_x < 0 or max_y < 0:
            return False
        for _ in range(50):
            x = random.randint(0, max_x)
            y = random.randint(0, max_y)
            valid = True
            for dx in range(w):
                for dy in range(h):
                    if self.obstacle_grid[x + dx][y + dy]:
                        valid = False
                        break
                if not valid:
                    break
            if not valid:
                continue
            # Временно занимаем
            for dx in range(w):
                for dy in range(h):
                    self.obstacle_grid[x + dx][y + dy] = True
                    self.obstacle_type[x + dx][y + dy] = kind
            if self._is_connected():
                return True
            else:
                for dx in range(w):
                    for dy in range(h):
                        self.obstacle_grid[x + dx][y + dy] = False
                        self.obstacle_type[x + dx][y + dy] = None
        return False

    def _generate_wall(self, length):
        if self._count_obstacles() + length > self.max_obstacle_cells:
            return False
        shape = random.choice(['straight', 'L', 'zigzag'])
        for _ in range(100):
            start_x = random.randint(0, self.width - 1)
            start_y = random.randint(0, self.height - 1)
            if self.obstacle_grid[start_x][start_y]:
                continue
            cells = [(start_x, start_y)]
            current_x, current_y = start_x, start_y
            direction = None
            if shape == 'straight':
                dirs = [(1,0), (-1,0), (0,1), (0,-1)]
                direction = random.choice(dirs)
                for _ in range(length - 1):
                    nx = current_x + direction[0]
                    ny = current_y + direction[1]
                    if not (0 <= nx < self.width and 0 <= ny < self.height):
                        break
                    if self.obstacle_grid[nx][ny] or (nx, ny) in cells:
                        break
                    cells.append((nx, ny))
                    current_x, current_y = nx, ny
                if len(cells) != length:
                    continue
            elif shape == 'L':
                dirs = [(1,0), (-1,0), (0,1), (0,-1)]
                first_dir = random.choice(dirs)
                if first_dir[0] == 0:
                    second_dirs = [(1,0), (-1,0)]
                else:
                    second_dirs = [(0,1), (0,-1)]
                second_dir = random.choice(second_dirs)
                split = random.randint(1, length - 2)
                for _ in range(split):
                    nx = current_x + first_dir[0]
                    ny = current_y + first_dir[1]
                    if not (0 <= nx < self.width and 0 <= ny < self.height):
                        break
                    if self.obstacle_grid[nx][ny] or (nx, ny) in cells:
                        break
                    cells.append((nx, ny))
                    current_x, current_y = nx, ny
                if len(cells) != split + 1:
                    continue
                for _ in range(length - split - 1):
                    nx = current_x + second_dir[0]
                    ny = current_y + second_dir[1]
                    if not (0 <= nx < self.width and 0 <= ny < self.height):
                        break
                    if self.obstacle_grid[nx][ny] or (nx, ny) in cells:
                        break
                    cells.append((nx, ny))
                    current_x, current_y = nx, ny
                if len(cells) != length:
                    continue
            elif shape == 'zigzag':
                direction = random.choice([(1,0), (-1,0), (0,1), (0,-1)])
                remaining = length - 1
                while remaining > 0:
                    segment_len = 2 if remaining >= 2 else 1
                    for _ in range(segment_len):
                        if remaining <= 0:
                            break
                        nx = current_x + direction[0]
                        ny = current_y + direction[1]
                        if not (0 <= nx < self.width and 0 <= ny < self.height):
                            break
                        if self.obstacle_grid[nx][ny] or (nx, ny) in cells:
                            break
                        cells.append((nx, ny))
                        current_x, current_y = nx, ny
                        remaining -= 1
                    if len(cells) != length and remaining > 0:
                        if direction[0] != 0:
                            direction = random.choice([(0,1), (0,-1)])
                        else:
                            direction = random.choice([(1,0), (-1,0)])
                    if len(cells) != length:
                        break
                if len(cells) != length:
                    continue

            # Проверка, что новая стена не граничит с существующей стеной
            if self._wall_too_close(cells):
                continue  # попробовать заново

            # Временно занимаем клетки
            for cx, cy in cells:
                self.obstacle_grid[cx][cy] = True
                self.obstacle_type[cx][cy] = 'wall'

            if self._is_connected():
                self.wall_segments.append(cells)
                return True
            else:
                # Откат
                for cx, cy in cells:
                    self.obstacle_grid[cx][cy] = False
                    self.obstacle_type[cx][cy] = None
                continue
        return False

    def _wall_too_close(self, cells):
        """Проверяет, не граничит ли новая стена (cells) с существующей стеной."""
        for x, y in cells:
            for dx, dy in [(-1,0), (1,0), (0,-1), (0,1)]:
                nx, ny = x + dx, y + dy
                if 0 <= nx < self.width and 0 <= ny < self.height:
                    if self.obstacle_grid[nx][ny] and self.obstacle_type[nx][ny] == 'wall':
                        # Если соседняя клетка принадлежит другой стене (не в текущем списке cells)
                        if (nx, ny) not in cells:
                            return True
        return False

    def _count_obstacles(self):
        return sum(sum(row) for row in self.obstacle_grid)

    def _is_connected(self):
        start = (0, 0)
        if self.obstacle_grid[0][0]:
            return False
        visited = [[False] * self.height for _ in range(self.width)]
        queue = deque([start])
        visited[0][0] = True
        free_count = 0
        total_free = 0
        for x in range(self.width):
            for y in range(self.height):
                if not self.obstacle_grid[x][y]:
                    total_free += 1
        while queue:
            cx, cy = queue.popleft()
            free_count += 1
            for dx, dy in [(-1,0), (1,0), (0,-1), (0,1)]:
                nx, ny = cx + dx, cy + dy
                if 0 <= nx < self.width and 0 <= ny < self.height:
                    if not self.obstacle_grid[nx][ny] and not visited[nx][ny]:
                        visited[nx][ny] = True
                        queue.append((nx, ny))
        return free_count == total_free

    def get_neighbors(self, x, y):
        neighbors = []
        for dx, dy in [(-1,0), (1,0), (0,-1), (0,1)]:
            nx, ny = x + dx, y + dy
            if 0 <= nx < self.width and 0 <= ny < self.height:
                if not self.obstacle_grid[nx][ny]:
                    neighbors.append((nx, ny))
        return neighbors

    def find_path(self, start, goal):
        if start == goal:
            return []
        if self.obstacle_grid[goal[0]][goal[1]]:
            return []
        queue = deque()
        queue.append(start)
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