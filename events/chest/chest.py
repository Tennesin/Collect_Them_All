from game.event_manager import EventDefinition, EventOutcome
from game.image_manager import IMAGES_DIR
from game.game_config import EFFECT_HALF_INCOME, CHEST_CURSE_DURATION_TURNS

class ChestEvent(EventDefinition):
    id = "chest"
    icon_file = "chest.png"
    prompt_text = (
        "Перед вами стоит старый сундук — крышка слегка подрагивает, будто он "
        "дышит. Кажется, он ждёт, когда вы решитесь его открыть."
    )
    outcomes = {
        1: EventOutcome(
            "Сундук оскалился деревянной пастью — внутри прятался настоящий "
            "демон! Он проклял вашу удачу.",
            gold_delta=-15,
            effect_type=EFFECT_HALF_INCOME,
            effect_duration=CHEST_CURSE_DURATION_TURNS,
        ),
        2: EventOutcome(
            "Сундук недовольно заскрипел и вытряс на вас пыль вместо сокровищ.",
            silver_delta=-35, moves_delta=-2,
        ),
        3: EventOutcome(
            "Сундук нехотя выдал горстку монет.",
            silver_delta=15,
        ),
        4: EventOutcome(
            "Сундук нехотя выдал горстку монет.",
            silver_delta=15,
        ),
        5: EventOutcome(
            "Похоже, вы ему приглянулись — сундук выдал щедрую пригоршню серебра.",
            silver_delta=35, moves_delta=3,
        ),
        6: EventOutcome(
            "Сундук довольно заурчал и вывалил перед вами настоящий подарок!",
            gold_delta=20, moves_delta=7,
        ),
    }

    @property
    def icon_dir(self):
        return IMAGES_DIR

EVENT = ChestEvent