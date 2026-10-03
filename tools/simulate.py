import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bot.bot_factory import create_bot_controller as _factory
from game.game_config import GameSettings
from game.world import GameWorld
from settings import PLAYER_COLORS, PLAYER_COLOR_ORDER

PALETTE = [(key, PLAYER_COLORS[key]) for key in PLAYER_COLOR_ORDER]

def percentile(sorted_values, p):
    if not sorted_values:
        return 0.0
    index = round((len(sorted_values) - 1) * p)
    return sorted_values[index]


def run_match(seed, difficulty, size, bots=4, limit_seconds=900.0):
    """Все участники (включая «человека») управляются ботами одной сложности."""
    settings = GameSettings(map_width=size, map_height=size, bot_count=bots,
                            bot_difficulty=difficulty, seed=seed)
    settings.clamp()
    world = GameWorld(settings, PALETTE, controller_factory=_factory)

    event_gold = {}
    event_silver = {}
    event_count = {}

    def on_event(player, event, outcome):
        key = player.color_key
        event_gold[key] = event_gold.get(key, 0) + outcome.gold_delta
        event_silver[key] = event_silver.get(key, 0) + outcome.silver_delta
        event_count[key] = event_count.get(key, 0) + 1

    world.on_bot_event = on_event

    for player in world.players:
        if player.controller is None:
            player.is_bot = True
            player.controller = _factory(world, player, difficulty, 0, len(world.players))

    while world.winner is None and world.clock.match_time < limit_seconds:
        world.update(0.05)

    winner = world.winner
    if winner is None:
        return None
    key = winner.color_key
    return {
        "time": world.clock.match_time,
        "place": world.players.index(winner),
        "gold": winner.gold,
        "silver": winner.silver,
        "events": event_count.get(key, 0),
        "event_gold": event_gold.get(key, 0),
        "event_silver": event_silver.get(key, 0),
    }


def report(label, results, total):
    wins = [r for r in results if r is not None]
    timeouts = total - len(wins)
    print(f"\n=== {label}: партий {total}, без победителя {timeouts} ===")
    if not wins:
        return
    times = sorted(r["time"] for r in wins)
    mean = lambda key: sum(r[key] for r in wins) / len(wins)
    print(f"Время победы, с: p10={percentile(times, 0.1):.0f}  "
          f"медиана={percentile(times, 0.5):.0f}  p90={percentile(times, 0.9):.0f}")
    print(f"У победителя в среднем: золото={mean('gold'):.1f} "
          f"(из событий {mean('event_gold'):+.1f}), "
          f"серебро={mean('silver'):.0f} (из событий {mean('event_silver'):+.0f}), "
          f"событий={mean('events'):.1f}")
    places = {}
    for r in wins:
        places[r["place"]] = places.get(r["place"], 0) + 1
    shares = ", ".join(f"#{p}: {places[p] * 100 // len(wins)}%" for p in sorted(places))
    print(f"Доля побед по месту в списке игроков: {shares}")


def main():
    count = int(sys.argv[1]) if len(sys.argv) > 1 else 30
    size = int(sys.argv[2]) if len(sys.argv) > 2 else 22
    print(f"Партий на сложность: {count}, карта {size}x{size}, 5 участников")
    for difficulty in ("easy", "normal", "hard"):
        results = [run_match(seed, difficulty, size) for seed in range(1, count + 1)]
        report(difficulty, results, count)

if __name__ == "__main__":
    main()