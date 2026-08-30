class Scene:
    """Базовый класс сцены. Конкретная сцена переопределяет то, что ей нужно."""

    def __init__(self, manager):
        self.manager = manager

    def handle_event(self, event):
        pass

    def update(self, dt):
        pass

    def draw(self, screen):
        pass

    def on_enter(self):
        """Вызывается один раз, когда сцена становится активной (push)."""
        pass

    def on_exit(self):
        """Вызывается один раз, когда сцена окончательно снимается со стека (pop)."""
        pass

    def on_pause(self):
        """Вызывается, когда поверх этой сцены кладут другую (например, паузу),
        но сама сцена остаётся в стеке."""
        pass

    def on_resume(self):
        """Вызывается, когда сцена снова становится верхней после pop() над ней."""
        pass


class SceneManager:

    def __init__(self, app):
        self.app = app
        self._stack = []

    @property
    def current(self):
        return self._stack[-1] if self._stack else None

    def push(self, scene):
        if self.current:
            self.current.on_pause()
        self._stack.append(scene)
        scene.on_enter()

    def pop(self):
        if not self._stack:
            return
        scene = self._stack.pop()
        scene.on_exit()
        if self.current:
            self.current.on_resume()

    def switch_to(self, scene):
        """Полностью очищает стек и кладёт одну новую сцену.
        Используется для возврата в главное меню из глубины стека."""
        while self._stack:
            self._stack.pop().on_exit()
        self._stack.append(scene)
        scene.on_enter()

    def handle_event(self, event):
        if self.current:
            self.current.handle_event(event)

    def update(self, dt):
        if self.current:
            self.current.update(dt)

    def draw(self, screen):
        if self.current:
            self.current.draw(screen)