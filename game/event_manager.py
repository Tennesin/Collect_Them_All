import os
import random
import importlib.util
from dataclasses import dataclass

from game.game_config import (
    EVENTS_DIR_NAME, EVENT_RESPAWN_CYCLES,
    EVENT_BASE_DENSITY, EVENT_DENSITY_PER_PLAYER, MIN_EVENTS_ABSOLUTE,
)

# Корень проекта = на уровень выше папки game/
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EVENTS_ROOT = os.path.join(_PROJECT_ROOT, EVENTS_DIR_NAME)

@dataclass
class EventOutcome:
    """Один из шести возможных исходов броска кубика."""
    text: str
    gold_delta: int = 0
    silver_delta: int = 0
    moves_delta: int = 0

class EventDefinition:
    """Базовый класс события. Каждый events/<id>/<id>.py должен объявить
    собственный класс-наследник и присвоить его модульной переменной EVENT."""
    id = None                # уникальный идентификатор, совпадает с именем папки
    icon_file = None         # имя png-файла внутри папки события
    prompt_text = ""         # текст в окне подтверждения
    outcomes = {}            # {1: EventOutcome, 2: EventOutcome, ..., 6: EventOutcome}

    @property
    def icon_dir(self):
        return os.path.join(EVENTS_ROOT, self.id)

    def get_outcome(self, roll):
        return self.outcomes[roll]

class EventRegistry:
    """Читает содержимое events/ один раз при создании. Ничего не знает
    про игровое поле, игроков или ход партии — чистый каталог доступных событий."""

    def __init__(self):
        self._definitions = {}
        self._load_all()

    def _load_all(self):
        if not os.path.isdir(EVENTS_ROOT):
            return
        for entry in sorted(os.listdir(EVENTS_ROOT)):
            folder = os.path.join(EVENTS_ROOT, entry)
            if not os.path.isdir(folder):
                continue
            module_path = os.path.join(folder, f"{entry}.py")
            if not os.path.isfile(module_path):
                continue
            self._load_one(entry, module_path)

    def _load_one(self, entry, module_path):
        spec = importlib.util.spec_from_file_location(f"events.{entry}.{entry}", module_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        event_cls = getattr(module, "EVENT", None)
        if event_cls is None:
            print(f"[EventRegistry] {entry}.py не объявляет переменную EVENT — файл пропущен.")
            return

        instance = event_cls()
        if not instance.id:
            instance.id = entry
        self._definitions[instance.id] = instance

    def all(self):
        return list(self._definitions.values())

    def get(self, event_id):
        return self._definitions.get(event_id)


class EventManager:
    def __init__(self, field, player_count, registry=None):
        self.field = field
        self.player_count = player_count
        self.registry = registry or EventRegistry()

        self.active_events = {}  # {(x, y): EventDefinition}
        self._occupied_provider = None  # callable() -> set[(x, y)] клетки, занятые игроками
        self._currency_provider = None  # callable() -> set[(x, y)] клетки с золотом/серебром
        self._visible_provider = None  # callable() -> set[(x, y)] клетки, видимые игрокам прямо сейчас
        self._cycles_since_respawn = 0

    def bind_dynamic_providers(self, occupied_provider, currency_provider, visible_provider=None):
        self._occupied_provider = occupied_provider
        self._currency_provider = currency_provider
        self._visible_provider = visible_provider

    # --- Цикл ходов ---

    def on_cycle_complete(self):
        self._cycles_since_respawn += 1
        if self._cycles_since_respawn >= EVENT_RESPAWN_CYCLES:
            self._cycles_since_respawn = 0
            self.respawn()

    def respawn(self):
        available = self.registry.all()
        if not available:
            self.active_events.clear()
            return

        visible = self._visible_provider() if self._visible_provider else set()
        kept = {pos: definition for pos, definition in self.active_events.items() if pos in visible}

        free_cells = [pos for pos in self._collectible_free_cells() if pos not in kept]
        total_pool = len(free_cells) + len(kept)
        target_count = self._event_count(total_pool)
        to_place = max(0, min(target_count - len(kept), len(free_cells)))

        random.shuffle(free_cells)
        self.active_events = kept
        for pos in free_cells[:to_place]:
            self.active_events[pos] = random.choice(available)

    def _event_count(self, free_cells_count):
        density = EVENT_BASE_DENSITY + EVENT_DENSITY_PER_PLAYER * (self.player_count - 1)
        count = int(round(free_cells_count * density))
        count = max(MIN_EVENTS_ABSOLUTE, count)
        return min(count, free_cells_count)

    def _collectible_free_cells(self):
        field = self.field
        occupied = self._occupied_provider() if self._occupied_provider else set()
        currency = self._currency_provider() if self._currency_provider else set()
        return [
            (x, y)
            for x in range(field.width)
            for y in range(field.height)
            if field.is_free(x, y)
            and (x, y) not in field.reserved_cells
            and (x, y) not in occupied
            and (x, y) not in currency
        ]

    # --- Доступ извне ---

    def get_event_at(self, pos):
        return self.active_events.get(pos)

    def consume_at(self, x, y):
        """Снимает событие с клетки (вызывается один раз, когда игрок реально
        наступил на клетку) и возвращает его определение, либо None."""
        return self.active_events.pop((x, y), None)