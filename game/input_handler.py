import pygame

class InputHandler:
    def __init__(self, camera, field, turn_manager):
        self.camera = camera
        self.field = field
        self.turn_manager = turn_manager

        self.dragging = False
        self.last_mouse_pos = (0, 0)
        self.mouse_pos = None

        self.preview_path = None
        self.preview_goal = None

    @property
    def player(self):
        return self.turn_manager.current_player

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            self._on_mouse_down(event)
        elif event.type == pygame.MOUSEBUTTONUP:
            self._on_mouse_up(event)
        elif event.type == pygame.MOUSEMOTION:
            self._on_mouse_motion(event)
        elif event.type == pygame.MOUSEWHEEL:
            self._on_mouse_wheel(event)
        elif event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
            self._on_space_pressed()

    def process_held_keys(self):
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]:
            if keys[pygame.K_UP]:
                self.camera.zoom(1.02)
            if keys[pygame.K_DOWN]:
                self.camera.zoom(0.98)

    def get_hovered_cell(self):
        player = self.player
        if player.moving or self.mouse_pos is None:
            return None
        wx, wy = self.camera.screen_to_world(*self.mouse_pos)
        if 0 <= wx < self.field.width and 0 <= wy < self.field.height:
            cell = (int(wx), int(wy))
            passable = player.ignores_obstacles or self.field.is_free(*cell)
            if passable and cell in player.explored_cells:
                return cell
        return None

    # --- Обработчики событий ---

    def _on_mouse_down(self, event):
        if event.button == 3:  # ПКМ — драг камеры
            self.dragging = True
            self.last_mouse_pos = event.pos
        elif event.button == 1:  # ЛКМ — выбор цели
            self._handle_left_click()

    def _on_mouse_up(self, event):
        if event.button == 3:
            self.dragging = False

    def _on_mouse_motion(self, event):
        self.mouse_pos = event.pos
        if self.dragging and not self.player.moving:
            dx = event.pos[0] - self.last_mouse_pos[0]
            dy = event.pos[1] - self.last_mouse_pos[1]
            self.camera.pan(dx, dy)
            self.last_mouse_pos = event.pos

    def _on_mouse_wheel(self, event):
        if event.y > 0:
            self.camera.zoom(1.1)
        elif event.y < 0:
            self.camera.zoom(0.9)

    def _on_space_pressed(self):
        if self.player.stop_movement():
            self.clear_preview()

    def _handle_left_click(self):
        player = self.player
        if player.moving or self.mouse_pos is None:
            return
        wx, wy = self.camera.screen_to_world(*self.mouse_pos)
        if not (0 <= wx < self.field.width and 0 <= wy < self.field.height):
            return
        goal_cell = (int(wx), int(wy))
        if not player.ignores_obstacles and not self.field.is_free(*goal_cell):
            return
        if goal_cell not in player.explored_cells:
            return
        if goal_cell == (player.grid_x, player.grid_y):
            return

        if self.preview_goal == goal_cell and self.preview_path:
            player.follow_path(self.preview_path)
            self.clear_preview()
        else:
            path = self._capped_path(player, goal_cell)
            if path:
                self.preview_path = path
                self.preview_goal = goal_cell
            else:
                self.clear_preview()

    def _capped_path(self, player, goal_cell):
        limit = self.turn_manager.moves_left
        if limit <= 0:
            return []
        path = self.field.find_path(
            (player.grid_x, player.grid_y), goal_cell,
            allowed_cells=player.explored_cells,
            ignore_obstacles=player.ignores_obstacles,
        )
        if not path:
            return []
        return path[:limit]

    def clear_preview(self):
        self.preview_path = None
        self.preview_goal = None