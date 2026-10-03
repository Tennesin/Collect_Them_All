from game.event_manager import EventDefinition, EventOutcome
from game.effects.effects import Effect, remove_warning_effects
from game.effects.speed_effects import StunEffect, HasteEffect

class ConfusionEffect(Effect):
    """Эффект события 'Аптечка' (ШИЗА): обзор и скорость игрока падают."""

    label = "Шиза"
    warning = True
    DURATION_SECONDS = 10.0
    VISION_RADIUS = 3
    SPEED_MULTIPLIER = 0.6

    vision_radius_override = VISION_RADIUS
    speed_multiplier = SPEED_MULTIPLIER

class SupermanEffect(Effect):
    """Эффект события 'Аптечка' (СУПЕРМЭН): полная видимость карты и ускорение."""

    label = "Супермэн"
    DURATION_SECONDS = 10.0
    SPEED_MULTIPLIER = 1.5

    full_map_vision = True
    speed_multiplier = SPEED_MULTIPLIER

    def on_apply(self, player):
        """Супермэн лечит от всего плохого разом."""
        remove_warning_effects(player)

class MedicineBagEvent(EventDefinition):
    id = "medicine_bag"
    icon_file = "medicine_bag.png"
    prompt_text = (
        "На пути лежала заброшенная аптечка, внутри которой нашлись странные "
        "медикаменты. Желаете попробовать их?"
    )

    outcomes = {
        1: EventOutcome(
            "ШИЗА: препарат оказался просроченным — сознание помутилось, обзор "
            "и подвижность резко упали.",
            silver_delta=-20,
            effect_factory=lambda: ConfusionEffect(ConfusionEffect.DURATION_SECONDS),
        ),
        2: EventOutcome(
            "Рвота: организм не принял находку — пришлось пережидать, приходя в себя.",
            effect_factory=lambda: StunEffect(2.5),
        ),
        3: EventOutcome(
            "Ничего: препарат оказался бесполезным, но на дне аптечки нашлась мелочь.",
            silver_delta=5,
        ),
        4: EventOutcome(
            "Усилитель: неизвестное средство придало бодрости и сил на дорогу.",
            effect_factory=lambda: HasteEffect(1.5, 5.0),
        ),
        5: EventOutcome(
            "Полная свежесть: препарат снял всю усталость и все дурные последствия.",
            effect_factory=lambda: HasteEffect(1.25, 4.0, cleanses=True),
        ),
        6: EventOutcome(
            "СУПЕРМЭН: чудо-состав пробудил нечеловеческие силы — вы видите всю карту "
            "и несётесь намного быстрее обычного!",
            effect_factory=lambda: SupermanEffect(SupermanEffect.DURATION_SECONDS),
        ),
    }

EVENT = MedicineBagEvent