"""Геометрия золотых коробов: где они могут стоять и сколько их вмещает карта.
Модуль работает только с числами и ничего не знает про Field и настройки."""
import random
from functools import lru_cache

from game.field import start_cell_for, win_cell_for

RANDOM_ATTEMPTS = 40   # сколько раз пробуем «живую» расстановку, прежде чем взять решётку

def center_distance(radius, buffer):
    """Минимальное расстояние между центрами двух коробов (по большей из осей).
    Отступ между соседями общий: короб + 1 свободная клетка + короб."""
    return 2 * radius + 1 + buffer

@lru_cache(maxsize=None)
def candidate_centers(width, height, radius, buffer):
    """Все центры, где короб помещается с отступом до краёв карты
    и не подходит вплотную к старту и финишу."""
    margin = radius + buffer
    keep_out = (start_cell_for(width, height), win_cell_for(width, height))
    centers = []
    for x in range(margin, width - margin):
        for y in range(margin, height - margin):
            near_keep_out = any(
                abs(x - kx) <= margin and abs(y - ky) <= margin for kx, ky in keep_out
            )
            if not near_keep_out:
                centers.append((x, y))
    return tuple(centers)

@lru_cache(maxsize=None)
def lattice_layouts(width, height, radius, buffer):
    """Регулярные решётки со всеми возможными сдвигами. Каждая - готовая
    расстановка, которая гарантированно удовлетворяет правилам расстояния."""
    margin = radius + buffer
    pitch = center_distance(radius, buffer)
    allowed = set(candidate_centers(width, height, radius, buffer))
    layouts = []
    for ox in range(pitch):
        for oy in range(pitch):
            slots = tuple(
                (x, y)
                for x in range(margin + ox, width - margin, pitch)
                for y in range(margin + oy, height - margin, pitch)
                if (x, y) in allowed
            )
            layouts.append(slots)
    return tuple(layouts)

@lru_cache(maxsize=None)
def gold_capacity(width, height, radius, buffer):
    """Сколько коробов карта вмещает ГАРАНТИРОВАННО (лучшая из решёток)."""
    return max((len(slots) for slots in lattice_layouts(width, height, radius, buffer)), default=0)

def plan_layout(width, height, count, radius, buffer):
    """Центры коробов. Если count не больше вместимости, вернёт ровно count центров."""
    count = min(count, gold_capacity(width, height, radius, buffer))
    if count <= 0:
        return []

    pitch = center_distance(radius, buffer)
    if count < gold_capacity(width, height, radius, buffer):
        candidates = candidate_centers(width, height, radius, buffer)
        for _ in range(RANDOM_ATTEMPTS):
            chosen = _random_greedy(candidates, count, pitch)
            if len(chosen) == count:
                return chosen

    fitting = [slots for slots in lattice_layouts(width, height, radius, buffer) if len(slots) >= count]
    return random.sample(random.choice(fitting), count)

def _random_greedy(candidates, count, pitch):
    pool = list(candidates)
    random.shuffle(pool)
    chosen = []
    for x, y in pool:
        if all(max(abs(x - cx), abs(y - cy)) >= pitch for cx, cy in chosen):
            chosen.append((x, y))
            if len(chosen) == count:
                break
    return chosen