import pygame
import math
from settings import *


class Renderer:
    """Только отрисовка. Получает все зависимости явно, не лезет в Game."""

    def __init__(self, screen, camera, field, player, input_handler):
        self.screen = screen
        self.camera = camera
        self.field = field
        self.player = player
        self.input_handler = input_handler

    def draw(self):
        self.draw_field()
        self.draw_path()
        self.draw_preview()
        self.draw_player()

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

    def draw_path(self):
        if not self.player.moving or not self.player.path:
            return
        points = [(self.player.pos_x, self.player.pos_y)]
        points += [(cx + 0.5, cy + 0.5) for cx, cy in self.player.path]
        screen_points = [self.camera.project(x, y) for x, y in points]

        line_width = max(3, int(PATH_WIDTH_RATIO * self.camera.scale))
        circle_radius = max(4, int(PATH_GOAL_RADIUS_RATIO * self.camera.scale))

        if len(screen_points) >= 2:
            pygame.draw.lines(self.screen, PATH_COLOR, False, screen_points, line_width)
        goal_screen = screen_points[-1]
        pygame.draw.circle(self.screen, PATH_COLOR, (int(goal_screen[0]), int(goal_screen[1])), circle_radius)

    def draw_preview(self):
        preview_path = self.input_handler.preview_path
        if not preview_path or self.player.moving:
            return

        overlay = pygame.Surface((self.screen.get_width(), self.screen.get_height()), pygame.SRCALPHA)
        line_width = max(2, int(PREVIEW_WIDTH_RATIO * self.camera.scale))
        dash_length = max(6, int(PREVIEW_DASH_RATIO * self.camera.scale))
        gap_length = max(4, int(PREVIEW_GAP_RATIO * self.camera.scale))

        points = [(self.player.pos_x, self.player.pos_y)]
        points += [(cx + 0.5, cy + 0.5) for cx, cy in preview_path]
        screen_points = [self.camera.project(x, y) for x, y in points]

        for i in range(len(screen_points) - 1):
            self._draw_dashed_line(
                overlay, PREVIEW_COLOR,
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

    def draw_player(self):
        screen_pos = self.camera.project(self.player.pos_x, self.player.pos_y)
        radius = max(3, int(PLAYER_RADIUS_RATIO * self.camera.scale))
        pygame.draw.circle(self.screen, PLAYER_COLOR, (int(screen_pos[0]), int(screen_pos[1])), radius)