from dataclasses import dataclass
from typing import Optional
from game.generation.gold_layout import gold_capacity

# --- Границы значений, которые задаются на экране настроек ---
MIN_MAP_SIZE = 11
MAX_MAP_SIZE = 50

MIN_OBSTACLE_PERCENT = 10
MAX_OBSTACLE_PERCENT = 35
DEFAULT_OBSTACLE_PERCENT = 20

MIN_BOT_COUNT = 0
MAX_BOT_COUNT = 4
DEFAULT_BOT_COUNT = 0

BOT_DIFFICULTY_ORDER = ["easy", "normal", "hard"]
DEFAULT_BOT_DIFFICULTY = "normal"

MIN_VISION_RADIUS = 3
MAX_VISION_RADIUS = 10
DEFAULT_VISION_RADIUS = 4

DEFAULT_MAP_SIZE = 15

# --- Движение в реальном времени ---
PLAYER_BASE_SPEED = 3.0        # клеток в секунду
MIN_SPEED_MULTIPLIER = 0.0     # 0 = полная остановка (стан)
MAX_SPEED_MULTIPLIER = 2.5
FIELD_COLOR_VARIANT_COUNT = 4   # сколько оттенков травы; должно совпадать с len(FIELD_COLOR_VARIANTS) в settings.py

# --- Периодические события мира, секунды ---
GOLD_YIELD_INTERVAL = 10.0     # раз в столько секунд в золотых клетках копится GOLD_CELL_YIELD
SILVER_RESPAWN_INTERVAL = 15.0
EVENT_RESPAWN_INTERVAL = 20.0

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
MIN_GOLD_CELLS = 3             # действует там, где карта вмещает столько (см. min_gold_cells_for_map)
MAX_GOLD_CELLS = 8
DEFAULT_GOLD_CELLS = 4         # столько вмещает карта по умолчанию (15x15)
GOLD_CELL_YIELD = 2
GOLD_CELL_BOX_RADIUS = 2       # половина стороны короба (2 -> короб 5x5)
GOLD_CELL_BUFFER = 1           # свободных клеток между коробами, до края карты и до старта/финиша (общая для соседей)

# --- Серебряные клетки ---
SILVER_CELL_BASE_DENSITY = 0.05
SILVER_CELL_DENSITY_PER_PLAYER = 0.01
MIN_SILVER_CELLS_ABSOLUTE = 1

SILVER_PILE_MIN_VALUE = 15
SILVER_PILE_MAX_VALUE = 45

# --- Условия победы (настраиваются на экране NewGameScene) ---
MIN_WIN_GOLD = 10
MAX_WIN_GOLD = 50
WIN_GOLD_STEP = 5
DEFAULT_WIN_GOLD = 25

MIN_WIN_SILVER = 50
MAX_WIN_SILVER = 500
WIN_SILVER_STEP = 25
DEFAULT_WIN_SILVER = 125

# --- События ---
EVENTS_DIR_NAME = "events"          # имя папки-реестра, на уровне корня проекта

MIN_EVENT_DENSITY_PERCENT = 2
MAX_EVENT_DENSITY_PERCENT = 10
EVENT_DENSITY_PERCENT_STEP = 1
DEFAULT_EVENT_DENSITY_PERCENT = 4   # эквивалент прежней константы EVENT_BASE_DENSITY

EVENT_DENSITY_PER_PLAYER = 0.005    # доп. плотность за каждого игрока сверх первого — остаётся фиксированной
MIN_EVENTS_ABSOLUTE = 1

def max_gold_cells_for_map(width, height):
    """Верхняя граница золотых клеток: сколько коробов карта гарантированно вмещает."""
    capacity = gold_capacity(width, height, GOLD_CELL_BOX_RADIUS, GOLD_CELL_BUFFER)
    return min(MAX_GOLD_CELLS, capacity)

def min_gold_cells_for_map(width, height):
    """Нижняя граница: MIN_GOLD_CELLS, но не больше того, что вмещает карта."""
    return min(MIN_GOLD_CELLS, max_gold_cells_for_map(width, height))

@dataclass
class GameSettings:
    map_width: int = DEFAULT_MAP_SIZE
    map_height: int = DEFAULT_MAP_SIZE
    bot_count: int = DEFAULT_BOT_COUNT
    bot_difficulty: str = DEFAULT_BOT_DIFFICULTY
    obstacle_percent: int = DEFAULT_OBSTACLE_PERCENT
    win_gold_required: int = DEFAULT_WIN_GOLD
    win_silver_required: int = DEFAULT_WIN_SILVER
    gold_cell_count: int = DEFAULT_GOLD_CELLS
    vision_radius: int = DEFAULT_VISION_RADIUS
    event_density_percent: int = DEFAULT_EVENT_DENSITY_PERCENT
    seed: Optional[int] = None

    def clamp(self):
        self.map_width = max(MIN_MAP_SIZE, min(MAX_MAP_SIZE, self.map_width))
        self.map_height = max(MIN_MAP_SIZE, min(MAX_MAP_SIZE, self.map_height))
        self.obstacle_percent = max(MIN_OBSTACLE_PERCENT, min(MAX_OBSTACLE_PERCENT, self.obstacle_percent))
        self.bot_count = max(MIN_BOT_COUNT, min(MAX_BOT_COUNT, self.bot_count))
        if self.bot_difficulty not in BOT_DIFFICULTY_ORDER:
            self.bot_difficulty = DEFAULT_BOT_DIFFICULTY

        self.win_gold_required = self._clamp_step(self.win_gold_required, MIN_WIN_GOLD, MAX_WIN_GOLD, WIN_GOLD_STEP)
        self.win_silver_required = self._clamp_step(
            self.win_silver_required, MIN_WIN_SILVER, MAX_WIN_SILVER, WIN_SILVER_STEP
        )

        min_cells = min_gold_cells_for_map(self.map_width, self.map_height)
        max_cells = max_gold_cells_for_map(self.map_width, self.map_height)
        self.gold_cell_count = max(min_cells, min(max_cells, self.gold_cell_count))

        self.vision_radius = max(MIN_VISION_RADIUS, min(MAX_VISION_RADIUS, self.vision_radius))
        self.event_density_percent = max(
            MIN_EVENT_DENSITY_PERCENT, min(MAX_EVENT_DENSITY_PERCENT, self.event_density_percent)
        )

    @staticmethod
    def _clamp_step(value, min_value, max_value, step):
        value = max(min_value, min(max_value, value))
        steps = round((value - min_value) / step)
        return min_value + steps * step

    @property
    def obstacle_fraction(self) -> float:
        """Доля препятствий в виде числа 0..1 — то, что реально нужно ObstacleGenerator."""
        return self.obstacle_percent / 100.0

    @property
    def player_count(self) -> int:
        """Всего участников партии: человек + боты (по этому числу растёт плотность ресурсов и событий)."""
        return 1 + self.bot_count

    @property
    def event_density_fraction(self) -> float:
        """Доля событий в виде числа 0..1 — то, что реально нужно EventManager."""
        return self.event_density_percent / 100.0