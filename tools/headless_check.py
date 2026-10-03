import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bot.bot_factory import create_bot_controller as _factory
from game.game_config import GameSettings
from game.world import GameWorld
from settings import PLAYER_COLORS, PLAYER_COLOR_ORDER

PALETTE = [(key, PLAYER_COLORS[key]) for key in PLAYER_COLOR_ORDER]


def build_world(seed):
    settings = GameSettings(map_width=22, map_height=22, bot_count=4, bot_difficulty="hard", seed=seed)
    settings.clamp()
    return GameWorld(settings, PALETTE, controller_factory=_factory)


def main():
    started = time.perf_counter()
    world = build_world(seed=1)
    print(f"Создание мира: {time.perf_counter() - started:.3f} с")

    twin = build_world(seed=1)
    same = (world.field.obstacle_grid == twin.field.obstacle_grid
            and world.field.gold_cell_positions == twin.field.gold_cell_positions)
    print("Одинаковый seed -> одинаковая карта:", same)

    dt = 0.05
    frames = 20 * 60   # 60 секунд игрового времени
    started = time.perf_counter()
    for _ in range(frames):
        world.update(dt)
    elapsed = time.perf_counter() - started
    print(f"{frames} кадров мира: {elapsed:.3f} с ({elapsed / frames * 1000:.3f} мс на кадр)")
    print("Игроков:", len(world.players), "| ботов:", sum(p.is_bot for p in world.players))
    print("pygame загружен:", "pygame" in sys.modules)
    print("Гонки и баланс: python tools/simulate.py [партий] [размер карты]")


if __name__ == "__main__":
    main()