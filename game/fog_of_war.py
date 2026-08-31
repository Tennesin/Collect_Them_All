class FogOfWar:

    def __init__(self, field, radius):
        self.field = field
        self.radius = radius
        self.radius_sq = radius * radius
        self._gold_aura = self._build_gold_aura()
        self._win_aura = self._build_win_aura()

    def update_player(self, player):
        visible = self.compute_visible(player.grid_x, player.grid_y)
        player.visible_cells = visible
        player.explored_cells |= visible

    def compute_visible(self, origin_x, origin_y):
        field = self.field
        visible = set(self._gold_aura)
        visible |= self._win_aura
        visible.add((origin_x, origin_y))

        min_x = max(0, origin_x - self.radius)
        max_x = min(field.width - 1, origin_x + self.radius)
        min_y = max(0, origin_y - self.radius)
        max_y = min(field.height - 1, origin_y + self.radius)

        for x in range(min_x, max_x + 1):
            for y in range(min_y, max_y + 1):
                dx = x - origin_x
                dy = y - origin_y
                if dx * dx + dy * dy > self.radius_sq:
                    continue
                if self._has_line_of_sight(origin_x, origin_y, x, y):
                    visible.add((x, y))

        return visible

    def _build_win_aura(self):
        field = self.field
        wx, wy = field.win_cell
        aura = {(wx, wy)}
        for dx, dy in [(-1, -1), (0, -1), (1, -1),
                       (-1, 0),           (1, 0),
                       (-1, 1),  (0, 1),  (1, 1)]:
            nx, ny = wx + dx, wy + dy
            if field.in_bounds(nx, ny):
                aura.add((nx, ny))
        return aura

    # --- Внутреннее ---

    def _build_gold_aura(self):
        field = self.field
        aura = set()
        for gx, gy in field.gold_cell_positions:
            aura.add((gx, gy))
            for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nx, ny = gx + dx, gy + dy
                if field.in_bounds(nx, ny):
                    aura.add((nx, ny))
        return aura

    def _has_line_of_sight(self, x0, y0, x1, y1):
        field = self.field
        for cx, cy in self._bresenham_cells(x0, y0, x1, y1):
            if field.obstacle_type[cx][cy] == 'block':
                return False
        return True

    @staticmethod
    def _bresenham_cells(x0, y0, x1, y1):
        cells = []
        dx = abs(x1 - x0)
        dy = -abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx + dy
        x, y = x0, y0
        while (x, y) != (x1, y1):
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x += sx
            if e2 <= dx:
                err += dx
                y += sy
            if (x, y) != (x1, y1):
                cells.append((x, y))
        return cells