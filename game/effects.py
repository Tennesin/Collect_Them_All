"""Базовый интерфейс временных эффектов, которые события накладывают на игрока."""

class Effect:
    """Базовый класс одного временного эффекта на игроке."""

    label = "Эффект"   # человекочитаемое название для панели игрока (RU)
    warning = False    # подсветить ли как предупреждение (например, проклятие)

    def __init__(self, duration_turns):
        self.duration_turns = duration_turns

    def tick(self):
        """Вызывается читателем один раз в конце каждого черёда игрока."""
        self.duration_turns -= 1
        return self.duration_turns > 0

    def on_cell_reached(self, player, context):
        """Игрок только что остановился на клетке (после хода)."""
        pass

    def modify_income(self, player, resource_type, amount):
        """Игрок получает доход resource_type ('gold' | 'silver') в размере amount."""
        return amount