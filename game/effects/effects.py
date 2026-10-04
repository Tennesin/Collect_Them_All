"""Базовый интерфейс временных эффектов, которые события накладывают на игрока."""

class Effect:
    """Базовый класс одного временного эффекта на игроке. Длительность в секундах игрового времени."""

    label = "Эффект"   # название для панели игрока (RU)
    warning = False    # подсветить ли как предупреждение (например, проклятие или замедление)
    stack_key = None   # эффекты с одинаковым ключом не складываются, а продлевают друг друга
    description = ""   # необязательное пояснение для инструкции (то, чего нет в label)

    # --- Необязательные модификаторы, которые читают другие системы игры ---
    ignores_obstacles = False       # путь строится сквозь стены
    vision_radius_override = None   # заменяет базовый радиус обзора, если задано
    full_map_vision = False         # вся карта видима, пока эффект активен
    speed_multiplier = 1.0          # множитель скорости; эффекты перемножаются

    def __init__(self, duration_seconds):
        self.duration_seconds = duration_seconds

    @property
    def key(self):
        return self.stack_key or type(self).__name__

    def tick(self, dt):
        """Вызывается каждый кадр. Возвращает True, пока эффект ещё действует."""
        self.duration_seconds -= dt
        return self.duration_seconds > 0

    def absorb(self, other):
        """Вызывается у уже действующего эффекта, когда на игрока накладывают
        второй с тем же key. По умолчанию просто продлевает время."""
        self.duration_seconds = max(self.duration_seconds, other.duration_seconds)

    def on_update(self, player, dt, context):
        """Вызывается каждый кадр, пока эффект активен (для периодических механик)."""
        pass

    def on_cell_reached(self, player, context):
        """Игрок только что пришёл на клетку."""
        pass

    def modify_income(self, player, resource_type, amount):
        """Игрок получает доход resource_type ('gold' | 'silver') в размере amount."""
        return amount

    def on_expire(self, player, context):
        """Вызывается один раз, когда эффект истёк."""
        pass

    def on_apply(self, player):
        """Вызывается сразу после наложения эффекта на игрока."""
        pass

def remove_warning_effects(player):
    """Снимает с игрока все «плохие» эффекты (warning = True) и просит мир пересчитать обзор."""
    player.active_effects = [
        effect for effect in player.active_effects if not getattr(effect, "warning", False)
    ]
    player.vision_dirty = True