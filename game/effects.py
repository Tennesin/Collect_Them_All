"""Базовый интерфейс временных эффектов, которые события накладывают на игрока."""

class Effect:
    """Базовый класс одного временного эффекта на игроке."""

    label = "Эффект"   # человекочитаемое название для панели игрока (RU)
    warning = False    # подсветить ли как предупреждение (например, проклятие)

    # --- Необязательные модификаторы, которые читают другие системы игры ---
    ignores_obstacles = False       # Field/InputHandler: путь строится сквозь стены
    vision_radius_override = None   # FogOfWar: заменяет базовый радиус обзора, если задано
    full_map_vision = False         # FogOfWar: считать всю карту видимой, пока эффект активен
    max_moves_override = None       # TurnManager: абсолютный лимит ходов за черёд, если задано
    max_moves_multiplier = None     # TurnManager: множитель к лимиту ходов за черёд

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

    def on_expire(self, player, context):
        """Вызывается один раз, когда эффект истёк (сразу после последнего tick())."""
        pass