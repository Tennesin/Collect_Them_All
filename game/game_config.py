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

MIN_TURN_MOVES = 4
MAX_TURN_MOVES = 16
DEFAULT_TURN_MOVES = TURN_MAX_MOVES

MIN_TURN_TIME = 15
MAX_TURN_TIME = 60
TURN_TIME_STEP = 3
DEFAULT_TURN_TIME = 30

MIN_VISION_RADIUS = 3
MAX_VISION_RADIUS = 10
DEFAULT_VISION_RADIUS = 4

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
MIN_GOLD_CELLS = 3
MAX_GOLD_CELLS = 8
DEFAULT_GOLD_CELLS = 5
GOLD_CELL_AREA_PER_CELL = 40  # сколько клеток поля "полагается" на одну золотую клетку
GOLD_CELL_YIELD = 2            # золота за один цикл ходов всех игроков
GOLD_CELL_BOX_RADIUS = 2       # половина стороны короба (2 -> короб 5x5)
GOLD_CELL_BUFFER = 1           # минимум свободных клеток вокруг короба

# --- Серебряные клетки ---
SILVER_CELL_BASE_DENSITY = 0.05
SILVER_CELL_DENSITY_PER_PLAYER = 0.01
MIN_SILVER_CELLS_ABSOLUTE = 1

SILVER_PILE_MIN_VALUE = 15
SILVER_PILE_MAX_VALUE = 45

SILVER_RESPAWN_CYCLES = 2

# --- Туман войны ---
VISION_RADIUS = 4

# --- Условия победы (настраиваются на экране NewGameScene) ---
MIN_WIN_GOLD = 10
MAX_WIN_GOLD = 50
WIN_GOLD_STEP = 5
DEFAULT_WIN_GOLD = 25

MIN_WIN_SILVER = 50
MAX_WIN_SILVER = 500
WIN_SILVER_STEP = 25
DEFAULT_WIN_SILVER = 125

# --- Режим завершения партии ---
FINISH_MODE_INSTANT = "instant"  # игра заканчивается для всех сразу, как только кто-то выполнил условие
FINISH_MODE_RANKED = "ranked"    # игроки выбывают по мере финиша, в конце — таблица мест
DEFAULT_FINISH_MODE = FINISH_MODE_INSTANT


def max_gold_cells_for_map(width, height):
    """Верхняя граница количества золотых клеток, разумная для данного размера карты."""
    capacity = (width * height) // GOLD_CELL_AREA_PER_CELL
    return max(MIN_GOLD_CELLS, min(MAX_GOLD_CELLS, capacity))


@dataclass
class GameSettings:
    map_width: int = DEFAULT_MAP_SIZE
    map_height: int = DEFAULT_MAP_SIZE
    obstacle_percent: int = DEFAULT_OBSTACLE_PERCENT
    player_count: int = DEFAULT_PLAYERS
    win_gold_required: int = DEFAULT_WIN_GOLD
    win_silver_required: int = DEFAULT_WIN_SILVER
    gold_cell_count: int = DEFAULT_GOLD_CELLS
    finish_mode: str = DEFAULT_FINISH_MODE
    moves_per_turn: int = DEFAULT_TURN_MOVES
    turn_time_seconds: int = DEFAULT_TURN_TIME
    vision_radius: int = DEFAULT_VISION_RADIUS

    def clamp(self):
        self.map_width = max(MIN_MAP_SIZE, min(MAX_MAP_SIZE, self.map_width))
        self.map_height = max(MIN_MAP_SIZE, min(MAX_MAP_SIZE, self.map_height))
        self.obstacle_percent = max(MIN_OBSTACLE_PERCENT, min(MAX_OBSTACLE_PERCENT, self.obstacle_percent))
        self.player_count = max(MIN_PLAYERS, min(MAX_PLAYERS, self.player_count))

        self.win_gold_required = self._clamp_step(self.win_gold_required, MIN_WIN_GOLD, MAX_WIN_GOLD, WIN_GOLD_STEP)
        self.win_silver_required = self._clamp_step(
            self.win_silver_required, MIN_WIN_SILVER, MAX_WIN_SILVER, WIN_SILVER_STEP
        )

        max_cells = max_gold_cells_for_map(self.map_width, self.map_height)
        self.gold_cell_count = max(MIN_GOLD_CELLS, min(max_cells, self.gold_cell_count))

        if self.finish_mode not in (FINISH_MODE_INSTANT, FINISH_MODE_RANKED):
            self.finish_mode = DEFAULT_FINISH_MODE

        self.moves_per_turn = max(MIN_TURN_MOVES, min(MAX_TURN_MOVES, self.moves_per_turn))
        self.turn_time_seconds = int(
            self._clamp_step(self.turn_time_seconds, MIN_TURN_TIME, MAX_TURN_TIME, TURN_TIME_STEP))
        self.vision_radius = max(MIN_VISION_RADIUS, min(MAX_VISION_RADIUS, self.vision_radius))

    @staticmethod
    def _clamp_step(value, min_value, max_value, step):
        value = max(min_value, min(max_value, value))
        steps = round((value - min_value) / step)
        return min_value + steps * step

    @property
    def obstacle_fraction(self) -> float:
        """Доля препятствий в виде числа 0..1 — то, что реально нужно ObstacleGenerator."""
        return self.obstacle_percent / 100.0