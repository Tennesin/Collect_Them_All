import os
import pygame
from settings import *
from widgets import Button, ScrollArea, get_font
from game.image_manager import ImageManager
from game.event_manager import EVENTS_ROOT
from scene.scenes import Scene

def _event_icon_dir(event_id):
    """Путь к папке события — там же лежит его иконка (см. game/event_manager.py)."""
    return os.path.join(EVENTS_ROOT, event_id)

INSTRUCTION_SECTIONS = [
    {
        "title": "Цель игры",
        "items": [
            ("p", "Соберите нужное количество золота и серебра, а затем приведите игрока "
                  "на финишную клетку — она всегда находится в правом нижнем углу карты."),
            ("icon", ICON_GOLD, "Золото для победы: 10–50 (шаг 5, по умолчанию 25).", SELECTED_BORDER_COLOR),
            ("icon", ICON_SILVER, "Серебро для победы: 50–500 (шаг 25, по умолчанию 125).", SELECTED_BORDER_COLOR),
            ("p", "Режим завершения партии выбирается в настройках перед стартом:"),
            ("p", "«Первый у цели» — партия сразу заканчивается, как только один игрок "
                  "выполнил условие победы."),
            ("p", "«До последнего» — финишировавшие игроки выбывают по очереди, а игра "
                  "продолжается для оставшихся, пока не останется один."),
            ("p", "Совет: финишная клетка всегда выделена на карте — планируйте маршрут "
                  "туда заранее, пока копите ресурсы.", WIN_CELL_COLOR),
        ],
    },
    {
        "title": "Ходы и время",
        "items": [
            ("p", "Каждый черёд у игрока есть два независимых ресурса — ходы и время на "
                  "размышление. Как только истощится любой из них, черёд переходит "
                  "следующему игроку."),
            ("icon", ICON_MOVE, "Ходов за черёд: 4–16 (по умолчанию 8).", SELECTED_BORDER_COLOR),
            ("icon", ICON_TIME, "Время на черёд: 15–60 сек, шаг 3 (по умолчанию 30 сек).", SELECTED_BORDER_COLOR),
            ("p", "Кликните по исследованной клетке, чтобы построить маршрут — повторный "
                  "клик по той же клетке подтверждает движение."),
            ("p", "Пробел мгновенно останавливает движение на месте, не тратя оставшиеся "
                  "ходы впустую.", HINT_TEXT_COLOR),
        ],
    },
    {
        "title": "Камера",
        "items": [
            ("p", "Зажмите правую кнопку мыши и потяните, чтобы панорамировать карту."),
            ("p", "Колесо мыши меняет масштаб; также можно зажать Shift и пользоваться "
                  "стрелками вверх/вниз для плавного зума."),
        ],
    },
    {
        "title": "Золотые клетки",
        "items": [
            ("p", "Золотые клетки спрятаны за кольцом стен и недоступны напрямую — но "
                  "каждый цикл ходов всех игроков в них понемногу накапливается золото."),
            ("icon", ICON_GOLD, "Прирост: 2 золота за клетку каждый цикл ходов.", GOLD_CELL_BORDER_COLOR),
            ("icon", ICON_GOLD, "Количество клеток на карте: 3–8 (по умолчанию 5; "
                                 "максимум зависит от размера карты).", GOLD_CELL_BORDER_COLOR),
            ("p", "Дойдите до клетки, чтобы забрать всё накопленное золото сразу."),
            ("p", "Совет: золотые клетки и площадка вокруг них видны на карте всегда, даже "
                  "вне обзора игрока — их можно приметить заранее и спланировать маршрут.",
             HINT_TEXT_COLOR),
        ],
    },
    {
        "title": "Серебряные клетки",
        "items": [
            ("p", "Серебряные кучки разбросаны по карте в случайных местах и исчезают "
                  "после сбора."),
            ("icon", ICON_SILVER_FIELD, "Плотность: 5% свободных клеток (+1% за каждого "
                                         "игрока сверх первого).", SELECTED_BORDER_COLOR),
            ("icon", ICON_SILVER, "Размер кучки: 15–45 серебра (случайно).", SELECTED_BORDER_COLOR),
            ("p", "Раз в 2 цикла ходов часть кучек обновляется — исчезнувшие пополняются "
                  "заново."),
        ],
    },
    {
        "title": "Туман войны",
        "items": [
            ("p", "Карта открывается постепенно."),
            ("p", "Клетки в радиусе обзора видны прямо сейчас."),
            ("p", "Ранее исследованные, но не видимые сейчас клетки — показаны "
                  "затемнёнными.", HINT_TEXT_COLOR),
            ("icon", ICON_SELECT, "Дальность обзора: 3–10 клеток (по умолчанию 4), "
                                   "настраивается перед игрой.", SELECTED_BORDER_COLOR),
            ("p", "Важно: капитальные блоки перекрывают обзор — сквозь них не видно. А "
                  "вот тонкие стены обзор не блокируют: видно, что за ними, но пройти "
                  "напрямую нельзя.", WARNING_TEXT_COLOR),
        ],
    },
    {
        "title": "Случайные события",
        "items": [
            ("p", "На карте иногда появляются загадочные объекты. Наступив на клетку с "
                  "событием, вам предложат с ним взаимодействовать — при согласии "
                  "бросается кубик."),
            ("icon", "dice-six-faces-six.png",
             "Грань 1–6 равновероятна; раскладка обновляется раз в 3 цикла ходов; "
             "плотность 2–10% (по умолчанию 4%) + 0.5% за каждого игрока сверх первого.",
             SELECTED_BORDER_COLOR),

            ("icon", "bag.png", "Мешок", TEXT_COLOR, _event_icon_dir("bag")),
            ("p", "Риск: разъярённый барсук — до −50 серебра и −7 ходов.", WARNING_TEXT_COLOR),
            ("p", "Удача: тайник контрабандиста — до +20 золота, +50 серебра и +4 хода.",
             SELECTED_BORDER_COLOR),

            ("icon", "box.png", "Коробка", TEXT_COLOR, _event_icon_dir("box")),
            ("p", "Риск: мина-ловушка — до −5 золота, −30 серебра и смещение на 4 клетки.",
             WARNING_TEXT_COLOR),
            ("p", "Удача: загадочный артефакт — «Магнит серебра» на 4 черёда (притягивает "
                  "серебро в радиусе 3 клеток) и +5 золота.", SELECTED_BORDER_COLOR),

            ("icon", "chest.png", "Сундук", TEXT_COLOR, _event_icon_dir("chest")),
            ("p", "Риск: демон в сундуке — −15 золота и проклятие «половина дохода» на "
                  "3 черёда.", WARNING_TEXT_COLOR),
            ("p", "Удача: щедрый подарок — до +20 золота и +7 ходов.", SELECTED_BORDER_COLOR),

            ("icon", "hole.png", "Яма", TEXT_COLOR, _event_icon_dir("hole")),
            ("p", "Риск: бездна — −35 серебра и мгновенная потеря всего остатка текущего "
                  "черёда.", WARNING_TEXT_COLOR),
            ("p", "Удача: тайный проход — +15 золота и способность проходить сквозь стены "
                  "2 черёда.", SELECTED_BORDER_COLOR),

            ("icon", "injured.png", "Раненый", TEXT_COLOR, _event_icon_dir("injured")),
            ("p", "Риск: мнимый раненый оказывается грабителем — до −10 золота, −60 "
                  "серебра и −3 хода.", WARNING_TEXT_COLOR),
            ("p", "Удача: раненый оказывается священником — +15 золота и +10 ходов.",
             SELECTED_BORDER_COLOR),

            ("icon", "medicine_bag.png", "Аптечка", TEXT_COLOR, _event_icon_dir("medicine_bag")),
            ("p", "Риск: «Шиза» — обзор и подвижность падают до минимума на 3 черёда.",
             WARNING_TEXT_COLOR),
            ("p", "Удача: «Супермэн» — видимость всей карты и ×1.5 к лимиту ходов на "
                  "3 черёда.", SELECTED_BORDER_COLOR),
        ],
    },
    {
        "title": "Настройки партии",
        "items": [
            ("p", "Перед стартом партии можно настроить множество параметров:"),
            ("p", "• Размер карты: 11–50 клеток (пресеты 15×15, 22×22, 30×30 — или свой "
                  "размер)."),
            ("p", "• Доля стен и камней: 10–35% (по умолчанию 20%)."),
            ("p", "• Количество игроков: 1–5."),
            ("icon", ICON_SELECT, "• Дальность обзора: 3–10 клеток (по умолчанию 4)."),
            ("p", "• Плотность событий: 2–10% (по умолчанию 4%)."),
            ("icon", ICON_GOLD, "• Золото для победы: 10–50, шаг 5."),
            ("icon", ICON_SILVER, "• Серебро для победы: 50–500, шаг 25."),
            ("icon", ICON_GOLD, "• Золотых клеток: 3–8 (максимум зависит от размера "
                                 "карты)."),
            ("p", "• Режим финиша: «Первый у цели» или «До последнего»."),
            ("icon", ICON_MOVE, "• Ходов за черёд: 4–16 (по умолчанию 8)."),
            ("icon", ICON_TIME, "• Время на черёд: 15–60 сек (по умолчанию 30)."),
        ],
    },
    {
        "title": "Пауза",
        "items": [
            ("p", "Клавиша Esc во время партии открывает паузу — оттуда можно вернуться "
                  "в игру или выйти в главное меню, не дожидаясь окончания партии."),
            ("p", "Совет: если чувствуете, что вот-вот истощатся время или ходы, ставьте "
                  "паузу заранее, чтобы спокойно спланировать следующий шаг.", HINT_TEXT_COLOR),
        ],
    },
]


class InstructionScene(Scene):
    """Полноэкранный текстовый блок с описанием механик игры, доступен из главного меню."""

    CONTENT_MARGIN_X = 60
    CONTENT_TOP = 96
    CONTENT_BOTTOM_MARGIN = 20
    ICON_LINE_SIZE = FONT_SIZE_HINT + 12

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

        # Прокрутка перетаскиванием: зажали ЛКМ на тексте — тянем вверх/вниз.
        self._dragging_content = False
        self._drag_last_y = 0

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
        icon_size = self.ICON_LINE_SIZE

        blocks = []
        y = 0
        for section in INSTRUCTION_SECTIONS:
            header_surf = header_font.render(section["title"], True, SELECTED_BORDER_COLOR)
            blocks.append((y, "header", header_surf))
            y += header_surf.get_height() + 4
            blocks.append((y, "underline", None))
            y += 12

            for item in section["items"]:
                kind = item[0]

                if kind == "p":
                    text = item[1]
                    color = item[2] if len(item) > 2 else TEXT_COLOR
                    for line in self._wrap_lines(para_font, text, content_width):
                        line_surf = para_font.render(line, True, color)
                        blocks.append((y, "text", line_surf))
                        y += line_surf.get_height() + 4
                    y += 6

                elif kind == "icon":
                    icon_name = item[1]
                    text = item[2]
                    color = item[3] if len(item) > 3 else TEXT_COLOR
                    base_dir = item[4] if len(item) > 4 else None
                    icon = ImageManager.get_scaled(icon_name, (icon_size, icon_size), base_dir=base_dir)

                    text_indent = icon.get_width() + 8
                    wrap_width = max(40, content_width - text_indent)
                    lines = self._wrap_lines(para_font, text, wrap_width) or [""]

                    first_surf = para_font.render(lines[0], True, color)
                    line_height = max(icon.get_height(), first_surf.get_height())
                    blocks.append((y, "icon", (icon, first_surf, line_height, text_indent)))
                    y += line_height + 4

                    for extra_line in lines[1:]:
                        extra_surf = para_font.render(extra_line, True, color)
                        blocks.append((y, "icon_cont", (extra_surf, text_indent)))
                        y += extra_surf.get_height() + 4

                    y += 6

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
            if self.content_rect.collidepoint(event.pos):
                self._dragging_content = True
                self._drag_last_y = event.pos[1]
            return
        if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self._dragging_content = False
            return
        if event.type == pygame.MOUSEMOTION:
            if self._dragging_content:
                dy = event.pos[1] - self._drag_last_y
                self._drag_last_y = event.pos[1]
                self._scroll_by(-dy)
            return
        if event.type == pygame.MOUSEWHEEL:
            self.scroll.scroll_by_wheel(event.y)

    def _scroll_by(self, delta):
        self.scroll.offset = max(0, min(self.scroll.max_scroll, self.scroll.offset + delta))

    # --- Отрисовка ---

    def draw(self, screen):
        screen.fill(MENU_BG_COLOR)

        title_surf = get_font(FONT_SIZE_TITLE - 16).render("Инструкция", True, TEXT_COLOR)
        screen.blit(title_surf, title_surf.get_rect(center=(SCREEN_WIDTH // 2, 40)))

        hint_surf = get_font(FONT_SIZE_HINT).render(
            "Колесо мыши или перетаскивание — прокрутка", True, HINT_TEXT_COLOR
        )
        screen.blit(hint_surf, hint_surf.get_rect(midright=(SCREEN_WIDTH - 20, 36)))

        mouse_pos = pygame.mouse.get_pos()
        self.back_button.draw(screen, mouse_pos)

        self._draw_content(screen)

    def _draw_content(self, screen):
        rect = self.content_rect
        screen.set_clip(rect)

        for rel_y, kind, data in self.content_blocks:
            draw_y = rect.y + rel_y - self.scroll.offset

            if kind == "header":
                surf = data
                if draw_y + surf.get_height() >= rect.y and draw_y <= rect.bottom:
                    screen.blit(surf, (rect.x, draw_y))

            elif kind == "underline":
                if draw_y >= rect.y - 4 and draw_y <= rect.bottom:
                    pygame.draw.line(
                        screen, SELECTED_BORDER_COLOR,
                        (rect.x, draw_y), (rect.x + 140, draw_y), 2,
                    )

            elif kind == "text":
                surf = data
                if draw_y + surf.get_height() >= rect.y and draw_y <= rect.bottom:
                    screen.blit(surf, (rect.x, draw_y))

            elif kind == "icon":
                icon, text_surf, line_height, indent = data
                if draw_y + line_height >= rect.y and draw_y <= rect.bottom:
                    icon_rect = icon.get_rect(midleft=(rect.x, draw_y + line_height // 2))
                    screen.blit(icon, icon_rect)
                    text_rect = text_surf.get_rect(midleft=(rect.x + indent, draw_y + line_height // 2))
                    screen.blit(text_surf, text_rect)

            elif kind == "icon_cont":
                text_surf, indent = data
                if draw_y + text_surf.get_height() >= rect.y and draw_y <= rect.bottom:
                    screen.blit(text_surf, (rect.x + indent, draw_y))

        screen.set_clip(None)
        self.scroll.draw_scrollbar(screen, rect)