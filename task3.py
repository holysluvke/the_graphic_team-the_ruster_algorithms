import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk

class Point:

    def __init__(self, x, y):
        self.x = x
        self.y = y

W, H = 420, 420

def rusterize_triangle():
    img = Image.new("RGB", (W, H), "white")
    pixels = list(img.getdata())

    A, A_color = Point(42, 63), (127, 63, 21)
    B, B_color = Point(279, 305), (249, 0, 180)
    C, C_color = Point(356, 88), (98, 14, 88)

    S_ABC = ((B.x - A.x) * (C.y - A.y) - (C.x - A.x) * (B.y - A.y) ) / 2
    if (S_ABC == 0):
        raise Exception("треугольник оказался вырожденным((")

    min_x = min(A.x, B.x, C.x)
    min_y = min(A.y, B.y, C.y)
    max_x = max(A.x, B.x, C.x)
    max_y = max(A.y, B.y, C.y)

    rect_A = Point(min_x, min_y)
    rect_B = Point(rect_A.x, max_y)
    rect_C = Point(max_x, rect_B.y)
    rect_D = Point(rect_C.x, rect_A.y)

    for x in range(min_x, max_x + 1):
        for y in range(min_y, max_y + 1):
            a = (((B.x - x) * (C.y - y) - (C.x - x) * (B.y - y)) / 2) / S_ABC
            b = (((C.x - x) * (A.y - y) - (A.x - x) * (C.y - y)) / 2) / S_ABC
            c = (((A.x - x) * (B.y - y) - (B.x - x) * (A.y - y)) / 2) / S_ABC

            if a < 0 or b < 0 or c < 0:
                continue

            red = round(a * A_color[0] + b * B_color[0] + c * C_color[0])
            green = round(a * A_color[1] + b * B_color[1] + c * C_color[1])
            blue = round(a * A_color[2] + b * B_color[2] + c * C_color[2])

            pixels[y * W + x] = (red, green, blue)

    img.putdata(pixels)

    return img

def Task3Frame(master):
    tab = ttk.Frame(master)

    ttk.Label(tab, text="Градиентный треугольник (барицентрические координаты)",
              font=("Segoe UI", 14)).pack(pady=(20, 10))

    picture = ttk.Label(tab)
    picture.pack(padx=10, pady=10)

    def draw():
        photo = ImageTk.PhotoImage(rusterize_triangle())
        picture.config(image=photo)
        picture.image = photo

    ttk.Button(tab, text="Нарисовать треугольник", command=draw).pack(pady=(0, 10))

    return tab