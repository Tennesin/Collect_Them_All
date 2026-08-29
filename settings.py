SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 60

GAME_TITLE = "Collect Them All!"

# --- Игровое поле и камера ---
INITIAL_SCALE = 30
MAX_SCALE = 50
PLAYER_SPEED = 5.0

# Цвета игрового поля
BG_COLOR = (135, 206, 235)
FIELD_COLOR = (34, 139, 34)
GRID_COLOR = (0, 100, 0)
HOVER_COLOR = (80, 200, 80)
PATH_COLOR = (255, 80, 80)
BLOCK_COLOR = (50, 50, 50)
WALL_COLOR = (90, 90, 90)
OBSTACLE_BORDER = (20, 20, 20)
PREVIEW_COLOR = (255, 80, 80, 150)

# Визуальные коэффициенты отрисовки (доля от текущего camera.scale)
WALL_THICKNESS_RATIO = 0.35
PATH_WIDTH_RATIO = 0.25
PATH_GOAL_RADIUS_RATIO = 0.3
PREVIEW_WIDTH_RATIO = 0.2
PREVIEW_DASH_RATIO = 0.2
PREVIEW_GAP_RATIO = 0.1
PLAYER_RADIUS_RATIO = 0.2

# --- Игроки (замена одиночного PLAYER_COLOR) ---
PLAYER_COLORS = {
    "red": (220, 40, 40),
    "blue": (40, 100, 220),
    "yellow": (230, 200, 40),
    "orange": (235, 140, 40),
    "pink": (230, 100, 180),
}

# Порядок раздачи цветов игрокам 1..5
PLAYER_COLOR_ORDER = ["red", "blue", "yellow", "orange", "pink"]

PLAYER_NAMES_RU = {
    "red": "Красный",
    "blue": "Синий",
    "yellow": "Жёлтый",
    "orange": "Оранжевый",
    "pink": "Розовый",
}

# Отрисовка "слоёв", когда несколько игроков в одной клетке
STACK_OFFSET_RATIO = 0.4   # смещение каждого следующего слоя, доля от радиуса круга
PLAYER_DIM_FACTOR = 0.45   # насколько темнее рисуются ожидающие (не ходящие сейчас) игроки

# --- UI (меню, настройки, пауза) ---
FONT_NAME = None  # None = системный шрифт pygame по умолчанию
FONT_SIZE_TITLE = 48
FONT_SIZE_LABEL = 22
FONT_SIZE_BUTTON = 22
FONT_SIZE_HINT = 16

MENU_BG_COLOR = (30, 30, 40)
TEXT_COLOR = (235, 235, 235)
HINT_TEXT_COLOR = (140, 140, 150)

BUTTON_COLOR = (60, 60, 80)
BUTTON_HOVER_COLOR = (85, 85, 115)
BUTTON_DISABLED_COLOR = (45, 45, 50)
BUTTON_TEXT_COLOR = (235, 235, 235)
SELECTED_BORDER_COLOR = (120, 200, 255)

INPUT_BG_COLOR = (45, 45, 55)
INPUT_BG_COLOR_FOCUS = (55, 55, 70)
INPUT_BORDER_COLOR = (80, 80, 95)
INPUT_BORDER_COLOR_FOCUS = (120, 200, 255)
INPUT_BORDER_COLOR_ERROR = (200, 70, 70)
INPUT_TEXT_COLOR = (235, 235, 235)
INPUT_HINT_COLOR = (120, 120, 130)

SLIDER_BG_COLOR = (25, 25, 25)
SLIDER_BORDER_COLOR = (15, 15, 15)
SLIDER_FILL_COLOR = (120, 200, 255)

PAUSE_OVERLAY_COLOR = (10, 10, 15, 170)  # с альфа-каналом

DEFAULT_SCROLL_SPEED = 20