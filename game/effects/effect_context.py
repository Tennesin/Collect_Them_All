"""Узкая точка доступа, которую эффекты событий получают вместо всего мира."""

class EffectContext:
    def __init__(self, world):
        self._world = world

    def collect_nearby_silver(self, player, radius):
        self._world.resource_manager.collect_nearby_silver(player, radius)

    def displace_player(self, player, distance):
        return self._world.displace_player_randomly(player, distance)

    def push_out_of_obstacle_if_needed(self, player):
        self._world.relocate_player_to_nearest_free_cell(player)