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

def run_race(seed, difficulty, size=22, limit_seconds=900.0):
    """Все 5 участников (включая «человека») управляются ботами.
    Возвращает (победитель, время, число событий у победителя)."""
    settings = GameSettings(map_width=size, map_height=size, bot_count=4,
                            bot_difficulty=difficulty, seed=seed)
    settings.clamp()
    world = GameWorld(settings, PALETTE, controller_factory=_factory)

    event_counts = {}
    def count_event(player, event, outcome):
        event_counts[player.color_key] = event_counts.get(player.color_key, 0) + 1
    world.on_bot_event = count_event

    for player in world.players:
        if player.controller is None:
            player.is_bot = True
            player.controller = _factory(world, player, difficulty, 0, len(world.players))
    while world.winner is None and world.clock.match_time < limit_seconds:
        world.update(0.05)
    events = event_counts.get(world.winner.color_key, 0) if world.winner else 0
    return world.winner, world.clock.match_time, events

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

    print("--- Гонки ботов, карта 22x22 ---")
    for difficulty in ("easy", "normal", "hard"):
        for seed in (1, 2, 3):
            winner, seconds, events = run_race(seed, difficulty)
            if winner is None:
                print(f"{difficulty:6} seed={seed}: никто (лимит времени)")
                continue
            print(f"{difficulty:6} seed={seed}: {winner.color_key}, {seconds:.0f} с, "
                  f"золото={winner.gold}, серебро={winner.silver}, событий={events}")

if __name__ == "__main__":
    main()