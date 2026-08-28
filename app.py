import pygame
import sys
from settings import *
from scenes import SceneManager
from scene_main_menu import MainMenuScene


class Application:
    """Composition root уровня приложения: инициализация pygame, окно, часы,
    SceneManager и главный цикл. Никакой игровой логики здесь нет —
    вся она находится внутри конкретных сцен."""

    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption(GAME_TITLE)
        self.clock = pygame.time.Clock()
        self.running = True

        self.scene_manager = SceneManager(self)
        self.scene_manager.push(MainMenuScene(self.scene_manager))

    def quit(self):
        self.running = False

    def run(self):
        while self.running:
            dt = self.clock.tick(FPS) / 1000.0
            self._process_events()
            self.scene_manager.update(dt)
            self.scene_manager.draw(self.screen)
            pygame.display.flip()
        pygame.quit()
        sys.exit()

    def _process_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            else:
                self.scene_manager.handle_event(event)