class FogOfWar:

    def __init__(self, field, radius):
        self.field = field
        self.radius = radius
        self._gold_aura = self._build_gold_aura()
        self._win_aura = self._build_win_aura()
        self._full_map_cache = None
        self._block_grid = [
            [field.obstacle_type[x][y] == 'block' for y in range(field.height)]
            for x in range(field.width)
        ]

    def update_player(self, player):
        radius = self._effective_radius(player)
        visible = self.compute_visible(player.grid_x, player.grid_y, radius=radius)
        player.explored_cells |= visible
        if self._has_full_map_vision(player):
            player.visible_cells = self._full_map_cells()
            player.known_cells = player.visible_cells
        else:
            player.visible_cells = visible
            player.known_cells = player.explored_cells

    def compute_visible(self, origin_x, origin_y, radius=None):
        field = self.field
        radius = self.radius if radius is None else radius
        radius_sq = radius * radius

        visible = set(self._gold_aura)
        visible |= self._win_aura
        visible.add((origin_x, origin_y))

        min_x = max(0, origin_x - radius)
        max_x = min(field.width - 1, origin_x + radius)
        min_y = max(0, origin_y - radius)
        max_y = min(field.height - 1, origin_y + radius)

        for x in range(min_x, max_x + 1):
            for y in range(min_y, max_y + 1):
                dx = x - origin_x
                dy = y - origin_y
                if dx * dx + dy * dy > radius_sq:
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

    @staticmethod
    def _has_full_map_vision(player):
        return any(getattr(effect, "full_map_vision", False) for effect in player.active_effects)

    def _effective_radius(self, player):
        overrides = [
            effect.vision_radius_override for effect in player.active_effects
            if getattr(effect, "vision_radius_override", None) is not None
        ]
        return min(self.radius, *overrides) if overrides else self.radius

    def _full_map_cells(self):
        if self._full_map_cache is None:
            field = self.field
            self._full_map_cache = frozenset(
                (x, y) for x in range(field.width) for y in range(field.height)
            )
        return self._full_map_cache

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
        """Брезенхэм без списка: проверяет клетки строго между началом и концом,
        останавливается на первом блоке."""
        if x0 == x1 and y0 == y1:
            return True
        blocks = self._block_grid
        dx = abs(x1 - x0)
        dy = -abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx + dy
        x, y = x0, y0
        while True:
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x += sx
            if e2 <= dx:
                err += dx
                y += sy
            if x == x1 and y == y1:
                return True
            if blocks[x][y]:
                return False