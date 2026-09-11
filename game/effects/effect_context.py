"""Узкая точка доступа, которую эффекты событий получают вместо всей сцены."""

class EffectContext:
    def __init__(self, gameplay_scene):
        self._scene = gameplay_scene

    def collect_nearby_silver(self, player, radius):
        self._scene.resource_manager.collect_nearby_silver(player, radius)

    def adjust_moves(self, delta):
        self._scene.turn_manager.adjust_moves(delta)

    def displace_player(self, player, distance):
        return self._scene.displace_player_randomly(player, distance)

    def push_out_of_obstacle_if_needed(self, player):
        self._scene.relocate_player_to_nearest_free_cell(player)