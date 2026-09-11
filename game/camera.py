import math

class Camera:
    """Отвечает исключительно за проекцию мир<->экран, зум и панорамирование."""

    def __init__(self, screen_width, screen_height, field_width, field_height,
                 initial_scale, max_scale, smooth_speed=10.0):
        self.width = screen_width
        self.height = screen_height
        self.field_width = field_width
        self.field_height = field_height
        self.smooth_speed = smooth_speed

        self.min_scale = max(screen_width / field_width, screen_height / field_height)
        self.max_scale = max(max_scale, self.min_scale)
        self.scale = max(self.min_scale, min(self.max_scale, initial_scale))

        self.center_x = screen_width // 2
        self.center_y = screen_height // 2
        self.offset_x = 0
        self.offset_y = 0
        self.target_offset_x = 0
        self.target_offset_y = 0

    def project(self, x, y):
        screen_x = x * self.scale + self.offset_x + self.center_x
        screen_y = y * self.scale + self.offset_y + self.center_y
        return screen_x, screen_y

    def screen_to_world(self, screen_x, screen_y):
        world_x = (screen_x - self.offset_x - self.center_x) / self.scale
        world_y = (screen_y - self.offset_y - self.center_y) / self.scale
        return world_x, world_y

    def clamp_offset(self):
        min_offset_x = self.center_x - self.field_width * self.scale
        max_offset_x = -self.center_x
        min_offset_y = self.center_y - self.field_height * self.scale
        max_offset_y = -self.center_y
        self.offset_x = max(min_offset_x, min(max_offset_x, self.offset_x))
        self.offset_y = max(min_offset_y, min(max_offset_y, self.offset_y))
        self.target_offset_x = max(min_offset_x, min(max_offset_x, self.target_offset_x))
        self.target_offset_y = max(min_offset_y, min(max_offset_y, self.target_offset_y))

    def update(self, dt):
        """Плавно подтягивает фактическое смещение к целевому. Экспоненциальное
        сглаживание — не зависит от FPS, вызывать каждый кадр из сцены."""
        if self.offset_x == self.target_offset_x and self.offset_y == self.target_offset_y:
            return
        t = 1.0 - math.exp(-self.smooth_speed * dt)
        self.offset_x += (self.target_offset_x - self.offset_x) * t
        self.offset_y += (self.target_offset_y - self.offset_y) * t
        # Догоняем небольшой остаток, чтобы не бесконечно приближаться к цели.
        if abs(self.offset_x - self.target_offset_x) < 0.05:
            self.offset_x = self.target_offset_x
        if abs(self.offset_y - self.target_offset_y) < 0.05:
            self.offset_y = self.target_offset_y

    def pan(self, dx, dy):
        """Драг камеры мышью должен ощущаться мгновенным — двигаем и факт, и цель
        разом, сглаживание тут ни к чему."""
        self.offset_x += dx
        self.offset_y += dy
        self.target_offset_x = self.offset_x
        self.target_offset_y = self.offset_y
        self.clamp_offset()

    def zoom(self, factor):
        new_scale = max(self.min_scale, min(self.max_scale, self.scale * factor))
        if new_scale == self.scale:
            return
        ratio = new_scale / self.scale
        self.offset_x *= ratio
        self.offset_y *= ratio
        self.target_offset_x = self.offset_x
        self.target_offset_y = self.offset_y
        self.scale = new_scale
        self.clamp_offset()

    def center_on(self, world_x, world_y, instant=False):
        """Задаёт цель, куда должна плавно выехать камера."""
        self.target_offset_x = -world_x * self.scale
        self.target_offset_y = -world_y * self.scale
        if instant:
            self.offset_x = self.target_offset_x
            self.offset_y = self.target_offset_y
        self.clamp_offset()