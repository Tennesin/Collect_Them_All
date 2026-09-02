import pygame
from settings import *
from widgets import Button, ScrollArea, get_font
from scene.scenes import Scene

# (заголовок раздела, текст раздела)
INSTRUCTION_SECTIONS = [
    (
        "Цель игры",
        "Соберите нужное количество золота и серебра и приведите игрока на финишную клетку "
        "(она всегда находится в правом нижнем углу карты). Режим завершения партии "
        "выбирается в настройках перед стартом: 'Первый у цели' — игра сразу заканчивается, "
        "как только кто-то выполнил условие, 'До последнего' — финишировавшие игроки выбывают "
        "по очереди, а партия продолжается для оставшихся, пока не останется один."
    ),
    (
        "Ходы и время",
        "Каждый черёд у игрока есть ограниченное количество ходов и время на размышление. "
        "Оба ресурса тратятся независимо: как только истощится любой из них, ход переходит "
        "следующему игроку. Кликните по исследованной клетке, чтобы построить маршрут — "
        "повторный клик по той же клетке подтверждает движение. Пробел мгновенно "
        "останавливает движение на месте."
    ),
    (
        "Камера",
        "Зажмите правую кнопку мыши и потяните, чтобы панорамировать карту. Колесо мыши "
        "меняет масштаб; также можно зажать Shift и пользоваться стрелками вверх/вниз."
    ),
    (
        "Золото и серебро",
        "Золотые клетки спрятаны за стенками короба и недоступны напрямую — но каждый цикл "
        "ходов всех игроков в них понемногу накапливается золото, которое можно забрать, "
        "дойдя до клетки. Серебряные кучки разбросаны по карте в случайных местах и "
        "исчезают после сбора, но раз в несколько циклов часть из них появляется заново."
    ),
    (
        "Туман войны",
        "Карта открывается постепенно: клетки в радиусе обзора текущего игрока видны прямо "
        "сейчас, ранее исследованные, но не видимые сейчас — показаны затемнёнными, а "
        "остальные скрыты полностью. Дальность обзора настраивается перед началом партии."
    ),
    (
        "Случайные события",
        "На карте иногда появляются загадочные объекты. Наступив на клетку с событием, вам "
        "предложат с ним взаимодействовать. Если согласиться — бросается кубик, и в "
        "зависимости от выпавшей грани вы получаете один из шести заранее заданных исходов: "
        "от неприятностей до щедрой награды золотом, серебром или ходами. Отказ ничего не "
        "меняет. Плотность событий на карте тоже настраивается перед игрой."
    ),
    (
        "Настройки партии",
        "Перед стартом можно настроить: размер карты и долю препятствий, количество игроков, "
        "дальность обзора, плотность событий, требуемое количество золота и серебра для "
        "победы, количество золотых клеток, режим завершения партии, а также число ходов "
        "и время на черёд."
    ),
    (
        "Пауза",
        "Клавиша Esc во время партии открывает паузу: оттуда можно вернуться в игру или "
        "выйти в главное меню, не дожидаясь окончания партии."
    ),
]


class InstructionScene(Scene):
    """Полноэкранный текстовый блок с описанием механик игры, доступен из главного меню."""

    CONTENT_MARGIN_X = 60
    CONTENT_TOP = 96
    CONTENT_BOTTOM_MARGIN = 20

    def __init__(self, manager):
        super().__init__(manager)
        self.back_button = Button((20, 20, 90, 32), "Назад")
        self.scroll = ScrollArea()

        self.content_rect = pygame.Rect(
            self.CONTENT_MARGIN_X, self.CONTENT_TOP,
            SCREEN_WIDTH - self.CONTENT_MARGIN_X * 2,
            SCREEN_HEIGHT - self.CONTENT_TOP - self.CONTENT_BOTTOM_MARGIN,
        )
        content_width = self.content_rect.width - 16  # запас под полосу прокрутки справа
        self.content_blocks, content_height = self._build_content(content_width)
        self.scroll.update_bounds(content_height, self.content_rect.height)

    # --- Построение содержимого (один раз при создании сцены) ---

    @staticmethod
    def _wrap_lines(font, text, max_width):
        words = text.split(" ")
        lines = []
        line = ""
        for word in words:
            candidate = f"{line} {word}".strip()
            if font.size(candidate)[0] > max_width and line:
                lines.append(line)
                line = word
            else:
                line = candidate
        if line:
            lines.append(line)
        return lines

    def _build_content(self, content_width):
        header_font = get_font(FONT_SIZE_LABEL + 2)
        para_font = get_font(FONT_SIZE_HINT + 2)

        blocks = []
        y = 0
        for title, paragraph in INSTRUCTION_SECTIONS:
            header_surf = header_font.render(title, True, SELECTED_BORDER_COLOR)
            blocks.append((y, header_surf))
            y += header_surf.get_height() + 8

            for line in self._wrap_lines(para_font, paragraph, content_width):
                line_surf = para_font.render(line, True, TEXT_COLOR)
                blocks.append((y, line_surf))
                y += line_surf.get_height() + 4

            y += 22  # отступ перед следующим разделом

        return blocks, y

    # --- События ---

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.manager.pop()
            return
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.back_button.collidepoint(event.pos):
                self.manager.pop()
            return
        if event.type == pygame.MOUSEWHEEL:
            self.scroll.scroll_by_wheel(event.y)

    # --- Отрисовка ---

    def draw(self, screen):
        screen.fill(MENU_BG_COLOR)

        title_surf = get_font(FONT_SIZE_TITLE - 16).render("Инструкция", True, TEXT_COLOR)
        screen.blit(title_surf, title_surf.get_rect(center=(SCREEN_WIDTH // 2, 40)))

        hint_surf = get_font(FONT_SIZE_HINT).render("Колесо мыши — прокрутка", True, HINT_TEXT_COLOR)
        screen.blit(hint_surf, hint_surf.get_rect(midright=(SCREEN_WIDTH - 20, 36)))

        mouse_pos = pygame.mouse.get_pos()
        self.back_button.draw(screen, mouse_pos)

        self._draw_content(screen)

    def _draw_content(self, screen):
        rect = self.content_rect
        screen.set_clip(rect)
        for rel_y, surf in self.content_blocks:
            draw_y = rect.y + rel_y - self.scroll.offset
            if draw_y + surf.get_height() < rect.y or draw_y > rect.bottom:
                continue
            screen.blit(surf, (rect.x, draw_y))
        screen.set_clip(None)

        self.scroll.draw_scrollbar(screen, rect)