from game.event_manager import EventDefinition, EventOutcome
from game.effects.speed_effects import SlowEffect, HasteEffect

class InjuredEvent(EventDefinition):
    id = "injured"
    icon_file = "injured.png"
    prompt_text = (
        "Вы наткнулись на раненого человека, который просит вас помочь ему. "
        "Вы хотите помочь раненому?"
    )
    outcomes = {
        1: EventOutcome(
            "Раненый оказался грабителем, который притворялся больным для окружающих. "
            "Вы попали в его ловушку, а удар по голове сбил вам темп.",
            gold_delta=-10, silver_delta=-60,
            effect_factory=lambda: SlowEffect(0.75, 4.0),
        ),
        2: EventOutcome(
            "Раненый после оказания помощи не сдержал слово и сбежал от вас.",
            silver_delta=-25,
        ),
        3: EventOutcome(
            "Раненый поспешил уйти сразу, дав вам минимальную компенсацию за задержку.",
            silver_delta=20,
            effect_factory=lambda: HasteEffect(1.25, 3.0),
        ),
        4: EventOutcome(
            "Раненый поспешил уйти сразу, дав вам минимальную компенсацию за задержку.",
            silver_delta=20,
            effect_factory=lambda: HasteEffect(1.25, 3.0),
        ),
        5: EventOutcome(
            "Раненый оплатил за вашу услугу и поблагодарил перед уходом.",
            gold_delta=5, silver_delta=35,
        ),
        6: EventOutcome(
            "Раненый оказался священником, который благословил вас своей силой "
            "за оказанную ему помощь.",
            gold_delta=15,
            effect_factory=lambda: HasteEffect(1.5, 6.0),
        ),
    }

EVENT = InjuredEvent