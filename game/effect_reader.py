"""Единственная точка, через которую игра взаимодействует с эффектами событий."""
from game.effects import Effect

class EffectReader:

    @staticmethod
    def notify_cell_reached(player, context):
        """Оповещает все активные эффекты игрока, что он остановился на клетке."""
        for effect in list(player.active_effects):
            EffectReader._safe_call(effect, "on_cell_reached", player, context)

    @staticmethod
    def modify_income(player, resource_type, amount):
        """Пропускает amount через все активные эффекты игрока по цепочке."""
        for effect in list(player.active_effects):
            amount = EffectReader._safe_call(
                effect, "modify_income", player, resource_type, amount,
                default=amount,
            )
        return amount

    @staticmethod
    def tick(player):
        """Тикает длительность всех эффектов игрока, снимая истёкшие."""
        still_active = []
        for effect in player.active_effects:
            if not isinstance(effect, Effect):
                print(f"[EffectReader] Пропущен эффект несовместимого типа: {effect!r}")
                continue
            try:
                if effect.tick():
                    still_active.append(effect)
            except Exception as exc:
                print(f"[EffectReader] Эффект {effect!r} упал на tick(): {exc}")
        player.active_effects = still_active

    # --- Внутреннее ---

    @staticmethod
    def _safe_call(effect, hook_name, *args, default=None):
        if not isinstance(effect, Effect):
            print(f"[EffectReader] Пропущен эффект несовместимого типа: {effect!r}")
            return default
        hook = getattr(effect, hook_name, None)
        if not callable(hook):
            return default
        try:
            result = hook(*args)
        except Exception as exc:
            print(f"[EffectReader] Эффект {effect!r} упал на {hook_name}(): {exc}")
            return default
        return result if result is not None else default