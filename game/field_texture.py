import random

# Каждый вариант — список маленьких прямоугольников в относительных координатах
# клетки (0.0-1.0 по x и y от левого верхнего угла клетки). Формат: (rel_x, rel_y, rel_w, rel_h).
CELL_TEXTURE_VARIANTS = [
    [(0.12, 0.15, 0.22, 0.18)],                                   # 0: пятно сверху-слева
    [(0.66, 0.14, 0.20, 0.20)],                                   # 1: пятно сверху-справа
    [(0.14, 0.62, 0.30, 0.16)],                                   # 2: горизонтальная полоска снизу-слева
    [(0.60, 0.55, 0.16, 0.32)],                                   # 3: вертикальная полоска справа
    [(0.16, 0.16, 0.18, 0.18), (0.62, 0.62, 0.20, 0.18)],         # 4: два пятна по диагонали (\)
    [(0.64, 0.14, 0.18, 0.18), (0.14, 0.64, 0.20, 0.18)],         # 5: два пятна по диагонали (/)
    [(0.10, 0.40, 0.14, 0.14), (0.45, 0.15, 0.14, 0.14),
     (0.70, 0.55, 0.16, 0.16)],                                   # 6: три мелких пятна вразброс
    [(0.20, 0.44, 0.60, 0.12)],                                   # 7: горизонтальная полоса по центру
    [(0.44, 0.18, 0.12, 0.62)],                                   # 8: вертикальная полоса по центру
    [(0.40, 0.40, 0.20, 0.20), (0.10, 0.10, 0.12, 0.12)],         # 9: центр + мелкое пятно в углу
    [(0.15, 0.70, 0.18, 0.14), (0.62, 0.70, 0.18, 0.14)],         # 10: два пятна снизу по краям
    [(0.36, 0.36, 0.28, 0.28)],                                   # 11: одно крупное пятно в центре
]


class FieldTextureGenerator:
    """Расставляет псевдо-текстуры по 'обычным' клеткам поля так, чтобы одна и та же
    вариация никогда не встречалась у двух соседних клеток (включая диагонали)."""

    def __init__(self, field):
        self.field = field
        self.variant_count = len(CELL_TEXTURE_VARIANTS)

    def generate(self):
        field = self.field
        # Построчно, сверху вниз, слева направо — важно для корректной проверки соседей.
        for y in range(field.height):
            for x in range(field.width):
                if not self._needs_texture(x, y):
                    continue
                forbidden = self._already_assigned_neighbor_variants(x, y)
                choices = [v for v in range(self.variant_count) if v not in forbidden]
                variant = random.choice(choices) if choices else random.randrange(self.variant_count)
                field.texture_variants[x][y] = variant

    def _needs_texture(self, x, y):
        field = self.field
        if field.obstacle_grid[x][y]:
            return False
        if (x, y) == field.win_cell:
            return False
        if (x, y) in field.gold_cell_positions:
            return False
        return True

    def _already_assigned_neighbor_variants(self, x, y):
        """Проверяем только те 4 соседних направления, которые уже обработаны раньше
        в построчном обходе (верх-лево, верх, верх-право, лево). Остальные 4 соседа
        проверят себя сами, когда дойдёт их очередь — тем самым покрываются все 8 направлений."""
        field = self.field
        forbidden = set()
        for dx, dy in [(-1, -1), (0, -1), (1, -1), (-1, 0)]:
            nx, ny = x + dx, y + dy
            if field.in_bounds(nx, ny):
                variant = field.texture_variants[nx][ny]
                if variant is not None:
                    forbidden.add(variant)
        return forbidden