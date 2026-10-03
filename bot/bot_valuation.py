"""Оценка ценности событий для бота. Всё считается в «серебряных эквивалентах»."""
from game.game_config import PLAYER_BASE_SPEED

SILVER_PER_CELL = 1.5        # сколько серебра «стоит» одна лишняя пройденная клетка
DISPLACEMENT_PENALTY = 3.0   # штраф за каждую клетку случайного смещения
VISION_LOSS_PENALTY = 10.0
FULL_MAP_BONUS = 15.0
PHANTOM_BONUS = 5.0
WARNING_SECOND_PENALTY = 1.5  # штраф за секунду «проклятия» без влияния на скорость

_event_cache = {}  # {id события: (среднее золото, среднее серебро, средняя «прочая» ценность)}

def estimate_effect_value(effect):
    """Грубая оценка эффекта по его публичным атрибутам (без привязки к конкретным событиям)."""
    multiplier = getattr(effect, "speed_multiplier", 1.0)
    duration = effect.duration_seconds
    value = (multiplier - 1.0) * duration * PLAYER_BASE_SPEED * SILVER_PER_CELL

    if getattr(effect, "full_map_vision", False):
        value += FULL_MAP_BONUS
    override = getattr(effect, "vision_radius_override", None)
    if override is not None:
        value -= VISION_LOSS_PENALTY
    if getattr(effect, "ignores_obstacles", False):
        value += PHANTOM_BONUS
    if getattr(effect, "warning", False) and multiplier >= 1.0 and override is None:
        value -= duration * WARNING_SECOND_PENALTY  # проклятия и прочие вредные эффекты
    return value


def event_averages(definition):
    """Средний исход шести равновероятных граней. Считается один раз на событие."""
    cached = _event_cache.get(definition.id)
    if cached is not None:
        return cached

    gold = silver = other = 0.0
    for roll in range(1, 7):
        outcome = definition.get_outcome(roll)
        gold += outcome.gold_delta
        silver += outcome.silver_delta
        other -= outcome.displacement_cells * DISPLACEMENT_PENALTY
        if outcome.effect_factory is not None:
            other += estimate_effect_value(outcome.effect_factory())
    result = (gold / 6, silver / 6, other / 6)
    _event_cache[definition.id] = result
    return result


def event_value(definition, profile, gold_value):
    """gold_value: сколько серебра стоит одна единица золота."""
    avg_gold, avg_silver, avg_other = event_averages(definition)
    return (avg_gold * gold_value * profile.gold_weight
            + avg_silver * profile.silver_weight
            + avg_other)


def risk_adjusted(value, event_risk):
    """Рисковый бот (event_risk -> 1) завышает выигрыш и занижает потери."""
    if value >= 0:
        return value * (0.5 + event_risk)
    return value * (1.5 - event_risk)