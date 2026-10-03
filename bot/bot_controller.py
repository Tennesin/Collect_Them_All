from bot.bot_brain import BotBrain

class BotController:
    """Источник команд для бота. Раз в think_interval вызывает think(), который
    просит мозг выбрать цель и отдаёт путь в player.follow_path()."""

    IDLE_THINK_DELAY = 0.05   # как быстро бот задумывается после остановки
    STUCK_TIMEOUT = 3.0       # секунд на одной клетке при ненулевой скорости
    STUCK_BLACKLIST = 8.0     # сколько секунд игнорировать цель, на которой застряли

    def __init__(self, world, player, profile, index=0, total=1):
        self.world = world
        self.player = player
        self.profile = profile
        self.brain = BotBrain(world, player, profile)
        # Обратный отсчёт до ближайшего размышления: стартовая задержка плюс сдвиг по фазе,
        # чтобы несколько ботов не думали в один и тот же кадр.
        self._time_to_think = profile.start_delay + profile.think_interval * index / max(1, total)

        self._was_moving = False
        self._last_cell = (player.grid_x, player.grid_y)
        self._stuck_since = 0.0

    def update(self, dt):
        now = self.world.clock.match_time

        # Маршрут закончился (дошли, событие, телепорт): не ждём весь интервал.
        moving = bool(self.player.path)
        if self._was_moving and not moving:
            self._time_to_think = min(self._time_to_think, self.IDLE_THINK_DELAY)
        self._was_moving = moving

        self._check_stuck(now)

        self._time_to_think -= dt
        if self._time_to_think > 0:
            return
        self._time_to_think += self.profile.think_interval
        self.think()

    def think(self):
        plan = self.brain.plan(self.world.clock.match_time)
        if plan is None:
            return
        _goal, path = plan
        self.player.follow_path(path)

    def _check_stuck(self, now):
        player = self.player
        cell = (player.grid_x, player.grid_y)
        if cell != self._last_cell or not player.path or player.speed <= 0:
            # Оглушённый бот не «застрявший»: таймер сбрасывается.
            self._last_cell = cell
            self._stuck_since = now
            return
        if now - self._stuck_since < self.STUCK_TIMEOUT:
            return
        self._stuck_since = now
        self.brain.abandon_goal(now, self.STUCK_BLACKLIST)
        player.path = []
        self._time_to_think = 0.0