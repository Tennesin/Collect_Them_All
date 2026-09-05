from game.event_manager import EventDefinition, EventOutcome
from game.effects import Effect

class ConfusionEffect(Effect):
    """Эффект события 'Аптечка' (ШИЗА): обзор и подвижность игрока падают до минимума."""

    label = "Шиза"
    warning = True
    DURATION_TURNS = 3
    RADIUS = 3

    vision_radius_override = RADIUS
    max_moves_override = RADIUS

class SupermanEffect(Effect):
    """Эффект события 'Аптечка' (СУПЕРМЭН): полная видимость карты и увеличенный лимит шагов."""

    label = "Супермэн"
    DURATION_TURNS = 3
    MOVES_MULTIPLIER = 1.5

    full_map_vision = True
    max_moves_multiplier = MOVES_MULTIPLIER


class MedicineBagEvent(EventDefinition):
    id = "medicine_bag"
    icon_file = "medicine_bag.png"
    prompt_text = (
        "На пути лежала заброшенная аптечка, внутри которой нашлись странные "
        "медикаменты. Желаете попробовать их?"
    )

    REFILL_EXTRA_CAP = 5  # см. исход 5 — насколько можно выйти за обычный лимит шагов

    outcomes = {
        1: EventOutcome(
            "ШИЗА: препарат оказался просроченным — сознание помутилось, обзор "
            "и подвижность резко упали.",
            silver_delta=-20,
            effect_factory=lambda: ConfusionEffect(ConfusionEffect.DURATION_TURNS),
        ),
        2: EventOutcome(
            "Рвота: организм не принял находку — пришлось потратить время, приходя в себя.",
            moves_delta=-4,
        ),
        3: EventOutcome(
            "Ничего: препарат оказался бесполезным, но на дне аптечки нашлась мелочь.",
            silver_delta=5,
        ),
        4: EventOutcome(
            "Усилитель: неизвестное средство придало бодрости и сил на дорогу.",
            moves_delta=4,
        ),
        5: EventOutcome(
            "Полная свежесть: препарат снял всю усталость без остатка.",
            refill_moves=True, refill_extra_cap=REFILL_EXTRA_CAP,
        ),
        6: EventOutcome(
            "СУПЕРМЭН: чудо-состав пробудил нечеловеческие силы — вы видите всю карту "
            "и способны пройти намного больше обычного!",
            effect_factory=lambda: SupermanEffect(SupermanEffect.DURATION_TURNS),
        ),
    }

EVENT = MedicineBagEvent