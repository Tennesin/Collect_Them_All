import random
from game.game_config import (
    GOLD_CELL_YIELD, MIN_SILVER_CELLS, MAX_SILVER_CELLS,
    SILVER_CELL_VALUE, SILVER_RESPAWN_CYCLES,
    WIN_GOLD_REQUIRED, WIN_SILVER_REQUIRED,
)


class ResourceManager:
    """Владеет ДИНАМИЧЕСКИМ состоянием ресурсов: сколько золота накопилось
    в каждой золотой клетке и где прямо сейчас лежит серебро. Field хранит
    только неизменную геометрию (где стоят золотые клетки) — сколько там
    золота в данный момент, знает только этот класс. Также умеет проверять
    условие победы."""

    def __init__(self, field):
        self.field = field
        self.gold_deposits = {pos: 0 for pos in field.gold_cell_positions}
        self.silver_cells = {}
        self._cycles_since_silver_respawn = 0
        self._respawn_silver()

    # --- Цикл ходов ---

    def on_cycle_complete(self):
        """Вызывается TurnManager'ом, когда очередь снова доходит до первого
        игрока — то есть все игроки уже сходили по разу в этом цикле."""
        for pos in self.gold_deposits:
            self.gold_deposits[pos] += GOLD_CELL_YIELD

        self._cycles_since_silver_respawn += 1
        if self._cycles_since_silver_respawn >= SILVER_RESPAWN_CYCLES:
            self._cycles_since_silver_respawn = 0
            self._respawn_silver()

    def _respawn_silver(self):
        self.silver_cells.clear()
        count = random.randint(MIN_SILVER_CELLS, MAX_SILVER_CELLS)
        free_cells = self._collectible_free_cells()
        random.shuffle(free_cells)
        for pos in free_cells[:count]:
            self.silver_cells[pos] = SILVER_CELL_VALUE

    def _collectible_free_cells(self):
        """Все проходимые клетки, кроме зарезервированных (золотые клетки,
        победная клетка) — серебро туда не кладём, чтобы не путать со
        стационарными ресурсами."""
        field = self.field
        return [
            (x, y)
            for x in range(field.width)
            for y in range(field.height)
            if field.is_free(x, y) and (x, y) not in field.reserved_cells
        ]

    # --- Сбор ресурсов ---

    def collect_at(self, player):
        """Вызывать при каждом входе игрока в новую клетку — собирает
        золото/серебро, если оно там есть."""
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