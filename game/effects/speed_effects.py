"""Общие эффекты скорости: замедление, ускорение, оглушение.
События используют их через effect_factory, не описывая свои классы."""
from game.effects.effects import Effect, remove_warning_effects


class SlowEffect(Effect):
    warning = True
    stack_key = "slow"

    def __init__(self, factor, duration_seconds):
        super().__init__(duration_seconds)
        self.speed_multiplier = factor

    @property
    def label(self):
        return f"Замедление ×{self.speed_multiplier:g}"

    def absorb(self, other):
        super().absorb(other)
        self.speed_multiplier = min(self.speed_multiplier, other.speed_multiplier)


class HasteEffect(Effect):
    stack_key = "haste"

    def __init__(self, factor, duration_seconds, cleanses=False):
        super().__init__(duration_seconds)
        self.speed_multiplier = factor
        self.cleanses = cleanses  # True -> при наложении снимает все негативные эффекты

    @property
    def label(self):
        return f"Ускорение ×{self.speed_multiplier:g}"

    @property
    def description(self):
        return "снимает негативные эффекты" if self.cleanses else ""

    def absorb(self, other):
        super().absorb(other)
        self.speed_multiplier = max(self.speed_multiplier, other.speed_multiplier)

    def on_apply(self, player):
        if self.cleanses:
            remove_warning_effects(player)

class StunEffect(Effect):
    """Полная остановка. Ввод не блокируется: клики запоминают маршрут,
    и игрок побежит, когда оглушение закончится."""
    label = "Оглушение"
    warning = True
    stack_key = "stun"
    speed_multiplier = 0.0

class BusyEffect(Effect):
    """Бот «занят событием»: стоит на месте, как стоит человек над окном события."""
    label = "Занят"
    stack_key = "busy"
    speed_multiplier = 0.0