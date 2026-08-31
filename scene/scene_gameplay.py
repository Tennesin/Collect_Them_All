import pygame
from settings import *
from widgets import get_font
from game.game_config import FINISH_MODE_INSTANT, FINISH_MODE_RANKED
from game.camera import Camera
from game.field import Field
from game.obstacle_generator import ObstacleGenerator
from game.gold_cell_generator import GoldCellGenerator
from game.resource_manager import ResourceManager
from game.fog_of_war import FogOfWar
from game.player import Player
from game.turn_manager import TurnManager
from game.input_handler import InputHandler
from game.renderer import Renderer
from game.ui import PlayerPanel
from scene.scenes import Scene

class GameplayScene(Scene):

    def __init__(self, manager, settings):
        super().__init__(manager)
        self.settings = settings
        self.paused = False
        self.winner = None
        self.placements = []  # порядок финиша: 1-е место первым
        screen = self.manager.app.screen

        self.field = Field(settings.map_width, settings.map_height)

        GoldCellGenerator(self.field, settings.gold_cell_count).generate()

        total_cells = settings.map_width * settings.map_height
        max_obstacle_cells = int(total_cells * settings.obstacle_fraction)
        ObstacleGenerator(self.field, max_obstacle_cells).generate()

        self.resource_manager = ResourceManager(
            self.field, settings.player_count,
            settings.win_gold_required, settings.win_silver_required,
        )

        self.fog_of_war = FogOfWar(self.field, settings.vision_radius)
        self.camera = Camera(GAME_AREA_WIDTH, SCREEN_HEIGHT, settings.map_width, settings.map_height,
                             INITIAL_SCALE, MAX_SCALE)

        # --- Игроки: все стартуют в одной клетке, поэтому сразу видно "слои" ---
        start_cell = (0, 0)
        self.players = []
        for i in range(settings.player_count):
            color_key = PLAYER_COLOR_ORDER[i]
            player = Player(self.field, start_cell=start_cell, speed=PLAYER_SPEED, color_key=color_key)
            player.on_move = self.camera.center_on
            player.on_cell_reached = self._make_cell_reached_handler(player)
            self.fog_of_war.update_player(player)  # видимость на старте, до первого хода
            self.players.append(player)

        # --- Очередь ходов ---
        self.turn_manager = TurnManager(
            self.players, max_moves=settings.moves_per_turn, turn_time=settings.turn_time_seconds
        )
        self.turn_manager.on_turn_change = self._on_turn_change
        self.turn_manager.on_cycle_complete = self.resource_manager.on_cycle_complete

        self.input_handler = InputHandler(self.camera, self.field, self.turn_manager)
        self.renderer = Renderer(
            screen, self.camera, self.field, self.players,
            self.turn_manager, self.input_handler, self.resource_manager,
        )
        self.player_panel = PlayerPanel(self.turn_manager, self.resource_manager)

        self.camera.center_on(self.players[0].pos_x, self.players[0].pos_y)

    def _make_cell_reached_handler(self, player):
        def handler():
            self.fog_of_war.update_player(player)
            self.resource_manager.collect_at(player)

            if self.winner is None and player not in self.placements and self.resource_manager.check_win(player):
                self._handle_player_finish(player)
                return

            self.turn_manager.consume_move()
            player.warning_message = self.resource_manager.missing_requirements_message(player)

        return handler

    def _handle_player_finish(self, player):
        """Игрок только что выполнил условие победы на финишной клетке."""
        player.moving = False
        player.path = []
        self.placements.append(player)

        if self.settings.finish_mode == FINISH_MODE_INSTANT:
            self.winner = player
            return

        # Режим "до последнего": игрок выбывает, партия продолжается для остальных.
        self.turn_manager.eliminate(player)
        active_players = [p for p in self.players if p not in self.placements]

        if len(active_players) <= 1:
            if active_players:
                self.placements.append(active_players[0])  # последнее место — автоматически
            self.winner = self.placements[0]  # для совместимости с остальной логикой
            return

        self.turn_manager.end_turn_early()

    def _on_turn_change(self, new_player):
        self.input_handler.clear_preview()
        self.camera.center_on(new_player.pos_x, new_player.pos_y)

    def on_pause(self):
        self.paused = True

    def on_resume(self):
        """Сцена снова становится верхней после снятия паузы."""
        self.paused = False

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            if self.winner is not None:
                from scene.scene_main_menu import MainMenuScene
                self.manager.switch_to(MainMenuScene(self.manager))
            else:
                from scene.scene_pause import PauseScene
                self.manager.push(PauseScene(self.manager, self))
            return
        if self.winner is not None:
            return
        self.input_handler.handle_event(event)

    def update(self, dt):
        if self.paused or self.winner is not None:
            return
        self.input_handler.process_held_keys()
        self.turn_manager.update(dt)

        current = self.turn_manager.current_player
        if current.moving:
            current.update(dt)

    def draw(self, screen):
        self.renderer.draw()
        self.player_panel.draw(screen)
        if self.winner is not None:
            self._draw_victory_overlay(screen)

    def _draw_victory_overlay(self, screen):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill(PAUSE_OVERLAY_COLOR)
        screen.blit(overlay, (0, 0))

        if self.settings.finish_mode == FINISH_MODE_RANKED and len(self.placements) > 1:
            self._draw_placements(screen)
        else:
            name = PLAYER_NAMES_RU[self.winner.color_key]
            title_surf = get_font(FONT_SIZE_TITLE - 8).render(f"Победил игрок: {name}", True, self.winner.color)
            screen.blit(title_surf, title_surf.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 20)))

        hint_surf = get_font(FONT_SIZE_HINT + 4).render("Esc — выйти в меню", True, TEXT_COLOR)
        screen.blit(hint_surf, hint_surf.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 140)))

    def _draw_placements(self, screen):
        title_surf = get_font(FONT_SIZE_TITLE - 14).render("Итоговые места", True, TEXT_COLOR)
        screen.blit(title_surf, title_surf.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 130)))

        start_y = SCREEN_HEIGHT // 2 - 70
        for i, place_player in enumerate(self.placements):
            name = PLAYER_NAMES_RU[place_player.color_key]
            line = f"{i + 1}. {name}"
            surf = get_font(FONT_SIZE_LABEL + 4).render(line, True, place_player.color)
            screen.blit(surf, surf.get_rect(center=(SCREEN_WIDTH // 2, start_y + i * 34)))