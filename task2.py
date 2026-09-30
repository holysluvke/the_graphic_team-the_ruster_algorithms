import tkinter as tk
from math import floor
from tkinter import ttk


class LineDrawer:

    def __init__(self, canvas, pixel_size=3):
        self.canvas = canvas
        self.pixel_size = pixel_size

    def _draw_pixel(self, x, y, color="black"):
        px = x * self.pixel_size
        py = y * self.pixel_size

        self.canvas.create_rectangle(
            px,
            py,
            px + self.pixel_size,
            py + self.pixel_size,
            fill=color,
            outline=color,
        )

    def _ipart(self, x):
        return floor(x)

    def _round_half_up(self, x):
        return floor(x + 0.5)

    def _fpart(self, x):
        return x - floor(x)

    def _rfpart(self, x):
        return 1 - self._fpart(x)

    def _blend_color(self, intensity):
        intensity = max(0.0, min(1.0, intensity))
        value = int(255 * (1 - intensity))
        return f"#{value:02x}{value:02x}{value:02x}"

    def _plot_wu(self, x, y, brightness):
        if brightness <= 0:
            return

        color = self._blend_color(brightness)

        px = x * self.pixel_size
        py = y * self.pixel_size

        self.canvas.create_rectangle(
            px,
            py,
            px + self.pixel_size,
            py + self.pixel_size,
            fill=color,
            outline=color,
        )

    def bresenham(self, x0, y0, x1, y1, color="black"):
        dx = abs(x1 - x0)
        dy = abs(y1 - y0)

        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1

        err = dx - dy

        while True:
            self._draw_pixel(x0, y0, color)

            if x0 == x1 and y0 == y1:
                break

            e2 = 2 * err

            if e2 > -dy:
                err -= dy
                x0 += sx

            if e2 < dx:
                err += dx
                y0 += sy

    def wu(self, x0, y0, x1, y1):
        steep = abs(y1 - y0) > abs(x1 - x0)

        if steep:
            x0, y0 = y0, x0
            x1, y1 = y1, x1

        if x0 > x1:
            x0, x1 = x1, x0
            y0, y1 = y1, y0

        dx = x1 - x0
        dy = y1 - y0

        gradient = dy / dx if dx != 0 else 0

        xend = self._round_half_up(x0)
        yend = y0 + gradient * (xend - x0)

        xgap = self._rfpart(x0 + 0.5)

        xpxl1 = xend
        ypxl1 = self._ipart(yend)

        if steep:
            self._plot_wu(ypxl1, xpxl1, self._rfpart(yend) * xgap)

            self._plot_wu(ypxl1 + 1, xpxl1, self._fpart(yend) * xgap)
        else:
            self._plot_wu(xpxl1, ypxl1, self._rfpart(yend) * xgap)

            self._plot_wu(xpxl1, ypxl1 + 1, self._fpart(yend) * xgap)

        intery = yend + gradient

        xend = self._round_half_up(x1)
        yend = y1 + gradient * (xend - x1)

        xgap = self._fpart(x1 + 0.5)

        xpxl2 = xend
        ypxl2 = self._ipart(yend)

        if steep:
            self._plot_wu(ypxl2, xpxl2, self._rfpart(yend) * xgap)

            self._plot_wu(ypxl2 + 1, xpxl2, self._fpart(yend) * xgap)
        else:
            self._plot_wu(xpxl2, ypxl2, self._rfpart(yend) * xgap)

            self._plot_wu(xpxl2, ypxl2 + 1, self._fpart(yend) * xgap)

        if steep:
            for x in range(xpxl1 + 1, xpxl2):
                self._plot_wu(self._ipart(intery), x, self._rfpart(intery))

                self._plot_wu(self._ipart(intery) + 1, x, self._fpart(intery))

                intery += gradient
        else:
            for x in range(xpxl1 + 1, xpxl2):
                self._plot_wu(x, self._ipart(intery), self._rfpart(intery))

                self._plot_wu(x, self._ipart(intery) + 1, self._fpart(intery))

                intery += gradient

    def clear(self):
        self.canvas.delete("all")


class Task2Frame(ttk.Frame):

    def __init__(self, master):
        super().__init__(master)

        self.pixel_size = 3
        self.canvas_size = 500

        self._create_controls()
        self._create_canvases()
        self._create_drawers()

        self.draw_lines()

    def _create_controls(self):
        controls = ttk.Frame(self)
        controls.pack(fill=tk.X, padx=10, pady=10)

        ttk.Label(controls, text="x0:").grid(row=0, column=0, padx=(0, 5))

        self.entry_x0 = ttk.Entry(controls, width=7)
        self.entry_x0.insert(0, "10")
        self.entry_x0.grid(row=0, column=1, padx=(0, 10))

        ttk.Label(controls, text="y0:").grid(row=0, column=2, padx=(0, 5))

        self.entry_y0 = ttk.Entry(controls, width=7)
        self.entry_y0.insert(0, "10")
        self.entry_y0.grid(row=0, column=3, padx=(0, 10))

        ttk.Label(controls, text="x1:").grid(row=0, column=4, padx=(0, 5))

        self.entry_x1 = ttk.Entry(controls, width=7)
        self.entry_x1.insert(0, "150")
        self.entry_x1.grid(row=0, column=5, padx=(0, 10))

        ttk.Label(controls, text="y1:").grid(row=0, column=6, padx=(0, 5))

        self.entry_y1 = ttk.Entry(controls, width=7)
        self.entry_y1.insert(0, "100")
        self.entry_y1.grid(row=0, column=7, padx=(0, 15))

        ttk.Button(controls, text="Нарисовать", command=self.draw_lines).grid(
            row=0, column=8, padx=5
        )

        ttk.Button(controls, text="Очистить", command=self.clear).grid(
            row=0, column=9, padx=5
        )

        self.error_label = ttk.Label(self, text="")
        self.error_label.pack()

    def _create_canvases(self):
        canvases = ttk.Frame(self)
        canvases.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        left_frame = ttk.Frame(canvases)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        right_frame = ttk.Frame(canvases)
        right_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        ttk.Label(
            left_frame,
            text="Целочисленный алгоритм Брезенхема",
            font=("Segoe UI", 12, "bold"),
        ).pack(pady=(0, 5))

        self.canvas_bres = tk.Canvas(
            left_frame,
            width=self.canvas_size,
            height=self.canvas_size,
            bg="white",
            highlightthickness=1,
        )
        self.canvas_bres.pack()

        ttk.Label(right_frame, text="Алгоритм Ву", font=("Segoe UI", 12, "bold")).pack(
            pady=(0, 5)
        )

        self.canvas_wu = tk.Canvas(
            right_frame,
            width=self.canvas_size,
            height=self.canvas_size,
            bg="white",
            highlightthickness=1,
        )
        self.canvas_wu.pack()

    def _create_drawers(self):
        self.bresenham = LineDrawer(self.canvas_bres, pixel_size=self.pixel_size)

        self.wu = LineDrawer(self.canvas_wu, pixel_size=self.pixel_size)

    def draw_lines(self):
        try:
            x0 = int(self.entry_x0.get())
            y0 = int(self.entry_y0.get())
            x1 = int(self.entry_x1.get())
            y1 = int(self.entry_y1.get())
        except ValueError:
            self.error_label.config(text="Координаты должны быть целыми числами.")
            return

        max_coord = self.canvas_size // self.pixel_size

        if not (
            0 <= x0 <= max_coord
            and 0 <= y0 <= max_coord
            and 0 <= x1 <= max_coord
            and 0 <= y1 <= max_coord
        ):
            self.error_label.config(text=f"Координаты должны быть от 0 до {max_coord}.")
            return

        self.error_label.config(text="")

        self.bresenham.clear()
        self.wu.clear()

        self.bresenham.bresenham(x0, y0, x1, y1)

        self.wu.wu(x0, y0, x1, y1)

    def clear(self):
        self.bresenham.clear()
        self.wu.clear()
        self.error_label.config(text="")
