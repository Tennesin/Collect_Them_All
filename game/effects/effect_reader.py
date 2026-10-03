"""Единственная точка, через которую игра взаимодействует с эффектами событий."""
from game.effects.effects import Effect

class EffectReader:

    @staticmethod
    def update(player, dt, context):
        """Покадровый хук on_update для всех активных эффектов игрока."""
        for effect in list(player.active_effects):
            EffectReader._safe_call(effect, "on_update", player, dt, context)

    @staticmethod
    def notify_cell_reached(player, context):
        for effect in list(player.active_effects):
            EffectReader._safe_call(effect, "on_cell_reached", player, context)

    @staticmethod
    def notify_effect_applied(player, effect):
        EffectReader._safe_call(effect, "on_apply", player)

    @staticmethod
    def modify_income(player, resource_type, amount):
        for effect in list(player.active_effects):
            amount = EffectReader._safe_call(
                effect, "modify_income", player, resource_type, amount,
                default=amount,
            )
        return amount

    @staticmethod
    def tick(player, dt, context=None):
        """Уменьшает длительность эффектов на dt секунд и снимает истёкшие.
        Список активных эффектов обновляется ДО вызова on_expire, чтобы
        истёкший эффект уже не влиял на проверки внутри on_expire."""
        still_active = []
        expired = []
        for effect in player.active_effects:
            if not isinstance(effect, Effect):
                print(f"[EffectReader] Пропущен эффект несовместимого типа: {effect!r}")
                continue
            try:
                still_running = effect.tick(dt)
            except Exception as exc:
                print(f"[EffectReader] Эффект {effect!r} упал на tick(): {exc}")
                continue
            (still_active if still_running else expired).append(effect)

        if len(still_active) != len(player.active_effects):
            player.active_effects = still_active
            player.vision_dirty = True
        for effect in expired:
            EffectReader._safe_call(effect, "on_expire", player, context)

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