from dataclasses import dataclass

# --- Границы значений, которые задаются на экране настроек ---
MIN_MAP_SIZE = 7
MAX_MAP_SIZE = 50

MIN_OBSTACLE_PERCENT = 10
MAX_OBSTACLE_PERCENT = 35
DEFAULT_OBSTACLE_PERCENT = 20

MIN_PLAYERS = 1
MAX_PLAYERS = 5
DEFAULT_PLAYERS = 1

DEFAULT_MAP_SIZE = 12

# (подпись кнопки, ширина, высота)
MAP_SIZE_PRESETS = [
    ("12x12", 12, 12),
    ("18x18", 18, 18),
    ("25x25", 25, 25),
]


@dataclass
class GameSettings:
    """Параметры одной партии, собранные игроком на экране настроек.
    Не хранит ничего игрового (позиции, поле и т.д.) — только конфигурацию."""

    map_width: int = DEFAULT_MAP_SIZE
    map_height: int = DEFAULT_MAP_SIZE
    obstacle_percent: int = DEFAULT_OBSTACLE_PERCENT
    player_count: int = DEFAULT_PLAYERS

    def clamp(self):
        """Подгоняет значения под допустимые границы. Вызывается перед стартом партии,
        так как ручной ввод размера карты может быть некорректным."""
        self.map_width = max(MIN_MAP_SIZE, min(MAX_MAP_SIZE, self.map_width))
        self.map_height = max(MIN_MAP_SIZE, min(MAX_MAP_SIZE, self.map_height))
        self.obstacle_percent = max(MIN_OBSTACLE_PERCENT, min(MAX_OBSTACLE_PERCENT, self.obstacle_percent))
        self.player_count = max(MIN_PLAYERS, min(MAX_PLAYERS, self.player_count))

    @property
    def obstacle_fraction(self) -> float:
        """Доля препятствий в виде числа 0..1 — то, что реально нужно ObstacleGenerator."""
        return self.obstacle_percent / 100.0