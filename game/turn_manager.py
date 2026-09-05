class TurnManager:

    def __init__(self, players, max_moves, turn_time):
        self.players = players
        self.max_moves = max_moves
        self.turn_time = turn_time

        self.current_index = 0
        self.moves_cap = self._effective_max_moves(self.current_player)
        self.moves_left = self.moves_cap
        self.time_left = turn_time

        self.eliminated = set()
        self.moves_trigger_suppressed = False  # пока открыт попап события, нехватка ходов сама по себе не завершает черёд

        self.on_turn_change = None
        self.on_cycle_complete = None
        self.on_player_turn_end = None  # вызывается с игроком, чей черёд только что завершился

    @property
    def current_player(self):
        return self.players[self.current_index]

    def update(self, dt):
        if self.time_left > 0:
            self.time_left = max(0.0, self.time_left - dt)
        self._maybe_advance()

    def consume_move(self):
        self.moves_left = max(0, self.moves_left - 1)
        self._maybe_advance()

    def adjust_moves(self, delta):
        """Разовое изменение оставшихся ходов от внешнего источника (событие)."""
        self.moves_left = max(0, self.moves_left + delta)
        self._maybe_advance()

    def refill_moves(self, extra_cap=0):
        """Полностью пополняет шаги текущего черёда; позволяет выйти за лимит
        не более, чем на extra_cap шагов сверху (см. события с полным восстановлением)."""
        self.moves_left = min(self.moves_left + self.moves_cap, self.moves_cap + extra_cap)
        self._maybe_advance()

    def eliminate(self, player):
        """Исключает игрока из дальнейшей очереди ходов (он уже финишировал)."""
        self.eliminated.add(player)

    def end_turn_early(self):
        """Немедленно завершает текущий черёд, не дожидаясь исчерпания ходов/времени."""
        self._advance_turn()

    def _maybe_advance(self):
        player = self.current_player
        if player.moving:
            return
        moves_exhausted = self.moves_left <= 0 and not self.moves_trigger_suppressed
        if moves_exhausted or self.time_left <= 0:
            self._advance_turn()

    def _advance_turn(self):
        ending_player = self.current_player
        self._move_to_next_active_index()
        self.moves_cap = self._effective_max_moves(self.current_player)
        self.moves_left = self.moves_cap
        self.time_left = self.turn_time
        if self.on_player_turn_end:
            self.on_player_turn_end(ending_player)
        if self.on_turn_change:
            self.on_turn_change(self.current_player)

    def _move_to_next_active_index(self):
        """Перебирает игроков по кругу, пропуская выбывших."""
        for _ in range(len(self.players)):
            self.current_index += 1
            if self.current_index >= len(self.players):
                self.current_index = 0
                if self.on_cycle_complete:
                    self.on_cycle_complete()
            if self.current_player not in self.eliminated:
                return

    # --- Индивидуальные модификаторы лимита ходов от эффектов игрока ---

    def _effective_max_moves(self, player):
        base = self.max_moves
        overrides = [
            getattr(effect, "max_moves_override", None) for effect in player.active_effects
        ]
        overrides = [value for value in overrides if value is not None]
        if overrides:
            base = min(overrides)

        for effect in player.active_effects:
            multiplier = getattr(effect, "max_moves_multiplier", None)
            if multiplier is not None:
                base = int(round(base * multiplier))

        return max(1, base)