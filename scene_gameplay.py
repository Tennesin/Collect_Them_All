import pygame
from settings import *
from camera import Camera
from field import Field
from obstacle_generator import ObstacleGenerator
from player import Player
from input_handler import InputHandler
from renderer import Renderer
from scenes import Scene

class GameplayScene(Scene):
    """Сборка и цикл собственно игры на поле. Раньше это был класс Game.
    settings.player_count пока используется только как число — реальных
    дополнительных игроков/ботов не создаём, это заглушка на будущее."""

    def __init__(self, manager, settings):
        super().__init__(manager)
        self.settings = settings
        screen = self.manager.app.screen

        self.field = Field(settings.map_width, settings.map_height)
        total_cells = settings.map_width * settings.map_height
        max_obstacle_cells = int(total_cells * settings.obstacle_fraction)
        ObstacleGenerator(self.field, max_obstacle_cells).generate()

        self.camera = Camera(SCREEN_WIDTH, SCREEN_HEIGHT, settings.map_width, settings.map_height,
                              INITIAL_SCALE, MAX_SCALE)

        self.player = Player(self.field, start_cell=(0, 0), speed=PLAYER_SPEED)
        self.player.on_move = self.camera.center_on

        self.input_handler = InputHandler(self.camera, self.field, self.player)
        self.renderer = Renderer(screen, self.camera, self.field, self.player, self.input_handler)

        self.camera.center_on(self.player.pos_x, self.player.pos_y)

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            from scene_pause import PauseScene
            self.manager.push(PauseScene(self.manager, self))
            return
        self.input_handler.handle_event(event)

    def update(self, dt):
        self.input_handler.process_held_keys()
        if self.player.moving:
            self.player.update(dt)

    def draw(self, screen):
        self.renderer.draw()