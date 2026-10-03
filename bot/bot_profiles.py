from dataclasses import dataclass
from game.game_config import DEFAULT_BOT_DIFFICULTY


@dataclass(frozen=True)
class BotProfile:
    """Параметры сложности бота. Все числа - стартовые, финально подбираются симуляцией."""
    think_interval: float    # секунд между "размышлениями" (выбор цели и построение пути)
    speed_factor: float      # множитель базовой скорости бота (самая простая ручка баланса)
    start_delay: float       # секунд, которые бот стоит на старте
    gold_weight: float       # вес золота в оценке целей
    silver_weight: float     # вес серебра в оценке целей
    event_risk: float        # 0..1: готовность идти на клетки событий
    mistake_chance: float    # 0..1: вероятность выбрать не лучшую цель

BOT_PROFILES = {
    "easy": BotProfile(
        think_interval=0.5, speed_factor=0.85, start_delay=3.0,
        gold_weight=1.0, silver_weight=1.0, event_risk=0.3, mistake_chance=0.25,
    ),
    "normal": BotProfile(
        think_interval=0.4, speed_factor=1.0, start_delay=1.5,
        gold_weight=1.0, silver_weight=1.0, event_risk=0.5, mistake_chance=0.10,
    ),
    "hard": BotProfile(
        think_interval=0.3, speed_factor=1.1, start_delay=0.0,
        gold_weight=1.2, silver_weight=1.0, event_risk=0.7, mistake_chance=0.0,
    ),
}

def get_profile(difficulty):
    return BOT_PROFILES.get(difficulty, BOT_PROFILES[DEFAULT_BOT_DIFFICULTY])