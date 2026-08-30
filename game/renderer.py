import pygame
import math
from settings import *
from game.image_manager import ImageManager

class Renderer:
    """Только отрисовка игрового поля и фигур на нём. Правая панель интерфейса
    рисуется отдельно (см. game.ui.PlayerPanel) — Renderer про неё не знает."""

    def __init__(self, screen, camera, field, players, turn_manager, input_handler, resource_manager):
        self.screen = screen
        self.camera = camera
        self.field = field
        self.players = players
        self.turn_manager = turn_manager
        self.input_handler = input_handler
        self.resource_manager = resource_manager

    def draw(self):
        self.draw_field()
        self.draw_resources()
        self.draw_path()
        self.draw_preview()
        self.draw_players()

    def draw_field(self):
        self.screen.fill(BG_COLOR)
        hovered_cell = self.input_handler.get_hovered_cell()

        for x in range(self.field.width):
            for y in range(self.field.height):
                p1 = self.camera.project(x, y)
                p2 = self.camera.project(x + 1, y)
                p3 = self.camera.project(x + 1, y + 1)
                p4 = self.camera.project(x, y + 1)
                points = [p1, p2, p3, p4]

                if self.field.obstacle_grid[x][y] and self.field.obstacle_type[x][y] == 'block':
                    pygame.draw.polygon(self.screen, BLOCK_COLOR, points)
                    pygame.draw.polygon(self.screen, OBSTACLE_BORDER, points, 2)
                elif (x, y) == self.field.win_cell:
                    pygame.draw.polygon(self.screen, WIN_CELL_COLOR, points)
                    pygame.draw.polygon(self.screen, WIN_CELL_BORDER_COLOR, points, 4)
                    pygame.draw.polygon(self.screen, WIN_CELL_BORDER_COLOR_SECONDARY, points, 2)
                elif (x, y) in self.field.gold_cell_positions:
                    pygame.draw.polygon(self.screen, GOLD_CELL_COLOR, points)
                    pygame.draw.polygon(self.screen, GOLD_CELL_BORDER_COLOR, points, 3)
                else:
                    color = HOVER_COLOR if hovered_cell == (x, y) else FIELD_COLOR
                    pygame.draw.polygon(self.screen, color, points)
                    pygame.draw.polygon(self.screen, GRID_COLOR, points, 1)

        self.draw_walls()

    def draw_walls(self):
        if not self.field.wall_segments:
            return
        wall_thickness = max(2.0, WALL_THICKNESS_RATIO * self.camera.scale)
        color = WALL_COLOR

        for segment in self.field.wall_segments:
            if len(segment) < 2:
                continue
            screen_points = [self.camera.project(cx + 0.5, cy + 0.5) for cx, cy in segment]

            pygame.draw.lines(self.screen, color, False, screen_points, int(wall_thickness))
            for pt in screen_points:
                rect = pygame.Rect(0, 0, wall_thickness, wall_thickness)
                rect.center = pt
                pygame.draw.rect(self.screen, color, rect)

        for segment in self.field.wall_segments:
            for x, y in segment:
                for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    nx, ny = x + dx, y + dy
                    if (self.field.in_bounds(nx, ny)
                            and self.field.obstacle_grid[nx][ny]
                            and self.field.obstacle_type[nx][ny] == 'block'):
                        screen1 = self.camera.project(x + 0.5, y + 0.5)
                        screen2 = self.camera.project(nx + 0.5, ny + 0.5)
                        screen_mid = ((screen1[0] + screen2[0]) / 2, (screen1[1] + screen2[1]) / 2)
                        pygame.draw.line(self.screen, color, screen1, screen_mid, int(wall_thickness))

    def draw_resources(self):
        """Иконки золотых клеток (постоянные) и текущих кучек серебра
        (появляются/исчезают по циклам — актуальный список берём у ResourceManager)."""
        icon_size = max(4, int(FIELD_ICON_RATIO * self.camera.scale))
        for pos in self.field.gold_cell_positions:
            has_gold = self.resource_manager.gold_deposits.get(pos, 0) > 0
            alpha = 255 if has_gold else GOLD_ICON_DIM_ALPHA
            self._draw_field_icon(ICON_GOLD, pos[0], pos[1], icon_size, alpha=alpha)
        for sx, sy in self.resource_manager.silver_cells:
            self._draw_field_icon(ICON_SILVER_FIELD, sx, sy, icon_size)

    def _draw_field_icon(self, image_name, cell_x, cell_y, size, alpha=255):
        icon = ImageManager.get_scaled(image_name, (size, size), alpha=alpha)
        screen_pos = self.camera.project(cell_x + 0.5, cell_y + 0.5)
        rect = icon.get_rect(center=(int(screen_pos[0]), int(screen_pos[1])))
        self.screen.blit(icon, rect)

    def draw_path(self):
        """Линия и точка цели текущего маршрута — цветом того игрока, который сейчас идёт."""
        player = self.turn_manager.current_player
        if not player.moving or not player.path:
            return
        points = [(player.pos_x, player.pos_y)]
        points += [(cx + 0.5, cy + 0.5) for cx, cy in player.path]
        screen_points = [self.camera.project(x, y) for x, y in points]

        line_width = max(3, int(PATH_WIDTH_RATIO * self.camera.scale))
        circle_radius = max(4, int(PATH_GOAL_RADIUS_RATIO * self.camera.scale))
        color = player.color

        if len(screen_points) >= 2:
            pygame.draw.lines(self.screen, color, False, screen_points, line_width)
        goal_screen = screen_points[-1]
        pygame.draw.circle(self.screen, color, (int(goal_screen[0]), int(goal_screen[1])), circle_radius)

    def draw_preview(self):
        """Пунктирный предпросмотр ещё не подтверждённого пути — тоже цветом текущего игрока."""
        preview_path = self.input_handler.preview_path
        player = self.turn_manager.current_player
        if not preview_path or player.moving:
            return

        overlay = pygame.Surface((self.screen.get_width(), self.screen.get_height()), pygame.SRCALPHA)
        line_width = max(2, int(PREVIEW_WIDTH_RATIO * self.camera.scale))
        dash_length = max(6, int(PREVIEW_DASH_RATIO * self.camera.scale))
        gap_length = max(4, int(PREVIEW_GAP_RATIO * self.camera.scale))
        preview_color = (*player.color, PREVIEW_ALPHA)

        points = [(player.pos_x, player.pos_y)]
        points += [(cx + 0.5, cy + 0.5) for cx, cy in preview_path]
        screen_points = [self.camera.project(x, y) for x, y in points]

        for i in range(len(screen_points) - 1):
            self._draw_dashed_line(
                overlay, preview_color,
                screen_points[i], screen_points[i + 1],
                dash_length, gap_length, line_width
            )
        self.screen.blit(overlay, (0, 0))

    def _draw_dashed_line(self, surface, color, start, end, dash_length, gap_length, width):
        x1, y1 = start
        x2, y2 = end
        dx = x2 - x1
        dy = y2 - y1
        distance = math.hypot(dx, dy)
        if distance == 0:
            return
        dx /= distance
        dy /= distance
        current = 0
        while current < distance:
            segment_end = min(current + dash_length, distance)
            sx = x1 + dx * current
            sy = y1 + dy * current
            ex = x1 + dx * segment_end
            ey = y1 + dy * segment_end
            pygame.draw.line(surface, color, (sx, sy), (ex, ey), width)
            current += dash_length + gap_length

    # --- Игроки ---

    def draw_players(self):
        current = self.turn_manager.current_player
        moving_player = current if current.moving else None
        stationary = [p for p in self.players if p is not moving_player]

        groups = {}
        for p in stationary:
            cell = (p.grid_x, p.grid_y)
            groups.setdefault(cell, []).append(p)

        for group in groups.values():
            self._draw_stack(group, current)

        if moving_player:
            radius = max(3, int(PLAYER_RADIUS_RATIO * self.camera.scale))
            screen_pos = self.camera.project(moving_player.pos_x, moving_player.pos_y)
            self._draw_circle(moving_player.color, screen_pos, radius, highlight=True)

    def _draw_stack(self, group, current):
        """Рисует игроков одной клетки "слоями", расходящимися по диагонали
        в обе стороны от центра (чётные слои — ниже-правее, нечётные — выше-левее),
        чтобы стопка не упиралась в один угол клетки. Тот, чей сейчас ход,
        всегда рисуется без смещения и поверх всех остальных."""
        radius = max(3, int(PLAYER_RADIUS_RATIO * self.camera.scale))
        step = STACK_OFFSET_RATIO * radius

        others = [p for p in group if p is not current]
        ordered = others + ([current] if current in group else [])
        n = len(ordered)

        grid_x, grid_y = ordered[0].grid_x, ordered[0].grid_y
        base_x, base_y = self.camera.project(grid_x + 0.5, grid_y + 0.5)

        for i, p in enumerate(ordered):
            back_index = n - 1 - i  # 0 у переднего (последнего в списке) слоя
            offset_x, offset_y = self._stack_offset(back_index, step)
            screen_pos = (base_x + offset_x, base_y + offset_y)

            is_current = p is current
            color = p.color if is_current else self._dim_color(p.color)
            self._draw_circle(color, screen_pos, radius, highlight=is_current)

    @staticmethod
    def _stack_offset(back_index, step):
        """back_index=0 — без смещения (передний слой). Дальше слои поочерёдно
        уходят по диагонали то влево-вверх, то вправо-вниз, с шагом,
        растущим через каждые два слоя — так место клетки расходуется экономнее."""
        if back_index == 0:
            return 0.0, 0.0
        magnitude = ((back_index + 1) // 2) * step
        direction = -1 if back_index % 2 == 1 else 1
        return direction * magnitude, direction * magnitude

    def _draw_circle(self, color, screen_pos, radius, highlight=False):
        center = (int(screen_pos[0]), int(screen_pos[1]))
        pygame.draw.circle(self.screen, color, center, radius)
        border_color = (255, 255, 255) if highlight else (20, 20, 20)
        border_width = 2 if highlight else 1
        pygame.draw.circle(self.screen, border_color, center, radius, border_width)

    @staticmethod
    def _dim_color(color):
        return tuple(max(0, int(c * PLAYER_DIM_FACTOR)) for c in color)