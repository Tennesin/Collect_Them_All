from game.game_config import GOLD_CELL_BOX_RADIUS, GOLD_CELL_BUFFER
from game.generation.gold_layout import plan_layout

class GoldCellGenerator:
    """Ставит золотые клетки в уголках стен. Где именно - решает gold_layout;
    здесь только построение коробов на поле."""

    def __init__(self, field, count):
        self.field = field
        self.count = count
        self.radius = GOLD_CELL_BOX_RADIUS
        self.buffer = GOLD_CELL_BUFFER

    def generate(self):
        centers = plan_layout(self.field.width, self.field.height, self.count, self.radius, self.buffer)
        for gx, gy in centers:
            self._build_box(gx, gy)
        if not self.field.is_connected():
            print("[GoldCellGenerator] Внимание: после постановки коробов поле несвязно.")
        return len(centers)

    def _build_box(self, gx, gy):
        field = self.field
        segments = self._corner_segments(gx, gy)
        for segment in segments:
            for cx, cy in segment:
                field.set_obstacle(cx, cy, True, 'wall')
        field.wall_segments.extend(segments)
        field.add_gold_cell(gx, gy)
        self._reserve_box(gx, gy)

    def _corner_segments(self, gx, gy):
        r = self.radius
        segments = []
        for sign_x, sign_y in [(-1, -1), (1, -1), (-1, 1), (1, 1)]:
            corner_x, corner_y = gx + sign_x * r, gy + sign_y * r
            arm_x = (gx + sign_x * (r - 1), corner_y)
            arm_y = (corner_x, gy + sign_y * (r - 1))
            segments.append([arm_x, (corner_x, corner_y), arm_y])
        return segments

    def _reserve_box(self, gx, gy):
        """Закрывает для препятствий, серебра и событий только площадку короба
        и по одной клетке у каждого из четырёх входов. Остальное кольцо вокруг свободно."""
        field = self.field
        r = self.radius
        for dx in range(-r, r + 1):
            for dy in range(-r, r + 1):
                field.reserve_cell(gx + dx, gy + dy)
        for dx, dy in ((r + 1, 0), (-r - 1, 0), (0, r + 1), (0, -r - 1)):
            if field.in_bounds(gx + dx, gy + dy):
                field.reserve_cell(gx + dx, gy + dy)