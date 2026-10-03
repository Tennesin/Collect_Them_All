from game.event_manager import EventDefinition, EventOutcome
from game.effects.effects import Effect
from game.effects.speed_effects import StunEffect

class PhantomWalkEffect(Effect):
    """Эффект события 'Яма': пока активен, игрок строит путь сквозь любые препятствия.
    Если срок истёк, а игрок стоит на стене/блоке — его выталкивает в ближайшую
    свободную клетку (см. EffectContext.push_out_of_obstacle_if_needed)."""

    label = "Тайный проход"
    DURATION_SECONDS = 6.0

    ignores_obstacles = True

    def on_expire(self, player, context):
        context.push_out_of_obstacle_if_needed(player)


class HoleEvent(EventDefinition):
    id = "hole"
    icon_file = "hole.png"
    prompt_text = (
        "Вы наткнулись на глубокую яму, дна которой не видно даже при освещении. "
        "Вы хотите туда спуститься?"
    )
    outcomes = {
        1: EventOutcome(
            "БЕЗДНА: яма оказалась глубже, чем казалось, — вы с трудом выбрались "
            "наружу, потеряв часть серебра и несколько долгих секунд.",
            silver_delta=-35,
            effect_factory=lambda: StunEffect(3.0),
        ),
        2: EventOutcome(
            "Пустота: внутри не оказалось ничего, кроме темноты — время потрачено впустую.",
            effect_factory=lambda: StunEffect(1.5),
        ),
        3: EventOutcome(
            "Ржавая монета: на дне ямы нашлась позеленевшая от времени монета.",
            silver_delta=10,
        ),
        4: EventOutcome(
            "Заброшенный мешок: кто-то давно обронил здесь мешочек с серебром.",
            silver_delta=30,
        ),
        5: EventOutcome(
            "Клад: в глубине ямы обнаружился настоящий тайник с добром.",
            gold_delta=10, silver_delta=35,
        ),
        6: EventOutcome(
            "ТАЙНЫЙ ПРОХОД: яма оказалась входом в потайной тоннель — вы нашли золото "
            "и на время научились проходить сквозь любые стены.",
            gold_delta=15,
            effect_factory=lambda: PhantomWalkEffect(PhantomWalkEffect.DURATION_SECONDS),
        ),
    }

EVENT = HoleEvent