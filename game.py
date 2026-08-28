import pygame
import sys
from settings import *
from camera import Camera
from field import Field
from obstacle_generator import ObstacleGenerator
from player import Player
from input_handler import InputHandler
from renderer import Renderer


class Game:
    """Composition root: собирает все части вместе и крутит игровой цикл.
    Никакой игровой логики здесь больше нет."""

    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Плоское поле с препятствиями")
        self.clock = pygame.time.Clock()

        self.field = Field(FIELD_WIDTH, FIELD_HEIGHT)
        total_cells = FIELD_WIDTH * FIELD_HEIGHT
        max_obstacle_cells = int(total_cells * MAX_OBSTACLE_PERCENT)
        ObstacleGenerator(self.field, max_obstacle_cells).generate()

        self.camera = Camera(SCREEN_WIDTH, SCREEN_HEIGHT, FIELD_WIDTH, FIELD_HEIGHT,
                              INITIAL_SCALE, MAX_SCALE)

        self.player = Player(self.field, start_cell=(0, 0), speed=PLAYER_SPEED)
        self.player.on_move = self.camera.center_on  # камера следит за игроком

        self.input_handler = InputHandler(self.camera, self.field, self.player)
        self.renderer = Renderer(self.screen, self.camera, self.field, self.player, self.input_handler)

        self.camera.center_on(self.player.pos_x, self.player.pos_y)

    def update(self, dt):
        if self.player.moving:
            self.player.update(dt)

    def run(self):
        while self.input_handler.running:
            dt = self.clock.tick(FPS) / 1000.0
            self.input_handler.process_events()
            self.input_handler.process_held_keys()
            self.update(dt)
            self.renderer.draw()
            pygame.display.flip()
        pygame.quit()
        sys.exit()