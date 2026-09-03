from game.event_manager import EventDefinition, EventOutcome
from game.image_manager import IMAGES_DIR

class BagEvent(EventDefinition):
    id = "bag"
    icon_file = "bag.png"
    prompt_text = (
        "На земле лежит потрёпанный оранжевый мешок, туго завязанный верёвкой. "
        "Заглянуть внутрь?"
    )
    outcomes = {
        1: EventOutcome(
            "Едва вы развязали узел, как из мешка выскочил разъярённый барсук "
            "и вцепился вам в ногу!",
            silver_delta=-50, moves_delta=-7,
        ),
        2: EventOutcome(
            "Узел оказался слишком тугим — провозились с ним впустую.",
            moves_delta=-2,
        ),
        3: EventOutcome(
            "Внутри — горстка мелкой монеты.",
            silver_delta=10,
        ),
        4: EventOutcome(
            "Неплохой улов — кто-то обронил здесь кошель.",
            silver_delta=20, moves_delta=2,
        ),
        5: EventOutcome(
            "Среди тряпья блеснули золотые монеты.",
            gold_delta=15, moves_delta=2,
        ),
        6: EventOutcome(
            "Это оказался тайник контрабандиста!",
            gold_delta=20, silver_delta=50, moves_delta=4,
        ),
    }

    @property
    def icon_dir(self):
        return IMAGES_DIR

EVENT = BagEvent