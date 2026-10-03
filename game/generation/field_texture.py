import random

class FieldTextureGenerator:
    """Назначает каждой клетке один из базовых оттенков (индекс 0..variant_count-1)."""

    def __init__(self, field, variant_count):
        self.field = field
        self.variant_count = variant_count

    def generate(self):
        field = self.field
        for y in range(field.height):
            for x in range(field.width):
                if not self._needs_color(x, y):
                    continue
                field.color_variants[x][y] = self._pick_base_color(x, y)

    def _pick_base_color(self, x, y):
        forbidden = self._forbidden_neighbor_colors(x, y)
        choices = [v for v in range(self.variant_count) if v not in forbidden]
        return random.choice(choices) if choices else random.randrange(self.variant_count)

    def _needs_color(self, x, y):
        field = self.field
        if field.obstacle_grid[x][y]:
            return False
        if (x, y) == field.win_cell:
            return False
        if (x, y) in field.gold_cell_positions:
            return False
        return True

    def _forbidden_neighbor_colors(self, x, y):
        field = self.field
        forbidden = set()
        for dx, dy in [(-1, -1), (0, -1), (1, -1), (-1, 0)]:
            nx, ny = x + dx, y + dy
            if field.in_bounds(nx, ny):
                value = field.color_variants[nx][ny]
                if value is not None:
                    forbidden.add(value)
        return forbidden