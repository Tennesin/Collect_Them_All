from game.game_config import PLAYER_BASE_SPEED
from bot.bot_controller import BotController
from bot.bot_profiles import get_profile

def create_bot_controller(world, player, difficulty, index, total):
    """Подходит под GameWorld(controller_factory=...)."""
    profile = get_profile(difficulty)
    player.base_speed = PLAYER_BASE_SPEED * profile.speed_factor
    return BotController(world, player, profile, index, total)