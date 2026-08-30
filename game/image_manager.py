import os
import pygame

# Абсолютный путь до папки images/ в корне проекта, не зависит от того,
# откуда запущен скрипт.
IMAGES_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "images")

# Общий модульный кэш — по аналогии с _font_cache в widgets.py.
_raw_cache = {}
_scaled_cache = {}

class ImageManager:
    """Загружает и кэширует изображения из папки images/. Ничего не знает
    про то, где именно они используются (поле, панель, иконки ресурсов) —
    просто отдаёт готовые Surface по имени файла."""

    @staticmethod
    def get(name):
        """Возвращает изображение в исходном размере, с альфа-каналом.
        name — имя файла внутри images/, например 'chest.png'."""
        surf = _raw_cache.get(name)
        if surf is None:
            path = os.path.join(IMAGES_DIR, name)
            surf = pygame.image.load(path).convert_alpha()
            _raw_cache[name] = surf
        return surf

    @staticmethod
    def get_scaled(name, size, alpha=255):
        """Возвращает изображение, отмасштабированное под size=(w, h).
        Результат кэшируется по (name, size, alpha) — при частых повторных
        запросах одного и того же размера/прозрачности (например, каждый кадр
        в панели или на поле) масштабирование выполняется только один раз."""
        size = (max(1, int(size[0])), max(1, int(size[1])))
        key = (name, size, alpha)
        surf = _scaled_cache.get(key)
        if surf is None:
            base = ImageManager.get(name)
            surf = pygame.transform.smoothscale(base, size)
            if alpha != 255:
                surf = surf.copy()
                surf.set_alpha(alpha)
            _scaled_cache[key] = surf
        return surf

    @staticmethod
    def clear_scaled_cache():
        """Сбрасывает кэш масштабированных изображений. Пригодится, если камера
        часто меняет масштаб и старые размеры больше не нужны — иначе кэш
        будет расти неограниченно на каждый новый scale."""
        _scaled_cache.clear()