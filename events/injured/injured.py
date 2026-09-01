from game.event_manager import EventDefinition, EventOutcome

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
            "Вы попали в его ловушку.",
            gold_delta=-10, silver_delta=-60, moves_delta=-3,
        ),
        2: EventOutcome(
            "Раненый после оказания помощи не сдержал слово и сбежал от вас.",
            silver_delta=-25,
        ),
        3: EventOutcome(
            "Раненый поспешил уйти сразу, дав вам минимальную компенсацию за задержку.",
            silver_delta=20, moves_delta=2,
        ),
        4: EventOutcome(
            "Раненый поспешил уйти сразу, дав вам минимальную компенсацию за задержку.",
            silver_delta=20, moves_delta=2,
        ),
        5: EventOutcome(
            "Раненый оплатил за вашу услугу и поблагодарил перед уходом.",
            gold_delta=5, silver_delta=35,
        ),
        6: EventOutcome(
            "Раненый оказался священником, который благословил вас своей силой "
            "за оказанную ему помощь.",
            gold_delta=15, moves_delta=10,
        ),
    }

EVENT = InjuredEvent