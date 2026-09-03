import random
from game.game_config import (
    GOLD_CELL_YIELD,
    SILVER_CELL_BASE_DENSITY, SILVER_CELL_DENSITY_PER_PLAYER, MIN_SILVER_CELLS_ABSOLUTE,
    SILVER_PILE_MIN_VALUE, SILVER_PILE_MAX_VALUE, SILVER_RESPAWN_CYCLES,
)
from game.effect_reader import EffectReader

class ResourceManager:

    def __init__(self, field, player_count, win_gold_required, win_silver_required):
        self.field = field
        self.player_count = player_count
        self.win_gold_required = win_gold_required
        self.win_silver_required = win_silver_required
        self.gold_deposits = {pos: 0 for pos in field.gold_cell_positions}
        self.silver_cells = {}
        self._cycles_since_silver_respawn = 0
        self._visible_provider = None  # клетки, видимые хотя бы одному игроку прямо сейчас
        self._event_provider = None  # клетки, занятые активным событием
        self._respawn_silver()

    def bind_dynamic_providers(self, visible_provider=None, event_provider=None):
        """GameplayScene вызывает это один раз после создания players и event_manager."""
        self._visible_provider = visible_provider
        self._event_provider = event_provider

    # --- Цикл ходов ---

    def on_cycle_complete(self):
        for pos in self.gold_deposits:
            self.gold_deposits[pos] += GOLD_CELL_YIELD

        self._cycles_since_silver_respawn += 1
        if self._cycles_since_silver_respawn >= SILVER_RESPAWN_CYCLES:
            self._cycles_since_silver_respawn = 0
            self._respawn_silver()

    def _respawn_silver(self):
        visible = self._visible_provider() if self._visible_provider else set()
        kept = {pos: amount for pos, amount in self.silver_cells.items() if pos in visible}

        free_cells = [pos for pos in self._collectible_free_cells() if pos not in kept]
        total_pool = len(free_cells) + len(kept)
        target_count = self._silver_cell_count(total_pool)
        to_place = max(0, min(target_count - len(kept), len(free_cells)))

        random.shuffle(free_cells)
        self.silver_cells = kept
        for pos in free_cells[:to_place]:
            self.silver_cells[pos] = random.randint(SILVER_PILE_MIN_VALUE, SILVER_PILE_MAX_VALUE)

    def _silver_cell_count(self, free_cells_count):
        density = SILVER_CELL_BASE_DENSITY + SILVER_CELL_DENSITY_PER_PLAYER * (self.player_count - 1)
        count = int(round(free_cells_count * density))
        count = max(MIN_SILVER_CELLS_ABSOLUTE, count)
        return min(count, free_cells_count)

    def _collectible_free_cells(self):
        field = self.field
        event_cells = self._event_provider() if self._event_provider else set()
        return [
            (x, y)
            for x in range(field.width)
            for y in range(field.height)
            if field.is_free(x, y)
            and (x, y) not in field.reserved_cells
            and (x, y) not in event_cells
        ]

    # --- Сбор ресурсов ---

    def collect_at(self, player):
        pos = (player.grid_x, player.grid_y)

        if pos in self.gold_deposits and self.gold_deposits[pos] > 0:
            amount = self.gold_deposits[pos]
            amount = EffectReader.modify_income(player, "gold", amount)
            player.gold += amount
            self.gold_deposits[pos] = 0

        if pos in self.silver_cells:
            amount = self.silver_cells.pop(pos)
            amount = EffectReader.modify_income(player, "silver", amount)
            player.silver += amount

    def collect_nearby_silver(self, player, radius):
        """Забирает всё серебро в радиусе — используется эффектом "магнит" (события "Коробка")."""
        px, py = player.grid_x, player.grid_y
        radius_sq = radius * radius
        nearby = [
            pos for pos in self.silver_cells
            if (pos[0] - px) ** 2 + (pos[1] - py) ** 2 <= radius_sq
        ]
        for pos in nearby:
            player.silver += self.silver_cells.pop(pos)

    def check_win(self, player):
        """True, если игрок стоит на финишной клетке и набрал достаточно золота и серебра."""
        if (player.grid_x, player.grid_y) != self.field.win_cell:
            return False
        return player.gold >= self.win_gold_required and player.silver >= self.win_silver_required

    def missing_requirements_message(self, player):
        if (player.grid_x, player.grid_y) != self.field.win_cell:
            return None

        gold_missing = max(0, self.win_gold_required - player.gold)
        silver_missing = max(0, self.win_silver_required - player.silver)
        if gold_missing <= 0 and silver_missing <= 0:
            return None

        parts = []
        if gold_missing > 0:
            parts.append(f"{gold_missing} золота")
        if silver_missing > 0:
            parts.append(f"{silver_missing} серебра")
        return "Недостаточно " + " и ".join(parts)