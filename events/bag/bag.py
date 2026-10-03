from game.event_manager import EventDefinition, EventOutcome
from game.effects.speed_effects import SlowEffect, HasteEffect, StunEffect

class BagEvent(EventDefinition):
    id = "bag"
    title = "Мешок"
    icon_file = "bag.png"
    prompt_text = (
        "На земле лежит потрёпанный оранжевый мешок, туго завязанный верёвкой. "
        "Заглянуть внутрь?"
    )
    outcomes = {
        1: EventOutcome(
            "Едва вы развязали узел, как из мешка выскочил разъярённый барсук "
            "и вцепился вам в ногу!",
            silver_delta=-50,
            effect_factory=lambda: SlowEffect(0.5, 6.0),
        ),
        2: EventOutcome(
            "Узел оказался слишком тугим — вы застряли над ним, потеряв пару секунд.",
            effect_factory=lambda: StunEffect(1.5),
        ),
        3: EventOutcome(
            "Внутри — горстка мелкой монеты.",
            silver_delta=10,
        ),
        4: EventOutcome(
            "Неплохой улов — кто-то обронил здесь кошель. Удача придала вам прыти.",
            silver_delta=20,
            effect_factory=lambda: HasteEffect(1.25, 3.0),
        ),
        5: EventOutcome(
            "Среди тряпья блеснули золотые монеты. Радость придала вам сил.",
            gold_delta=15,
            effect_factory=lambda: HasteEffect(1.25, 3.0),
        ),
        6: EventOutcome(
            "Это оказался тайник контрабандиста!",
            gold_delta=20, silver_delta=50,
            effect_factory=lambda: HasteEffect(1.5, 5.0),
        ),
    }

EVENT = BagEvent