import random

class EventResolver:
    """Применяет исход события к игроку. Ничего не знает про UI и сцены."""

    def __init__(self, world):
        self._world = world

    @staticmethod
    def roll():
        return random.randint(1, 6)

    def resolve(self, player, event, roll):
        """Возвращает (outcome, effect): исход и созданный эффект (или None) — для показа в попапе."""
        outcome = event.get_outcome(roll)
        player.gold = max(0, player.gold + outcome.gold_delta)
        player.silver = max(0, player.silver + outcome.silver_delta)
        if outcome.displacement_cells:
            self._world.displace_player_randomly(player, outcome.displacement_cells)
        effect = outcome.effect_factory() if outcome.effect_factory else None
        if effect is not None:
            player.add_effect(effect)
        return outcome, effect