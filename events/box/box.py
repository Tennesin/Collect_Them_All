from game.event_manager import EventDefinition, EventOutcome
from game.effects import Effect

class SilverMagnetEffect(Effect):
    """Собственная механика события 'Коробка'."""

    label = "Магнит серебра"
    RADIUS = 3
    DURATION_TURNS = 4

    def on_cell_reached(self, player, context):
        context.collect_nearby_silver(player, self.RADIUS)

class BoxEvent(EventDefinition):
    id = "box"
    icon_file = "box.png"
    prompt_text = (
        "Незнакомец в капюшоне протянул вам перевязанную коробку и растворился "
        "в толпе, прежде чем вы успели спросить, что это. Открыть посылку?"
    )
    outcomes = {
        1: EventOutcome(
            "Внутри оказалась мина-ловушка! Взрыв отбросил вас далеко в сторону.",
            gold_delta=-5, silver_delta=-30, displacement_cells=4,
        ),
        2: EventOutcome(
            "Коробка совершенно пуста — только время потрачено зря.",
            moves_delta=-3,
        ),
        3: EventOutcome(
            "Внутри — скромный, но честный подарок.",
            silver_delta=20,
        ),
        4: EventOutcome(
            "Внутри — скромный, но честный подарок.",
            silver_delta=20,
        ),
        5: EventOutcome(
            "Щедрое подношение — не ожидали такого от случайного незнакомца.",
            gold_delta=5, silver_delta=25,
        ),
        6: EventOutcome(
            "Внутри оказался странный гудящий артефакт — он словно сам "
            "притягивает к вам разбросанное вокруг серебро!",
            gold_delta=5,
            effect_factory=lambda: SilverMagnetEffect(SilverMagnetEffect.DURATION_TURNS),
        ),
    }

EVENT = BoxEvent