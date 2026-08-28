import pygame
import sys
from settings import *
from renderer import Renderer
from player import Player
from objects import Field

class Game:
    def __init__(self):
        pygame.init()
        self.width = SCREEN_WIDTH
        self.height = SCREEN_HEIGHT
        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption("Плоское поле с препятствиями")
        self.clock = pygame.time.Clock()
        self.running = True

        # Камера
        self.scale = INITIAL_SCALE
        self.max_scale = MAX_SCALE
        self.center_x = self.width // 2
        self.center_y = self.height // 2
        self.offset_x = 0
        self.offset_y = 0

        # Перетаскивание
        self.dragging = False
        self.last_mouse_pos = (0, 0)
        self.mouse_pos = (0, 0)

        # Поле
        self.field_width = FIELD_WIDTH
        self.field_height = FIELD_HEIGHT
        self.total_cells = self.field_width * self.field_height
        self.max_obstacle_cells = int(self.total_cells * MAX_OBSTACLE_PERCENT)

        # Объекты
        self.field = Field(self.field_width, self.field_height, self.max_obstacle_cells)
        self.renderer = Renderer(self)
        self.player = Player(self)

        # Предпросмотр пути
        self.preview_path = None
        self.preview_goal = None

        self.center_on_player()
        self.min_scale = max(self.width / self.field_width, self.height / self.field_height)

    def project(self, x, y, z=0):
        return self.renderer.project(x, y, z)

    def screen_to_world(self, screen_x, screen_y):
        return self.renderer.screen_to_world(screen_x, screen_y)

    def clamp_offset(self):
        min_offset_x = self.center_x - self.field_width * self.scale
        max_offset_x = -self.center_x
        min_offset_y = self.center_y - self.field_height * self.scale
        max_offset_y = -self.center_y
        self.offset_x = max(min_offset_x, min(max_offset_x, self.offset_x))
        self.offset_y = max(min_offset_y, min(max_offset_y, self.offset_y))

    def zoom(self, factor):
        new_scale = self.scale * factor
        self.min_scale = max(self.width / self.field_width, self.height / self.field_height)
        new_scale = max(self.min_scale, min(self.max_scale, new_scale))
        if new_scale == self.scale:
            return
        ratio = new_scale / self.scale
        self.offset_x *= ratio
        self.offset_y *= ratio
        self.scale = new_scale
        self.clamp_offset()

    def center_on_player(self):
        px, py = self.player.pos_x, self.player.pos_y
        self.offset_x = -px * self.scale
        self.offset_y = -py * self.scale
        self.clamp_offset()

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 3:
                    self.dragging = True
                    self.last_mouse_pos = event.pos
                elif event.button == 1:
                    if not self.player.moving and self.mouse_pos is not None:
                        world = self.screen_to_world(*self.mouse_pos)
                        if world:
                            wx, wy = world
                            if 0 <= wx < self.field_width and 0 <= wy < self.field_height:
                                goal_cell = (int(wx), int(wy))
                                if not self.field.obstacle_grid[goal_cell[0]][goal_cell[1]]:
                                    # Клик по свободной клетке
                                    if goal_cell != (self.player.grid_x, self.player.grid_y):
                                        if self.preview_goal == goal_cell:
                                            # Повторный клик: начинаем движение
                                            self.player.set_goal(goal_cell)
                                            self.preview_path = None
                                            self.preview_goal = None
                                        else:
                                            # Новый предпросмотр
                                            path = self.field.find_path((self.player.grid_x, self.player.grid_y), goal_cell)
                                            if path:
                                                self.preview_path = path
                                                self.preview_goal = goal_cell
                                            else:
                                                self.preview_path = None
                                                self.preview_goal = None
            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 3:
                    self.dragging = False
            elif event.type == pygame.MOUSEMOTION:
                self.mouse_pos = event.pos
                if self.dragging and not self.player.moving:
                    dx = event.pos[0] - self.last_mouse_pos[0]
                    dy = event.pos[1] - self.last_mouse_pos[1]
                    self.offset_x += dx
                    self.offset_y += dy
                    self.clamp_offset()
                    self.last_mouse_pos = event.pos
            elif event.type == pygame.MOUSEWHEEL:
                if event.y > 0:
                    self.zoom(1.1)
                elif event.y < 0:
                    self.zoom(0.9)

    def handle_zoom_keys(self):
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]:
            if keys[pygame.K_UP]:
                self.zoom(1.02)
            if keys[pygame.K_DOWN]:
                self.zoom(0.98)

    def update(self, dt):
        if self.player.moving:
            self.player.update(dt)
            self.center_on_player()

    def draw(self):
        self.renderer.draw_field()
        self.renderer.draw_path()
        self.renderer.draw_preview()
        self.renderer.draw_player()

    def run(self):
        while self.running:
            dt = self.clock.tick(FPS) / 1000.0
            self.handle_events()
            self.handle_zoom_keys()
            self.update(dt)
            self.draw()
            pygame.display.flip()
        pygame.quit()
        sys.exit()