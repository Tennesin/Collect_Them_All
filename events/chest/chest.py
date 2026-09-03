from game.event_manager import EventDefinition, EventOutcome
from game.effects import Effect


class HalfIncomeCurseEffect(Effect):
    """Собственная механика события 'Сундук': пока эффект активен, весь
    собираемый игроком доход (золото и серебро) урезается вдвое."""

    label = "Проклятие (половина дохода)"
    warning = True
    DURATION_TURNS = 3

    def modify_income(self, player, resource_type, amount):
        return amount // 2


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
            effect_factory=lambda: HalfIncomeCurseEffect(HalfIncomeCurseEffect.DURATION_TURNS),
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

EVENT = ChestEvent