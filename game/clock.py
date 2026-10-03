class PeriodicTimer:
    """Вызывает callback каждые interval секунд игрового времени.
    Остаток времени не теряется: при больших dt callback вызовется несколько раз."""

    def __init__(self, interval, callback):
        self.interval = max(0.001, interval)
        self.callback = callback
        self.elapsed = 0.0

    def update(self, dt):
        self.elapsed += dt
        while self.elapsed >= self.interval:
            self.elapsed -= self.interval
            self.callback()

class WorldClock:
    """Игровые часы мира. Тикают только когда мир обновляется (пауза и попапы их останавливают)."""

    def __init__(self):
        self.match_time = 0.0
        self._timers = []

    def every(self, interval, callback):
        timer = PeriodicTimer(interval, callback)
        self._timers.append(timer)
        return timer

    def update(self, dt):
        self.match_time += dt
        for timer in self._timers:
            timer.update(dt)