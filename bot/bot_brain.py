import random
from dataclasses import dataclass

from bot.bot_knowledge import BotKnowledge
from bot.bot_valuation import event_value, risk_adjusted
from game.game_config import GOLD_CELL_YIELD, GOLD_YIELD_INTERVAL

DIST_OFFSET = 3.0          # сглаживает «ценность / расстояние» вблизи цели
MIN_VALUE = 3.0            # цели дешевле этого бот игнорирует
EXPLORE_VALUE = 8.0        # условная ценность исследования границы тумана
EXPLORE_FINISH_BIAS = 0.4  # исследование в сторону финиша чуть привлекательнее
FINISH_SCORE = 1000.0
HYSTERESIS = 1.3           # новая цель должна быть лучше текущей минимум во столько раз
MISTAKE_POOL = 3           # ошибка выбирает 2-ю или 3-ю по качеству цель
SURPLUS_FACTOR = 0.2       # ценность ресурса сверх нужного для победы
GOLD_BUFFER = 3            # запас золота сверх требования (на случай потерь в событиях)
SILVER_BUFFER = 30
UNREACHABLE_BLACKLIST = 5.0
WANDER_MIN, WANDER_MAX = 2, 6
DIRECTIONS = ((-1, 0), (1, 0), (0, -1), (0, 1))


@dataclass
class Target:
    kind: str     # "finish" | "gold" | "silver" | "event" | "explore" | "wander"
    pos: tuple
    score: float


class BotBrain:
    """Выбор цели и построение пути. Не знает про таймеры: их ведёт BotController."""

    def __init__(self, world, player, profile):
        self.world = world
        self.player = player
        self.profile = profile
        self.knowledge = BotKnowledge()
        self.goal = None
        self._blacklist = {}   # {клетка: до какого времени игнорировать}

    # --- Публичный интерфейс ---

    def plan(self, now):
        """Возвращает (цель, путь от anchor_cell) либо None, если идти некуда."""
        world, player = self.world, self.player
        field = world.field

        self.knowledge.observe(world, player, now)
        self._purge_blacklist(now)

        start = player.anchor_cell
        known = player.known_cells
        avoid = self._cells_to_avoid()

        dist, parents = field.optimistic_tree(start, known, avoid)
        candidates = self._build_candidates(dist, known, now)
        if not candidates and avoid:
            # Обход плохих событий отрезал все цели - идём напрямую.
            dist, parents = field.optimistic_tree(start, known, None)
            candidates = self._build_candidates(dist, known, now)
        if not candidates:
            candidates = self._fallback_candidates(dist, now)
        if not candidates:
            self.goal = None
            return None

        goal = self._select(candidates, start)
        path = field.path_from_tree(parents, start, goal.pos)
        if goal.pos != start and not path:
            self.blacklist(goal.pos, UNREACHABLE_BLACKLIST, now)
            self.goal = None
            return None
        return goal, path

    def abandon_goal(self, now, seconds):
        """Вызывается контроллером при застревании."""
        if self.goal is not None:
            self.blacklist(self.goal.pos, seconds, now)
        self.goal = None

    def blacklist(self, pos, seconds, now):
        self._blacklist[pos] = now + seconds

    # --- Кандидаты ---

    def _build_candidates(self, dist, known, now):
        world, player, profile = self.world, self.player, self.profile
        field = world.field
        rm = world.resource_manager
        candidates = {}

        if self._ready():
            if field.win_cell in dist:
                candidates[field.win_cell] = Target("finish", field.win_cell, FINISH_SCORE)
            return candidates

        speed = max(1.0, player.base_speed)
        need_gold = max(0, rm.win_gold_required - player.gold)
        need_silver = max(0, rm.win_silver_required - player.silver)
        gold_value = self._gold_value()

        for pos in field.gold_cell_positions:
            d = dist.get(pos)
            if not d or self._blacklisted(pos, now):   # None (недостижима) или 0 (стоим на ней)
                continue
            eta = d / speed
            expected = rm.gold_deposits.get(pos, 0) + GOLD_CELL_YIELD * eta / GOLD_YIELD_INTERVAL
            value = self._capped(expected, need_gold, GOLD_BUFFER) * gold_value * profile.gold_weight
            self._offer(candidates, "gold", pos, value, d)

        for pos, (amount, _seen) in self.knowledge.silver.items():
            d = dist.get(pos)
            if not d or self._blacklisted(pos, now):
                continue
            value = self._capped(amount, need_silver, SILVER_BUFFER) * profile.silver_weight
            self._offer(candidates, "silver", pos, value, d)

        for pos, (definition, _seen) in self.knowledge.events.items():
            d = dist.get(pos)
            if not d or self._blacklisted(pos, now):
                continue
            self._offer(candidates, "event", pos, self._event_score(definition), d)

        self._offer_frontier(candidates, dist, known, now)
        return candidates

    def _fallback_candidates(self, dist, now):
        """Нечего собирать и нечего исследовать: ждём золото на другой клетке или бродим."""
        rm = self.world.resource_manager
        result = {}
        for pos in self.world.field.gold_cell_positions:
            d = dist.get(pos)
            if d and not self._blacklisted(pos, now):
                result[pos] = Target("gold", pos, float(rm.gold_deposits.get(pos, 0)) / (d + DIST_OFFSET))
        if result:
            return result
        near = [cell for cell, d in dist.items() if WANDER_MIN <= d <= WANDER_MAX]
        if near:
            cell = random.choice(near)
            result[cell] = Target("wander", cell, 0.0)
        return result

    def _offer_frontier(self, candidates, dist, known, now):
        field = self.world.field
        fx, fy = field.win_cell
        span = field.width + field.height
        best = None
        for cell, d in dist.items():
            if d == 0 or cell not in known or self._blacklisted(cell, now):
                continue
            x, y = cell
            if not self._has_unknown_neighbor(x, y, known):
                continue
            progress = 1.0 - (abs(fx - x) + abs(fy - y)) / span
            score = EXPLORE_VALUE * (1.0 + EXPLORE_FINISH_BIAS * progress) / (d + DIST_OFFSET)
            if best is None or score > best.score:
                best = Target("explore", cell, score)
        if best is not None:
            candidates.setdefault(best.pos, best)

    def _has_unknown_neighbor(self, x, y, known):
        field = self.world.field
        for dx, dy in DIRECTIONS:
            nx, ny = x + dx, y + dy
            if field.in_bounds(nx, ny) and (nx, ny) not in known:
                return True
        return False

    @staticmethod
    def _offer(candidates, kind, pos, value, distance):
        if value < MIN_VALUE:
            return
        score = value / (distance + DIST_OFFSET)
        existing = candidates.get(pos)
        if existing is None or score > existing.score:
            candidates[pos] = Target(kind, pos, score)

    # --- Выбор ---

    def _select(self, candidates, start):
        ranked = sorted(candidates.values(), key=lambda t: t.score, reverse=True)
        best = ranked[0]

        current = self.goal
        if current is not None and current.pos != start:
            same = candidates.get(current.pos)
            if same is not None and same.kind == current.kind and same.score * HYSTERESIS >= best.score:
                self.goal = same
                return same

        choice = best
        if len(ranked) > 1 and random.random() < self.profile.mistake_chance:
            choice = random.choice(ranked[1:MISTAKE_POOL])
        self.goal = choice
        return choice

    # --- Вспомогательное ---

    def _ready(self):
        rm = self.world.resource_manager
        return (self.player.gold >= rm.win_gold_required
                and self.player.silver >= rm.win_silver_required)

    def _gold_value(self):
        rm = self.world.resource_manager
        return rm.win_silver_required / max(1, rm.win_gold_required)

    @staticmethod
    def _capped(amount, need, buffer):
        if need > 0:
            return min(amount, need + buffer)
        return amount * SURPLUS_FACTOR

    def _event_score(self, definition):
        value = event_value(definition, self.profile, self._gold_value())
        return risk_adjusted(value, self.profile.event_risk)

    def _cells_to_avoid(self):
        return {
            pos for pos, (definition, _seen) in self.knowledge.events.items()
            if self._event_score(definition) < 0
        }

    def _blacklisted(self, pos, now):
        return self._blacklist.get(pos, 0.0) > now

    def _purge_blacklist(self, now):
        for pos in [p for p, until in self._blacklist.items() if until <= now]:
            del self._blacklist[pos]