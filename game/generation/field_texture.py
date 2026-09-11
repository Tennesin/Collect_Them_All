import random
from settings import FIELD_COLOR_VARIANTS, FIELD_TEXTURE_COLOR_VARIANTS

# Каждый вариант — список маленьких прямоугольников в относительных координатах
# клетки (0.0-1.0 по x и y от левого верхнего угла клетки). Формат: (rel_x, rel_y, rel_w, rel_h).
CELL_TEXTURE_VARIANTS = [
    [(0.14, 0.16, 0.20, 0.18)],                                   # 0: пятно сверху-слева
    [(0.64, 0.14, 0.20, 0.20)],                                   # 1: пятно сверху-справа
    [(0.16, 0.62, 0.20, 0.18)],                                   # 2: пятно снизу-слева
    [(0.62, 0.60, 0.20, 0.20)],                                   # 3: пятно снизу-справа
    [(0.16, 0.16, 0.18, 0.16), (0.62, 0.62, 0.20, 0.18)],         # 4: два пятна по диагонали (\)
    [(0.64, 0.14, 0.18, 0.16), (0.14, 0.64, 0.20, 0.18)],         # 5: два пятна по диагонали (/)
    [(0.12, 0.40, 0.14, 0.14), (0.46, 0.16, 0.14, 0.14),
     (0.68, 0.56, 0.16, 0.16)],                                   # 6: три мелких пятна вразброс
    [(0.38, 0.38, 0.24, 0.22)],                                   # 7: одно пятно ближе к центру
    [(0.28, 0.40, 0.16, 0.16), (0.52, 0.42, 0.16, 0.16)],         # 8: два пятна рядом по центру
    [(0.40, 0.40, 0.20, 0.18), (0.12, 0.12, 0.12, 0.12)],         # 9: центр + мелкое пятно в углу
    [(0.16, 0.68, 0.18, 0.14), (0.60, 0.68, 0.18, 0.14)],         # 10: два пятна снизу по краям
    [(0.34, 0.34, 0.28, 0.26)],                                   # 11: одно крупное мягкое пятно
]

class FieldTextureGenerator:

    def __init__(self, field):
        self.field = field
        self.variant_count = len(CELL_TEXTURE_VARIANTS)

    def generate(self):
        field = self.field
        for y in range(field.height):
            for x in range(field.width):
                if not self._needs_texture(x, y):
                    continue

                field.color_variants[x][y] = self._pick_base_color(x, y)

                forbidden = self._forbidden_neighbor_values(field.texture_variants, x, y)
                choices = [v for v in range(self.variant_count) if v not in forbidden]
                variant = random.choice(choices) if choices else random.randrange(self.variant_count)
                field.texture_variants[x][y] = variant

                shapes = CELL_TEXTURE_VARIANTS[variant]
                field.texture_colors[x][y] = [
                    random.choice(FIELD_TEXTURE_COLOR_VARIANTS) for _ in shapes
                ]

    def _pick_base_color(self, x, y):
        forbidden = self._forbidden_neighbor_values(self.field.color_variants, x, y)
        choices = [v for v in range(len(FIELD_COLOR_VARIANTS)) if v not in forbidden]
        return random.choice(choices) if choices else random.randrange(len(FIELD_COLOR_VARIANTS))

    def _needs_texture(self, x, y):
        field = self.field
        if field.obstacle_grid[x][y]:
            return False
        if (x, y) == field.win_cell:
            return False
        if (x, y) in field.gold_cell_positions:
            return False
        return True

    def _forbidden_neighbor_values(self, grid, x, y):
        """Универсальная версия старого _already_assigned_neighbor_variants —
        работает с любым гридом (форма текстуры или базовый цвет клетки)."""
        field = self.field
        forbidden = set()
        for dx, dy in [(-1, -1), (0, -1), (1, -1), (-1, 0)]:
            nx, ny = x + dx, y + dy
            if field.in_bounds(nx, ny):
                value = grid[nx][ny]
                if value is not None:
                    forbidden.add(value)
        return forbidden