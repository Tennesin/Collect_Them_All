import random


class EventResolver:
    """Применяет исход события к игроку. Ничего не знает про UI и сцены."""

    def __init__(self, world):
        self._world = world

    @staticmethod
    def roll():
        return random.randint(1, 6)

    def resolve(self, player, event, roll):
        """Возвращает (outcome, effect). Эффект создан, но НЕ наложен на игрока."""
        outcome = event.get_outcome(roll)
        player.gold = max(0, player.gold + outcome.gold_delta)
        player.silver = max(0, player.silver + outcome.silver_delta)
        effect = outcome.effect_factory() if outcome.effect_factory else None
        return outcome, effect

    def commit(self, player, outcome, effect):
        """Смещение и наложение эффекта - момент, когда событие реально закончилось."""
        if outcome.displacement_cells:
            self._world.displace_player_randomly(player, outcome.displacement_cells)
        if effect is not None:
            player.add_effect(effect)

    def resolve_now(self, player, event, roll):
        """Полный цикл без окна - для ботов."""
        outcome, effect = self.resolve(player, event, roll)
        self.commit(player, outcome, effect)
        return outcome, effect