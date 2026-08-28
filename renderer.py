import pygame
import math
from settings import *

class Renderer:
    def __init__(self, game):
        self.game = game

    def project(self, x, y, z=0):
        g = self.game
        screen_x = x * g.scale + g.offset_x + g.center_x
        screen_y = y * g.scale + g.offset_y + g.center_y
        return screen_x, screen_y

    def screen_to_world(self, screen_x, screen_y):
        g = self.game
        world_x = (screen_x - g.offset_x - g.center_x) / g.scale
        world_y = (screen_y - g.offset_y - g.center_y) / g.scale
        return world_x, world_y

    def draw_field(self):
        g = self.game
        g.screen.fill(BG_COLOR)

        hovered_cell = None
        if not g.player.moving and g.mouse_pos:
            world = self.screen_to_world(*g.mouse_pos)
            if world:
                wx, wy = world
                if 0 <= wx < g.field_width and 0 <= wy < g.field_height:
                    cell = (int(wx), int(wy))
                    if not g.field.obstacle_grid[cell[0]][cell[1]]:
                        hovered_cell = cell

        for x in range(g.field_width):
            for y in range(g.field_height):
                p1 = self.project(x, y)
                p2 = self.project(x + 1, y)
                p3 = self.project(x + 1, y + 1)
                p4 = self.project(x, y + 1)
                points = [p1, p2, p3, p4]

                if g.field.obstacle_grid[x][y] and g.field.obstacle_type[x][y] == 'block':
                    color = BLOCK_COLOR
                    pygame.draw.polygon(g.screen, color, points)
                    pygame.draw.polygon(g.screen, OBSTACLE_BORDER, points, 2)
                else:
                    if hovered_cell == (x, y):
                        color = HOVER_COLOR
                    else:
                        color = FIELD_COLOR
                    pygame.draw.polygon(g.screen, color, points)
                    pygame.draw.polygon(g.screen, GRID_COLOR, points, 1)

        self.draw_walls()

    def draw_walls(self):
        g = self.game
        if not g.field.wall_segments:
            return
        # Для высокой точности не приводим к int при вычислении толщины
        wall_thickness = max(2.0, 0.35 * g.scale)
        color = WALL_COLOR

        for segment in g.field.wall_segments:
            if len(segment) < 2:
                continue
            screen_points = []
            for cell in segment:
                cx = cell[0] + 0.5
                cy = cell[1] + 0.5
                screen_points.append(self.project(cx, cy))

            # 1. Рисуем саму линию
            pygame.draw.lines(g.screen, color, False, screen_points, int(wall_thickness))

            # 2. Перекрываем узлы с помощью FRect (плавающая точка гарантирует точное попадание в центр)
            for pt in screen_points:
                rect = pygame.Rect(0, 0, wall_thickness, wall_thickness)
                rect.center = pt
                pygame.draw.rect(g.screen, color, rect)

        # 3. Соединительные полоски к соседним блокам
        for segment in g.field.wall_segments:
            for cell in segment:
                x, y = cell
                for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < g.field_width and 0 <= ny < g.field_height:
                        if g.field.obstacle_grid[nx][ny] and g.field.obstacle_type[nx][ny] == 'block':
                            cx1, cy1 = x + 0.5, y + 0.5
                            cx2, ny_val = nx + 0.5, ny + 0.5
                            screen1 = self.project(cx1, cy1)
                            screen2 = self.project(cx2, ny_val)
                            screen_mid = ((screen1[0] + screen2[0]) / 2, (screen1[1] + screen2[1]) / 2)
                            pygame.draw.line(g.screen, color, screen1, screen_mid, int(wall_thickness))

    def draw_path(self):
        g = self.game
        if not g.player.moving or not g.player.path:
            return
        points = [(g.player.pos_x, g.player.pos_y)]
        for cell in g.player.path:
            cx = cell[0] + 0.5
            cy = cell[1] + 0.5
            points.append((cx, cy))
        screen_points = [self.project(x, y) for x, y in points]
        line_width = max(3, int(0.25 * g.scale))
        circle_radius = max(4, int(0.3 * g.scale))
        if len(screen_points) >= 2:
            pygame.draw.lines(g.screen, PATH_COLOR, False, screen_points, line_width)
        goal_screen = screen_points[-1]
        pygame.draw.circle(g.screen, PATH_COLOR, (int(goal_screen[0]), int(goal_screen[1])), circle_radius)

    def draw_preview(self):
        g = self.game
        if not g.preview_path or g.player.moving:
            return
        overlay = pygame.Surface((g.width, g.height), pygame.SRCALPHA)
        color = (255, 80, 80, 150)
        line_width = max(2, int(0.2 * g.scale))
        dash_length = max(6, int(0.2 * g.scale))
        gap_length = max(4, int(0.1 * g.scale))
        points = [(g.player.pos_x, g.player.pos_y)]
        for cell in g.preview_path:
            cx = cell[0] + 0.5
            cy = cell[1] + 0.5
            points.append((cx, cy))
        screen_points = [self.project(x, y) for x, y in points]
        for i in range(len(screen_points) - 1):
            self._draw_dashed_line(
                overlay,
                color,
                screen_points[i],
                screen_points[i+1],
                dash_length,
                gap_length,
                line_width
            )
        g.screen.blit(overlay, (0, 0))

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
        g = self.game
        screen_pos = self.project(g.player.pos_x, g.player.pos_y)
        radius = max(3, int(0.3 * g.scale))
        pygame.draw.circle(g.screen, PLAYER_COLOR, (int(screen_pos[0]), int(screen_pos[1])), radius)