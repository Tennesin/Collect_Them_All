import os
import pygame

IMAGES_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "images")

# Общий модульный кэш — по аналогии с _font_cache в widgets.py.
_raw_cache = {}
_scaled_cache = {}

class ImageManager:

    @staticmethod
    def get(name, base_dir=None):
        base_dir = base_dir or IMAGES_DIR
        key = (base_dir, name)
        surf = _raw_cache.get(key)
        if surf is None:
            path = os.path.join(base_dir, name)
            surf = pygame.image.load(path).convert_alpha()
            _raw_cache[key] = surf
        return surf

    @staticmethod
    def get_scaled(name, size, alpha=255, base_dir=None):
        size = (max(1, int(size[0])), max(1, int(size[1])))
        base_dir = base_dir or IMAGES_DIR
        key = (base_dir, name, size, alpha)
        surf = _scaled_cache.get(key)
        if surf is None:
            base = ImageManager.get(name, base_dir=base_dir)
            surf = pygame.transform.smoothscale(base, size)
            if alpha != 255:
                surf = surf.copy()
                surf.set_alpha(alpha)
            _scaled_cache[key] = surf
        return surf

    @staticmethod
    def clear_scaled_cache():
        _scaled_cache.clear()