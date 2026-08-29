import pygame
from settings import *
from game_config import TURN_MAX_MOVES, TURN_TIME_SECONDS
from camera import Camera
from field import Field
from obstacle_generator import ObstacleGenerator
from player import Player
from turn_manager import TurnManager
from input_handler import InputHandler
from renderer import Renderer
from scenes import Scene

class GameplayScene(Scene):
    """Сборка и цикл собственно игры на поле. Создаёт нужное количество
    игроков (Красный, Синий, Жёлтый, Оранжевый, Розовый — по очереди),
    ботов пока нет: каждым по очереди управляет один и тот же человек."""

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

        # --- Игроки: все стартуют в одной клетке, поэтому сразу видно "слои" ---
        start_cell = (0, 0)
        self.players = []
        for i in range(settings.player_count):
            color_key = PLAYER_COLOR_ORDER[i]
            player = Player(self.field, start_cell=start_cell, speed=PLAYER_SPEED, color_key=color_key)
            player.on_move = self.camera.center_on
            self.players.append(player)

        # --- Очередь ходов ---
        self.turn_manager = TurnManager(self.players, max_moves=TURN_MAX_MOVES, turn_time=TURN_TIME_SECONDS)
        for player in self.players:
            player.on_cell_reached = self.turn_manager.consume_move
        self.turn_manager.on_turn_change = self._on_turn_change

        self.input_handler = InputHandler(self.camera, self.field, self.turn_manager)
        self.renderer = Renderer(screen, self.camera, self.field, self.players, self.turn_manager, self.input_handler)

        self.camera.center_on(self.players[0].pos_x, self.players[0].pos_y)

    def _on_turn_change(self, new_player):
        """Колбэк TurnManager'а: очищаем чужой предпросмотр пути и переносим
        камеру на игрока, чей ход начался."""
        self.input_handler.clear_preview()
        self.camera.center_on(new_player.pos_x, new_player.pos_y)

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            from scene_pause import PauseScene
            self.manager.push(PauseScene(self.manager, self))
            return
        self.input_handler.handle_event(event)

    def update(self, dt):
        self.input_handler.process_held_keys()
        self.turn_manager.update(dt)

        current = self.turn_manager.current_player
        if current.moving:
            current.update(dt)

    def draw(self, screen):
        self.renderer.draw()