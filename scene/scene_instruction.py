import pygame
from settings import *
from widgets import Button, ScrollArea, get_font, wrap_text
from game.rendering.image_manager import ImageManager
from game.event_manager import EventRegistry
from bot.bot_profiles import BOT_PROFILES
from scene.scenes import Scene
from game.game_config import (
    PLAYER_BASE_SPEED, GOLD_YIELD_INTERVAL, GOLD_CELL_YIELD,
    SILVER_RESPAWN_INTERVAL, EVENT_RESPAWN_INTERVAL,
    SILVER_PILE_MIN_VALUE, SILVER_PILE_MAX_VALUE,
    SILVER_CELL_BASE_DENSITY, SILVER_CELL_DENSITY_PER_PLAYER,
    MIN_MAP_SIZE, MAX_MAP_SIZE, MAP_SIZE_PRESETS,
    MIN_OBSTACLE_PERCENT, MAX_OBSTACLE_PERCENT, DEFAULT_OBSTACLE_PERCENT,
    MIN_VISION_RADIUS, MAX_VISION_RADIUS, DEFAULT_VISION_RADIUS,
    MIN_WIN_GOLD, MAX_WIN_GOLD, WIN_GOLD_STEP, DEFAULT_WIN_GOLD,
    MIN_WIN_SILVER, MAX_WIN_SILVER, WIN_SILVER_STEP, DEFAULT_WIN_SILVER,
    MIN_GOLD_CELLS, MAX_GOLD_CELLS, DEFAULT_GOLD_CELLS,
    MIN_EVENT_DENSITY_PERCENT, MAX_EVENT_DENSITY_PERCENT, DEFAULT_EVENT_DENSITY_PERCENT,
    EVENT_DENSITY_PER_PLAYER,
    MIN_BOT_COUNT, MAX_BOT_COUNT, BOT_DIFFICULTY_ORDER,
)

def _pct(fraction):
    """0.05 -> '5%'."""
    return f"{fraction * 100:g}%"

def _bot_difficulty_items():
    """Строки про уровни сложности собираются из профилей, чтобы не расходились с балансом."""
    items = []
    for key in BOT_DIFFICULTY_ORDER:
        profile = BOT_PROFILES[key]
        mistakes = (f"ошибается в выборе цели в {_pct(profile.mistake_chance)} случаев"
                    if profile.mistake_chance > 0 else "не ошибается в выборе цели")
        items.append(("p", f"• {BOT_DIFFICULTY_NAMES_RU[key]}: скорость ×{profile.speed_factor:g}, "
                           f"стоит на старте {profile.start_delay:g} с, {mistakes}."))
    return items

def _event_items():
    """Блок по каждому событию собирается из самих определений в events/."""
    items = []
    for event in EventRegistry.shared().all():
        items.append(("icon", event.icon_file, event.title, TEXT_COLOR, event.icon_dir))
        items.append(("p", f"Риск: {event.describe_outcome(1)}.", WARNING_TEXT_COLOR))
        items.append(("p", f"Удача: {event.describe_outcome(6)}.", SELECTED_BORDER_COLOR))
    return items

INSTRUCTION_SECTIONS = [
    {
        "title": "Цель игры",
        "items": [
            ("p", "Соберите нужное количество золота и серебра, а затем добегите до финишной "
                  "клетки — она всегда находится в правом нижнем углу карты. Игра идёт в "
                  "реальном времени."),
            ("icon", ICON_GOLD, f"Золото для победы: {MIN_WIN_GOLD}–{MAX_WIN_GOLD} "
                                 f"(шаг {WIN_GOLD_STEP}, по умолчанию {DEFAULT_WIN_GOLD}).",
             SELECTED_BORDER_COLOR),
            ("icon", ICON_SILVER, f"Серебро для победы: {MIN_WIN_SILVER}–{MAX_WIN_SILVER} "
                                   f"(шаг {WIN_SILVER_STEP}, по умолчанию {DEFAULT_WIN_SILVER}).",
             SELECTED_BORDER_COLOR),
            ("p", "Побеждает первый, кто стоит на финише, имея достаточно золота и серебра, "
                  "будь то вы или бот. Партия заканчивается сразу."),
            ("p", "Совет: финишная клетка всегда выделена на карте — планируйте маршрут "
                  "туда заранее, пока копите ресурсы.", WIN_CELL_COLOR),
        ],
    },
    {
        "title": "Движение",
        "items": [
            ("p", "Кликните по исследованной клетке — игрок сразу побежит к ней. Новый клик "
                  "на бегу перенаправляет игрока без отката назад."),
            ("icon", ICON_MOVE, f"Базовая скорость: {PLAYER_BASE_SPEED:g} клетки в секунду. "
                                 "Эффекты замедляют и ускоряют её.", SELECTED_BORDER_COLOR),
            ("p", "Эффекты разных видов перемножаются, одинаковые не складываются, а "
                  "продлеваются. Оглушение полностью останавливает игрока, но команды "
                  "запоминаются."),
            ("p", "Пробел останавливает игрока у ближайшей клетки маршрута.", HINT_TEXT_COLOR),
        ],
    },
    {
        "title": "Камера",
        "items": [
            ("p", "Зажмите правую кнопку мыши и потяните, чтобы панорамировать карту."),
            ("p", "Колесо мыши меняет масштаб; также можно зажать Shift и пользоваться "
                  "стрелками вверх/вниз для плавного зума."),
            ("p", "После перетаскивания камера перестаёт следовать за игроком. Нажмите C "
                  "или отдайте команду движения, чтобы вернуть её.", HINT_TEXT_COLOR),
        ],
    },
    {
        "title": "Золотые клетки",
        "items": [
            ("p", "Золотые клетки окружены уголками стен: войти можно через проходы "
                  "посередине сторон. Каждые "
                  f"{GOLD_YIELD_INTERVAL:g} секунд в них понемногу накапливается золото."),
            ("icon", ICON_GOLD, f"Прирост: {GOLD_CELL_YIELD} золота за клетку каждые "
                                 f"{GOLD_YIELD_INTERVAL:g} с.", GOLD_CELL_BORDER_COLOR),
            ("icon", ICON_GOLD, f"Количество клеток на карте: {MIN_GOLD_CELLS}–{MAX_GOLD_CELLS} "
                                 f"(по умолчанию {DEFAULT_GOLD_CELLS}; максимум зависит от "
                                 "размера карты).", GOLD_CELL_BORDER_COLOR),
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
            ("icon", ICON_SILVER_FIELD,
             f"Плотность: {_pct(SILVER_CELL_BASE_DENSITY)} свободных клеток "
             f"плюс {_pct(SILVER_CELL_DENSITY_PER_PLAYER)} за каждого бота.", SELECTED_BORDER_COLOR),
            ("icon", ICON_SILVER, f"Размер кучки: {SILVER_PILE_MIN_VALUE}–{SILVER_PILE_MAX_VALUE} "
                                   "серебра (случайно).", SELECTED_BORDER_COLOR),
            ("p", f"Каждые {SILVER_RESPAWN_INTERVAL:g} секунд кучки вне вашего поля зрения "
                  "обновляются — исчезнувшие пополняются заново."),
        ],
    },
    {
        "title": "Туман войны",
        "items": [
            ("p", "Карта открывается постепенно."),
            ("p", "Клетки в радиусе обзора видны прямо сейчас."),
            ("p", "Ранее исследованные, но не видимые сейчас клетки — показаны "
                  "затемнёнными.", HINT_TEXT_COLOR),
            ("icon", ICON_SELECT, f"Дальность обзора: {MIN_VISION_RADIUS}–{MAX_VISION_RADIUS} клеток "
                                   f"(по умолчанию {DEFAULT_VISION_RADIUS}), настраивается перед игрой.",
             SELECTED_BORDER_COLOR),
            ("p", "Важно: капитальные блоки перекрывают обзор — сквозь них не видно. А "
                  "вот тонкие стены обзор не блокируют: видно, что за ними, но пройти "
                  "напрямую нельзя.", WARNING_TEXT_COLOR),
        ],
    },
    {
        "title": "Боты",
        "items": [
            ("p", f"Против вас могут играть от {MIN_BOT_COUNT} до {MAX_BOT_COUNT} ботов. "
                  "Они подчиняются тем же правилам: туман войны, скорость, события и эффекты."),
            ("p", "Золотые клетки и финиш бот знает с самого начала, как и вы. Серебро и события "
                  "он запоминает только те, что увидел сам, и забывает, если клетка оказалась пустой."),
            ("p", "Игроки не мешают друг другу и свободно проходят сквозь друг друга. Борьба идёт "
                  "только за ресурсы: кто первый пришёл, тот и забрал."),
            ("p", "Сложность выбирается перед игрой:"),
            *_bot_difficulty_items(),
            ("p", "Если бот открыл событие в вашем поле зрения, слева вверху появится уведомление "
                  "с его результатом.", HINT_TEXT_COLOR),
        ],
    },
    {
        "title": "Случайные события",
        "items": [
            ("p", "На карте иногда появляются загадочные объекты. Наступив на клетку с "
                  "событием, вам предложат с ним взаимодействовать — при согласии "
                  "бросается кубик. Время в мире не останавливается, пока открыто окно "
                  "события; эффекты начинают действовать после его закрытия."),
            ("icon", "dice-six-faces-six.png",
             "Грань 1–6 равновероятна; расстановка вне поля зрения обновляется каждые "
             f"{EVENT_RESPAWN_INTERVAL:g} секунд; плотность {MIN_EVENT_DENSITY_PERCENT}–"
             f"{MAX_EVENT_DENSITY_PERCENT}% (по умолчанию {DEFAULT_EVENT_DENSITY_PERCENT}%, "
             f"плюс {_pct(EVENT_DENSITY_PER_PLAYER)} за каждого бота).",
             SELECTED_BORDER_COLOR),

            *_event_items(),
        ],
    },
    {
        "title": "Настройки партии",
        "items": [
            ("p", "Перед стартом партии можно настроить параметры:"),
            ("p", f"• Размер карты: {MIN_MAP_SIZE}–{MAX_MAP_SIZE} клеток (пресеты "
                  f"{', '.join(label.replace('x', '×') for label, _w, _h in MAP_SIZE_PRESETS)} "
                  "или свой размер)."),
            ("p", f"• Доля стен и камней: {MIN_OBSTACLE_PERCENT}–{MAX_OBSTACLE_PERCENT}% "
                  f"(по умолчанию {DEFAULT_OBSTACLE_PERCENT}%)."),
            ("icon", ICON_SELECT, f"• Дальность обзора: {MIN_VISION_RADIUS}–{MAX_VISION_RADIUS} "
                                   f"(по умолчанию {DEFAULT_VISION_RADIUS})."),
            ("p", f"• Количество ботов: {MIN_BOT_COUNT}–{MAX_BOT_COUNT} и их сложность."),
            ("p", f"• Плотность событий: {MIN_EVENT_DENSITY_PERCENT}–{MAX_EVENT_DENSITY_PERCENT}% "
                  f"(по умолчанию {DEFAULT_EVENT_DENSITY_PERCENT}%)."),
            ("icon", ICON_GOLD, f"• Золото для победы: {MIN_WIN_GOLD}–{MAX_WIN_GOLD}, "
                                 f"шаг {WIN_GOLD_STEP}."),
            ("icon", ICON_SILVER, f"• Серебро для победы: {MIN_WIN_SILVER}–{MAX_WIN_SILVER}, "
                                   f"шаг {WIN_SILVER_STEP}."),
            ("icon", ICON_GOLD, f"• Золотых клеток: {MIN_GOLD_CELLS}–{MAX_GOLD_CELLS} "
                                 "(максимум зависит от размера карты)."),
        ],
    },
    {
        "title": "Пауза",
        "items": [
            ("p", "Клавиша Esc во время партии открывает паузу — оттуда можно вернуться "
                  "в игру или выйти в главное меню. Пока пауза открыта, время в мире стоит."),
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
                    for line in wrap_text(para_font, text, content_width):
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
                    lines = wrap_text(para_font, text, wrap_width) or [""]

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