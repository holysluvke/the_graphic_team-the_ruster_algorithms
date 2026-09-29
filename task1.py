"""
Задание 1. Заливка и выделение границы.

1а) Рекурсивный алгоритм заливки на основе серий пикселов (линий) заданным цветом.
1б) Рекурсивный алгоритм заливки на основе серий пикселов рисунком из графического файла
    (небольшой рисунок повторяется циклически, большой берётся напрямую, без масштабирования).
1в) Выделение границы связной области: обход границы, точки заносятся в список
    в порядке обхода, затем граница прорисовывается поверх исходного изображения.
"""

import os
import sys
import threading
import time
import tkinter as tk
from tkinter import ttk, filedialog, colorchooser, messagebox

from PIL import Image, ImageDraw, ImageTk

CANVAS_W, CANVAS_H = 900, 600
BACKGROUND = (255, 255, 255)
PATTERNS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "patterns")

# Рекурсия может быть очень глубокой (по одному вызову на каждую серию пикселов),
# поэтому поднимаем лимит и запускаем заливку в потоке с большим стеком.
sys.setrecursionlimit(1_000_000)


def run_with_big_stack(func, *args):
    """Выполняет func(*args) в отдельном потоке с увеличенным стеком и ждёт результат."""
    result = {}

    def target():
        try:
            result["value"] = func(*args)
        except BaseException as e:  # пробрасываем ошибку в основной поток
            result["error"] = e

    old_size = threading.stack_size()
    threading.stack_size(128 * 1024 * 1024)  # в Windows допускается меньше 256 МБ
    try:
        t = threading.Thread(target=target)
        t.start()
        t.join()
    finally:
        threading.stack_size(old_size)

    if "error" in result:
        raise result["error"]
    return result.get("value")


# ---------------------------------------------------------------------------
# 1а, 1б. Рекурсивная заливка на основе серий пикселов
# ---------------------------------------------------------------------------

def line_fill(img, x, y, color_at):
    """
    Рекурсивная заливка серий пикселов (линий).

    Заливается 4-связная область пикселов того же цвета, что и затравочная точка (x, y).
    color_at(px, py) возвращает цвет, которым надо закрасить пиксел:
    для 1а это всегда один цвет, для 1б - пиксел рисунка.
    Посещённые пикселы отмечаются в маске, поэтому алгоритм корректно работает,
    даже если новый цвет (или цвет рисунка) совпадает с цветом области.
    Возвращает количество закрашенных пикселов.
    """
    w, h = img.size
    pix = img.load()
    old = pix[x, y]
    visited = bytearray(w * h)
    painted = 0

    def inside(px, py):
        return not visited[py * w + px] and pix[px, py] == old

    def fill(sx, sy):
        nonlocal painted
        # 1. Ищем левую и правую границы серии, содержащей (sx, sy)
        xl = sx
        while xl > 0 and inside(xl - 1, sy):
            xl -= 1
        xr = sx
        while xr < w - 1 and inside(xr + 1, sy):
            xr += 1

        # 2. Закрашиваем всю серию [xl, xr]
        row = sy * w
        for px in range(xl, xr + 1):
            pix[px, sy] = color_at(px, sy)
            visited[row + px] = 1
        painted += xr - xl + 1

        # 3. Просматриваем строки выше и ниже в пределах [xl, xr];
        #    для каждой незакрашенной серии рекурсивно вызываем заливку
        for ny in (sy - 1, sy + 1):
            if 0 <= ny < h:
                px = xl
                while px <= xr:
                    if inside(px, ny):
                        fill(px, ny)
                    px += 1

    fill(x, y)
    return painted


def fill_with_color(img, x, y, color):
    """1а. Заливка заданным цветом."""
    return line_fill(img, x, y, lambda px, py: color)


def fill_with_pattern(img, x, y, pattern, origin=(0, 0)):
    """
    1б. Заливка рисунком.

    Точка холста (px, py) берёт пиксел рисунка ((px - ox) mod pw, (py - oy) mod ph).
    - Небольшой рисунок при этом повторяется циклически (как плитка).
    - Большой рисунок (не меньше холста) при origin = (0, 0) просто "лежит под холстом"
      и берётся напрямую, без повторения и масштабирования.
    """
    pp = pattern.load()
    pw, ph = pattern.size
    ox, oy = origin
    return line_fill(img, x, y, lambda px, py: pp[(px - ox) % pw, (py - oy) % ph])


# ---------------------------------------------------------------------------
# 1в. Выделение границы связной области
# ---------------------------------------------------------------------------

# 8 направлений по часовой стрелке (ось y направлена вниз):
# 0 - вправо, 1 - вправо-вниз, 2 - вниз, 3 - влево-вниз,
# 4 - влево, 5 - влево-вверх, 6 - вверх, 7 - вправо-вверх
DIRS = [(1, 0), (1, 1), (0, 1), (-1, 1), (-1, 0), (-1, -1), (0, -1), (1, -1)]


def find_border_start(img, x, y):
    """
    Начальная точка границы: от точки (x, y) внутри области идём вправо
    до первого пиксела другого цвета. Он и есть точка границы, а его цвет - цвет границы.
    Возвращает ((bx, by), цвет_границы) или (None, None), если граница не найдена.
    """
    w, _ = img.size
    pix = img.load()
    inner = pix[x, y]
    while x < w - 1:
        x += 1
        if pix[x, y] != inner:
            return (x, y), pix[x, y]
    return None, None


def trace_border(img, start, border_color):
    """
    Обход границы (трассировка по 8 соседям, алгоритм Мура).
    """
    w, h = img.size
    pix = img.load()

    def is_border(px, py):
        return 0 <= px < w and 0 <= py < h and pix[px, py] == border_color

    contour = [start]
    p = start
    back = 4          # в начальную точку мы пришли слева 
    second = None
    max_steps = 4 * w * h

    for _ in range(max_steps):
        for i in range(1, 9):
            d = (back + i) % 8
            q = (p[0] + DIRS[d][0], p[1] + DIRS[d][1])
            if is_border(*q):
                break
        else:
            return contour  # изолированная точка - обходить нечего

        # новое направление "назад": последний проверенный сосед, не входящий в границу
        pd = (back + i - 1) % 8
        prev = (p[0] + DIRS[pd][0], p[1] + DIRS[pd][1])
        back = DIRS.index((prev[0] - q[0], prev[1] - q[1]))

        if second is None:
            second = q
        elif p == start and q == second:
            break  # вернулись в начало тем же шагом - граница замкнулась

        contour.append(q)
        p = q

    # последняя добавленная точка - повтор start, убираем её
    if len(contour) > 1 and contour[-1] == start:
        contour.pop()
    return contour


# ---------------------------------------------------------------------------
# Интерфейс вкладки "Задание 1"
# ---------------------------------------------------------------------------

def rgb_to_hex(c):
    return "#%02x%02x%02x" % c


class Task1Frame(ttk.Frame):
    MODES = [
        ("Рисование области", "draw"),
        ("1а: заливка цветом", "fill_color"),
        ("1б: заливка рисунком", "fill_pattern"),
        ("1в: выделение границы", "border"),
    ]

    def __init__(self, master):
        super().__init__(master)
        self.img = Image.new("RGB", (CANVAS_W, CANVAS_H), BACKGROUND)
        self.draw = ImageDraw.Draw(self.img)

        self.line_color = (0, 0, 0)
        self.fill_color = (255, 190, 0)
        self.highlight_color = (255, 0, 0)
        self.pattern = None
        self.contour = []
        self.last_point = None

        self.mode = tk.StringVar(value="draw")
        self.line_width = tk.IntVar(value=2)
        self.anchor_to_click = tk.BooleanVar(value=False)

        self._build_ui()
        self.refresh()

    # ----- построение интерфейса -----

    def _build_ui(self):
        panel = ttk.Frame(self, padding=6)
        panel.pack(side=tk.LEFT, fill=tk.Y)

        box = ttk.LabelFrame(panel, text="Режим (щелчок по холсту)", padding=6)
        box.pack(fill=tk.X, pady=3)
        for text, value in self.MODES:
            ttk.Radiobutton(box, text=text, value=value, variable=self.mode,
                            command=self.refresh).pack(anchor=tk.W)

        box = ttk.LabelFrame(panel, text="Рисование", padding=6)
        box.pack(fill=tk.X, pady=3)
        self.line_color_btn = tk.Button(box, text="Цвет линии", command=self.choose_line_color)
        self.line_color_btn.pack(fill=tk.X)
        row = ttk.Frame(box)
        row.pack(fill=tk.X, pady=3)
        ttk.Label(row, text="Толщина:").pack(side=tk.LEFT)
        ttk.Spinbox(row, from_=1, to=10, width=4, textvariable=self.line_width).pack(side=tk.LEFT)
        ttk.Button(box, text="Пример области с отверстиями", command=self.draw_example).pack(fill=tk.X)
        ttk.Button(box, text="Очистить холст", command=self.clear).pack(fill=tk.X, pady=(3, 0))

        box = ttk.LabelFrame(panel, text="1а. Заливка цветом", padding=6)
        box.pack(fill=tk.X, pady=3)
        self.fill_color_btn = tk.Button(box, text="Цвет заливки", command=self.choose_fill_color)
        self.fill_color_btn.pack(fill=tk.X)

        box = ttk.LabelFrame(panel, text="1б. Заливка рисунком", padding=6)
        box.pack(fill=tk.X, pady=3)
        ttk.Button(box, text="Загрузить рисунок...", command=self.load_pattern).pack(fill=tk.X)
        self.pattern_label = ttk.Label(box, text="Рисунок не загружен", wraplength=190)
        self.pattern_label.pack(fill=tk.X, pady=3)
        ttk.Checkbutton(box, text="Привязать рисунок\nк точке щелчка",
                        variable=self.anchor_to_click).pack(anchor=tk.W)

        box = ttk.LabelFrame(panel, text="1в. Выделение границы", padding=6)
        box.pack(fill=tk.X, pady=3)
        ttk.Button(box, text="Загрузить изображение...", command=self.load_image).pack(fill=tk.X)
        self.highlight_btn = tk.Button(box, text="Цвет выделения", command=self.choose_highlight_color)
        self.highlight_btn.pack(fill=tk.X, pady=3)
        ttk.Button(box, text="Сохранить точки границы...", command=self.save_contour).pack(fill=tk.X)

        self.status = ttk.Label(panel, text="", wraplength=200, justify=tk.LEFT)
        self.status.pack(fill=tk.X, pady=8)

        self.canvas = tk.Canvas(self, width=CANVAS_W, height=CANVAS_H,
                                highlightthickness=1, highlightbackground="gray", cursor="crosshair")
        self.canvas.pack(side=tk.LEFT, padx=6, pady=6, anchor=tk.N)
        self.photo = ImageTk.PhotoImage(self.img)
        self.canvas.create_image(0, 0, image=self.photo, anchor=tk.NW)

        self.canvas.bind("<Button-1>", self.on_press)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_release)

        self._update_color_buttons()

    def _update_color_buttons(self):
        for btn, color in ((self.line_color_btn, self.line_color),
                           (self.fill_color_btn, self.fill_color),
                           (self.highlight_btn, self.highlight_color)):
            fg = "white" if sum(color) < 380 else "black"
            btn.configure(bg=rgb_to_hex(color), fg=fg, activebackground=rgb_to_hex(color))

    def set_status(self, text):
        self.status.configure(text=text)

    # ----- отображение -----

    def refresh(self, show_contour=False):
        """Выводит изображение на холст; при show_contour - поверх рисуется найденная граница."""
        self.canvas.delete("marker")
        if show_contour and self.contour:
            shown = self.img.copy()
            sp = shown.load()
            for x, y in self.contour:
                sp[x, y] = self.highlight_color
            self.photo.paste(shown)
            sx, sy = self.contour[0]
            self.canvas.create_oval(sx - 4, sy - 4, sx + 4, sy + 4,
                                    outline="blue", width=2, tags="marker")
        else:
            self.photo.paste(self.img)

    # ----- выбор цветов -----

    def _ask_color(self, current):
        rgb, _ = colorchooser.askcolor(color=rgb_to_hex(current), parent=self)
        return tuple(int(c) for c in rgb) if rgb else current

    def choose_line_color(self):
        self.line_color = self._ask_color(self.line_color)
        self._update_color_buttons()

    def choose_fill_color(self):
        self.fill_color = self._ask_color(self.fill_color)
        self._update_color_buttons()

    def choose_highlight_color(self):
        self.highlight_color = self._ask_color(self.highlight_color)
        self._update_color_buttons()
        self.refresh(show_contour=True)

    # ----- файлы -----

    def load_pattern(self):
        path = filedialog.askopenfilename(
            parent=self, title="Рисунок для заливки",
            initialdir=PATTERNS_DIR if os.path.isdir(PATTERNS_DIR) else None,
            filetypes=[("Изображения", "*.png *.jpg *.jpeg *.bmp *.gif"), ("Все файлы", "*.*")])
        if not path:
            return
        try:
            self.pattern = Image.open(path).convert("RGB")
        except OSError as e:
            messagebox.showerror("Ошибка", f"Не удалось открыть файл:\n{e}", parent=self)
            return
        pw, ph = self.pattern.size
        if pw >= CANVAS_W and ph >= CANVAS_H:
            kind = "большой - берётся напрямую, без повторения"
        else:
            kind = "небольшой - повторяется циклически"
        self.pattern_label.configure(text=f"{os.path.basename(path)}\n{pw}x{ph}, {kind}")
        self.mode.set("fill_pattern")

    def load_image(self):
        path = filedialog.askopenfilename(
            parent=self, title="Исходное изображение",
            filetypes=[("Изображения", "*.png *.jpg *.jpeg *.bmp *.gif"), ("Все файлы", "*.*")])
        if not path:
            return
        try:
            src = Image.open(path).convert("RGB")
        except OSError as e:
            messagebox.showerror("Ошибка", f"Не удалось открыть файл:\n{e}", parent=self)
            return
        self.img.paste(BACKGROUND, (0, 0, CANVAS_W, CANVAS_H))
        self.img.paste(src.crop((0, 0, min(src.width, CANVAS_W), min(src.height, CANVAS_H))), (0, 0))
        self.contour = []
        self.mode.set("border")
        self.refresh()
        self.set_status("Изображение загружено. Щёлкните внутри области, чтобы выделить её границу.")

    def save_contour(self):
        if not self.contour:
            messagebox.showinfo("Граница", "Сначала выделите границу (режим 1в).", parent=self)
            return
        path = filedialog.asksaveasfilename(parent=self, defaultextension=".txt",
                                            filetypes=[("Текст", "*.txt")])
        if path:
            with open(path, "w", encoding="utf-8") as f:
                for x, y in self.contour:
                    f.write(f"{x} {y}\n")
            self.set_status(f"Сохранено {len(self.contour)} точек границы.")

    # ----- рисование -----

    def clear(self):
        self.img.paste(BACKGROUND, (0, 0, CANVAS_W, CANVAS_H))
        self.contour = []
        self.refresh()
        self.set_status("")

    def _draw_segment(self, p, q):
        width = max(1, self.line_width.get())
        self.draw.line([p, q], fill=self.line_color, width=width)
        if width > 2:  # скругляем стыки толстых линий
            r = width / 2
            self.draw.ellipse([q[0] - r, q[1] - r, q[0] + r, q[1] + r], fill=self.line_color)

    def draw_example(self):
        """Произвольная область с двумя отверстиями - для быстрой проверки."""
        c, w = self.line_color, max(1, self.line_width.get())
        outer = [(120, 80), (420, 40), (760, 120), (820, 330), (650, 540), (300, 560), (180, 420), (80, 260)]
        self.draw.line(outer + [outer[0]], fill=c, width=w, joint="curve")
        self.draw.ellipse([250, 180, 400, 330], outline=c, width=w)
        self.draw.polygon([(500, 250), (650, 220), (680, 400), (560, 450), (470, 380)], outline=c, width=w)
        self.contour = []
        self.refresh()

    # ----- обработка мыши -----

    def _in_canvas(self, x, y):
        return 0 <= x < CANVAS_W and 0 <= y < CANVAS_H

    def on_press(self, event):
        x, y = event.x, event.y
        if not self._in_canvas(x, y):
            return
        mode = self.mode.get()
        if mode == "draw":
            self.last_point = (x, y)
            self._draw_segment((x, y), (x, y))
            self.contour = []
            self.refresh()
        elif mode == "fill_color":
            self.do_fill(x, y, pattern=False)
        elif mode == "fill_pattern":
            self.do_fill(x, y, pattern=True)
        elif mode == "border":
            self.do_border(x, y)

    def on_drag(self, event):
        if self.mode.get() != "draw" or self.last_point is None:
            return
        x = min(max(event.x, 0), CANVAS_W - 1)
        y = min(max(event.y, 0), CANVAS_H - 1)
        self._draw_segment(self.last_point, (x, y))
        self.last_point = (x, y)
        self.refresh()

    def on_release(self, event):
        self.last_point = None

    # ----- запуск алгоритмов -----

    def do_fill(self, x, y, pattern):
        if pattern and self.pattern is None:
            messagebox.showinfo("Заливка рисунком", "Сначала загрузите рисунок.", parent=self)
            return
        self.contour = []
        self.configure(cursor="watch")
        self.update_idletasks()
        t0 = time.perf_counter()
        if pattern:
            origin = (x, y) if self.anchor_to_click.get() else (0, 0)
            count = run_with_big_stack(fill_with_pattern, self.img, x, y, self.pattern, origin)
        else:
            count = run_with_big_stack(fill_with_color, self.img, x, y, self.fill_color)
        dt = time.perf_counter() - t0
        self.configure(cursor="")
        self.refresh()
        self.set_status(f"Закрашено пикселов: {count}\nВремя: {dt:.2f} с")

    def do_border(self, x, y):
        start, color = find_border_start(self.img, x, y)
        if start is None:
            self.contour = []
            self.refresh()
            self.set_status("Справа от точки щелчка граница не найдена.")
            return
        self.contour = trace_border(self.img, start, color)
        self.refresh(show_contour=True)
        head = ", ".join(f"({px},{py})" for px, py in self.contour[:5])
        self.set_status(f"Цвет границы: {rgb_to_hex(color)}\n"
                        f"Точек в обходе: {len(self.contour)}\n"
                        f"Начало (синий круг): {self.contour[0]}\n"
                        f"Первые точки: {head}...")
