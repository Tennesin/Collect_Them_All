class TurnManager:

    def __init__(self, players, max_moves, turn_time):
        self.players = players
        self.max_moves = max_moves
        self.turn_time = turn_time

        self.current_index = 0
        self.moves_left = max_moves
        self.time_left = turn_time

        self.eliminated = set()
        self.moves_trigger_suppressed = False  # пока открыт попап события, нехватка ходов сама по себе не завершает черёд

        self.on_turn_change = None
        self.on_cycle_complete = None

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
        self._move_to_next_active_index()
        self.moves_left = self.max_moves
        self.time_left = self.turn_time
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