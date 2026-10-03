from game.game_config import SILVER_RESPAWN_INTERVAL, EVENT_RESPAWN_INTERVAL

class BotKnowledge:
    """Что бот помнит о мире. Серебро и события попадают сюда, только если бот
    видел их сам (клетка была в player.visible_cells)."""

    def __init__(self):
        self.silver = {}   # {клетка: (количество, время последнего наблюдения)}
        self.events = {}   # {клетка: (EventDefinition, время последнего наблюдения)}

    def observe(self, world, player, now):
        visible = player.visible_cells
        silver_world = world.resource_manager.silver_cells
        events_world = world.event_manager.active_events

        for pos, amount in silver_world.items():
            if pos in visible:
                self.silver[pos] = (amount, now)
        for pos, definition in events_world.items():
            if pos in visible:
                self.events[pos] = (definition, now)

        # «Призраки»: клетка видна сейчас, а добычи на ней уже нет.
        for pos in [p for p in self.silver if p in visible and p not in silver_world]:
            del self.silver[pos]
        for pos in [p for p in self.events if p in visible and p not in events_world]:
            del self.events[pos]

        self._forget_stale(now)

    def _forget_stale(self, now):
        """Вне поля зрения мир перераскладывает добычу по таймеру, поэтому
        старое воспоминание через интервал респавна уже ненадёжно."""
        for pos in [p for p, (_, seen) in self.silver.items() if now - seen > SILVER_RESPAWN_INTERVAL]:
            del self.silver[pos]
        for pos in [p for p, (_, seen) in self.events.items() if now - seen > EVENT_RESPAWN_INTERVAL]:
            del self.events[pos]