import pygame
from settings import GAME_AREA_WIDTH

class InputHandler:
    """Источник команд человека: клик задаёт цель, Space тормозит, C возвращает камеру."""

    def __init__(self, camera, field, player):
        self.camera = camera
        self.field = field
        self.player = player

        self.dragging = False
        self.last_mouse_pos = (0, 0)
        self.mouse_pos = None

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            self._on_mouse_down(event)
        elif event.type == pygame.MOUSEBUTTONUP:
            self._on_mouse_up(event)
        elif event.type == pygame.MOUSEMOTION:
            self._on_mouse_motion(event)
        elif event.type == pygame.MOUSEWHEEL:
            self._on_mouse_wheel(event)
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                self.player.stop_movement()
            elif event.key == pygame.K_c:
                self.camera.follow = True

    def process_held_keys(self):
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]:
            if keys[pygame.K_UP]:
                self.camera.zoom(1.02)
            if keys[pygame.K_DOWN]:
                self.camera.zoom(0.98)

    def get_hovered_cell(self):
        cell = self._cell_under_mouse()
        if cell is None:
            return None
        player = self.player
        passable = player.ignores_obstacles or self.field.is_free(*cell)
        if passable and cell in player.explored_cells:
            return cell
        return None

    # --- Обработчики событий ---

    def _on_mouse_down(self, event):
        if event.button == 3:  # ПКМ - драг камеры
            self.dragging = True
            self.camera.follow = False
            self.last_mouse_pos = event.pos
        elif event.button == 1:  # ЛКМ - новая цель
            self._handle_left_click()

    def _on_mouse_up(self, event):
        if event.button == 3:
            self.dragging = False

    def _on_mouse_motion(self, event):
        self.mouse_pos = event.pos
        if self.dragging:
            dx = event.pos[0] - self.last_mouse_pos[0]
            dy = event.pos[1] - self.last_mouse_pos[1]
            self.camera.pan(dx, dy)
            self.last_mouse_pos = event.pos

    def _on_mouse_wheel(self, event):
        if event.y > 0:
            self.camera.zoom(1.1)
        elif event.y < 0:
            self.camera.zoom(0.9)

    def _handle_left_click(self):
        goal = self._cell_under_mouse()
        if goal is None:
            return
        player = self.player
        if not player.ignores_obstacles and not self.field.is_free(*goal):
            return
        if goal not in player.explored_cells:
            return

        start = player.anchor_cell
        path = self.field.find_path(
            start, goal,
            allowed_cells=player.explored_cells,
            ignore_obstacles=player.ignores_obstacles,
        )
        if goal != start and not path:
            return  # цель недостижима по известным клеткам
        # goal == start при движении означает "остановись у ближайшей клетки"
        player.follow_path(path)
        self.camera.follow = True

    def _cell_under_mouse(self):
        if self.mouse_pos is None or self.mouse_pos[0] >= GAME_AREA_WIDTH:
            return None
        wx, wy = self.camera.screen_to_world(*self.mouse_pos)
        if 0 <= wx < self.field.width and 0 <= wy < self.field.height:
            return (int(wx), int(wy))
        return None