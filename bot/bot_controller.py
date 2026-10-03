class BotController:
    """Источник команд для бота. Раз в think_interval вызывает think(), который
    выбирает цель и задаёт путь через player.follow_path(). Пока думать нечем:
    каркас с таймерами готов, мозг добавится на этапе 3."""

    def __init__(self, world, player, profile, index=0, total=1):
        self.world = world
        self.player = player
        self.profile = profile
        # Обратный отсчёт до ближайшего размышления: стартовая задержка плюс сдвиг по фазе,
        # чтобы несколько ботов не думали в один и тот же кадр.
        self._time_to_think = profile.start_delay + profile.think_interval * index / max(1, total)

    def update(self, dt):
        self._time_to_think -= dt
        if self._time_to_think > 0:
            return
        self._time_to_think += self.profile.think_interval
        self.think()

    def think(self):
        """Этап 3: выбор цели, построение пути, защита от застревания."""
        pass