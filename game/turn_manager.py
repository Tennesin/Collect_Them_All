class TurnManager:
    """Управляет очередностью ходов между игроками одной партии.
    Знает про лимит движений и времени в рамках одного черёда,
    но ничего не знает про pygame и про то, как игроки рисуются."""

    def __init__(self, players, max_moves, turn_time):
        self.players = players
        self.max_moves = max_moves
        self.turn_time = turn_time

        self.current_index = 0
        self.moves_left = max_moves
        self.time_left = turn_time

        # Вызывается с новым текущим игроком, когда ход переходит к следующему.
        self.on_turn_change = None

    @property
    def current_player(self):
        return self.players[self.current_index]

    def update(self, dt):
        """Вызывать каждый кадр, пока идёт геймплей (таймер тикает всегда,
        даже если игрок ещё не начал двигаться в этом черёде)."""
        if self.time_left > 0:
            self.time_left = max(0.0, self.time_left - dt)
        self._maybe_advance()

    def consume_move(self):
        """Вызывается игроком (через Player.on_cell_reached) при входе в новую клетку."""
        self.moves_left = max(0, self.moves_left - 1)
        self._maybe_advance()

    def _maybe_advance(self):
        player = self.current_player
        if player.moving:
            # Не прерываем анимацию посреди движения — дожидаемся,
            # пока игрок физически остановится в клетке.
            return
        if self.moves_left <= 0 or self.time_left <= 0:
            self._advance_turn()

    def _advance_turn(self):
        self.current_index = (self.current_index + 1) % len(self.players)
        self.moves_left = self.max_moves
        self.time_left = self.turn_time
        if self.on_turn_change:
            self.on_turn_change(self.current_player)