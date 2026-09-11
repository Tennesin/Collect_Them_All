"""Небольшая утилита для плавных анимаций (числовых интерполяций), не привязанная
к конкретной сцене или виджету — используется везде, где раньше значение
менялось мгновенно (альфа попапов, положение камеры и т.д.)."""

def linear(t):
    return t

def ease_out_cubic(t):
    return 1 - (1 - t) ** 3

def ease_in_cubic(t):
    return t ** 3

def ease_in_out_cubic(t):
    if t < 0.5:
        return 4 * t ** 3
    return 1 - (-2 * t + 2) ** 3 / 2

class Tween:
    """Интерполирует число от start к end за duration секунд по заданной кривой."""

    def __init__(self, start, end, duration, ease=ease_out_cubic):
        self.start = start
        self.end = end
        self.duration = max(0.0001, duration)
        self.ease = ease
        self.elapsed = 0.0
        self.value = start

    @property
    def finished(self):
        return self.elapsed >= self.duration

    def update(self, dt):
        self.elapsed = min(self.duration, self.elapsed + dt)
        progress = self.elapsed / self.duration
        eased = self.ease(progress)
        self.value = self.start + (self.end - self.start) * eased
        return self.value

    def reset(self, start, end, duration=None):
        """Перезапускает ту же Tween с новыми границами — удобно, чтобы развернуть
        fade-in в fade-out, продолжив с текущего значения (start=self.value)."""
        self.start = start
        self.end = end
        if duration is not None:
            self.duration = max(0.0001, duration)
        self.elapsed = 0.0
        self.value = start