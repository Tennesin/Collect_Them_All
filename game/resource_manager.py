import random
from game.game_config import (
    GOLD_CELL_YIELD,
    SILVER_CELL_BASE_DENSITY, SILVER_CELL_DENSITY_PER_PLAYER, MIN_SILVER_CELLS_ABSOLUTE,
    SILVER_PILE_MIN_VALUE, SILVER_PILE_MAX_VALUE, SILVER_RESPAWN_CYCLES,
    WIN_GOLD_REQUIRED, WIN_SILVER_REQUIRED,
)

class ResourceManager:

    def __init__(self, field, player_count):
        self.field = field
        self.player_count = player_count
        self.gold_deposits = {pos: 0 for pos in field.gold_cell_positions}
        self.silver_cells = {}
        self._cycles_since_silver_respawn = 0
        self._respawn_silver()

    # --- Цикл ходов ---

    def on_cycle_complete(self):
        for pos in self.gold_deposits:
            self.gold_deposits[pos] += GOLD_CELL_YIELD

        self._cycles_since_silver_respawn += 1
        if self._cycles_since_silver_respawn >= SILVER_RESPAWN_CYCLES:
            self._cycles_since_silver_respawn = 0
            self._respawn_silver()

    def _respawn_silver(self):
        self.silver_cells.clear()
        free_cells = self._collectible_free_cells()
        count = self._silver_cell_count(len(free_cells))
        random.shuffle(free_cells)
        for pos in free_cells[:count]:
            self.silver_cells[pos] = random.randint(SILVER_PILE_MIN_VALUE, SILVER_PILE_MAX_VALUE)

    def _silver_cell_count(self, free_cells_count):
        density = SILVER_CELL_BASE_DENSITY + SILVER_CELL_DENSITY_PER_PLAYER * (self.player_count - 1)
        count = int(round(free_cells_count * density))
        count = max(MIN_SILVER_CELLS_ABSOLUTE, count)
        return min(count, free_cells_count)

    def _collectible_free_cells(self):
        field = self.field
        return [
            (x, y)
            for x in range(field.width)
            for y in range(field.height)
            if field.is_free(x, y) and (x, y) not in field.reserved_cells
        ]

    # --- Сбор ресурсов ---

    def collect_at(self, player):
        pos = (player.grid_x, player.grid_y)

        if pos in self.gold_deposits and self.gold_deposits[pos] > 0:
            player.gold += self.gold_deposits[pos]
            self.gold_deposits[pos] = 0

        if pos in self.silver_cells:
            player.silver += self.silver_cells.pop(pos)

    def check_win(self, player):
        """True, если игрок прямо сейчас выполняет условие победы."""
        pos = (player.grid_x, player.grid_y)
        return (
            pos == self.field.win_cell
            and player.gold >= WIN_GOLD_REQUIRED
            and player.silver >= WIN_SILVER_REQUIRED
        )

    def missing_requirements_message(self, player):
        if (player.grid_x, player.grid_y) != self.field.win_cell:
            return None

        gold_missing = max(0, WIN_GOLD_REQUIRED - player.gold)
        silver_missing = max(0, WIN_SILVER_REQUIRED - player.silver)
        if gold_missing <= 0 and silver_missing <= 0:
            return None

        parts = []
        if gold_missing > 0:
            parts.append(f"{gold_missing} золота")
        if silver_missing > 0:
            parts.append(f"{silver_missing} серебра")
        return "Недостаточно " + " и ".join(parts)