from game.event_manager import EventDefinition, EventOutcome
from game.effects.effects import Effect
from game.effects.speed_effects import SlowEffect, HasteEffect

class HalfIncomeCurseEffect(Effect):
    """Собственная механика события 'Сундук': пока эффект активен, весь
    собираемый игроком доход (золото и серебро) урезается вдвое."""

    label = "Проклятие (половина дохода)"
    warning = True
    DURATION_SECONDS = 10.0

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
            effect_factory=lambda: HalfIncomeCurseEffect(HalfIncomeCurseEffect.DURATION_SECONDS),
        ),
        2: EventOutcome(
            "Сундук недовольно заскрипел и вытряс на вас пыль вместо сокровищ — "
            "вы закашлялись и сбавили шаг.",
            silver_delta=-35,
            effect_factory=lambda: SlowEffect(0.75, 3.5),
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
            "Похоже, вы ему приглянулись — сундук выдал щедрую пригоршню серебра "
            "и будто подбодрил вас.",
            silver_delta=35,
            effect_factory=lambda: HasteEffect(1.25, 4.0),
        ),
        6: EventOutcome(
            "Сундук довольно заурчал и вывалил перед вами настоящий подарок — "
            "силы так и прибывают!",
            gold_delta=20,
            effect_factory=lambda: HasteEffect(1.5, 5.0),
        ),
    }

EVENT = ChestEvent