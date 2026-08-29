from dataclasses import dataclass

# --- Границы значений, которые задаются на экране настроек ---
MIN_MAP_SIZE = 11
MAX_MAP_SIZE = 50

MIN_OBSTACLE_PERCENT = 10
MAX_OBSTACLE_PERCENT = 35
DEFAULT_OBSTACLE_PERCENT = 20

MIN_PLAYERS = 1
MAX_PLAYERS = 5
DEFAULT_PLAYERS = 1

# --- Правила одного черёда хода ---
TURN_MAX_MOVES = 8
TURN_TIME_SECONDS = 30.0

DEFAULT_MAP_SIZE = 15

# (подпись кнопки, ширина, высота)
MAP_SIZE_PRESETS = [
    ("15x15", 15, 15),
    ("22x22", 22, 22),
    ("30x30", 30, 30),
]

# --- Валюты игроков ---
STARTING_GOLD = 0
STARTING_SILVER = 0

# --- Золотые клетки ---
MIN_GOLD_CELLS = 4
MAX_GOLD_CELLS = 8
GOLD_CELL_YIELD = 2           # золота за один цикл ходов всех игроков
GOLD_CELL_BOX_RADIUS = 2      # половина стороны короба (2 -> короб 5x5)

# --- Серебряные клетки ---
SILVER_CELL_BASE_DENSITY = 0.05          # доля свободных клеток при 1 игроке
SILVER_CELL_DENSITY_PER_PLAYER = 0.01    # надбавка к доле за каждого игрока сверх первого
MIN_SILVER_CELLS_ABSOLUTE = 1            # минимум кучек, даже если формула даёт меньше

SILVER_PILE_MIN_VALUE = 15               # серебра в одной кучке — нижняя граница
SILVER_PILE_MAX_VALUE = 45               # серебра в одной кучке — верхняя граница

SILVER_RESPAWN_CYCLES = 2

# --- Условия победы ---
WIN_GOLD_REQUIRED = 25
WIN_SILVER_REQUIRED = 125

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