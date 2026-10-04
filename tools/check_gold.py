import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from game.game_config import GameSettings, max_gold_cells_for_map
from game.world import GameWorld
from settings import PLAYER_COLORS, PLAYER_COLOR_ORDER

PALETTE = [(key, PLAYER_COLORS[key]) for key in PLAYER_COLOR_ORDER]
SIZES = (11, 12, 13, 14, 15, 18, 22, 30, 41, 50)


def main():
    checked = failed = 0
    for w in SIZES:
        for h in SIZES:
            cap = max_gold_cells_for_map(w, h)
            for seed in range(3):
                settings = GameSettings(map_width=w, map_height=h, gold_cell_count=cap, seed=seed)
                settings.clamp()
                world = GameWorld(settings, PALETTE)
                placed = len(world.field.gold_cell_positions)
                ok = placed == settings.gold_cell_count and world.field.is_connected()
                checked += 1
                if not ok:
                    failed += 1
                    print(f"ПРОВАЛ {w}x{h} seed={seed}: запрошено {settings.gold_cell_count}, поставлено {placed}")
    print(f"Проверено карт: {checked}, провалов: {failed}")


if __name__ == "__main__":
    main()