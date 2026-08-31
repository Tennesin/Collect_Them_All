class Camera:
    """Отвечает исключительно за проекцию мир<->экран, зум и панорамирование."""

    def __init__(self, screen_width, screen_height, field_width, field_height,
                 initial_scale, max_scale):
        self.width = screen_width
        self.height = screen_height
        self.field_width = field_width
        self.field_height = field_height

        self.min_scale = max(screen_width / field_width, screen_height / field_height)
        self.max_scale = max_scale
        self.scale = max(self.min_scale, min(self.max_scale, initial_scale))

        self.center_x = screen_width // 2
        self.center_y = screen_height // 2
        self.offset_x = 0
        self.offset_y = 0

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

    def pan(self, dx, dy):
        self.offset_x += dx
        self.offset_y += dy
        self.clamp_offset()

    def zoom(self, factor):
        new_scale = max(self.min_scale, min(self.max_scale, self.scale * factor))
        if new_scale == self.scale:
            return
        ratio = new_scale / self.scale
        self.offset_x *= ratio
        self.offset_y *= ratio
        self.scale = new_scale
        self.clamp_offset()

    def center_on(self, world_x, world_y):
        self.offset_x = -world_x * self.scale
        self.offset_y = -world_y * self.scale
        self.clamp_offset()