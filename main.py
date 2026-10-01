"""
Лабораторная работа №3 «Растровые алгоритмы». Команда «Графические».

Запуск:  python main.py   (нужен Pillow: pip install -r requirements.txt)
"""

import tkinter as tk
from tkinter import ttk

from task1 import Task1Frame
from task2 import Task2Frame
from task3 import Task3Frame


def main():
    root = tk.Tk()
    root.title("Растровые алгоритмы")

    tabs = ttk.Notebook(root)
    tabs.pack(fill=tk.BOTH, expand=True)

    tabs.add(Task1Frame(tabs), text="Задание 1: заливка и граница")
    tabs.add(Task2Frame(tabs), text="Задание 2: отрезки")
    tabs.add(Task3Frame(tabs), text="Задание 3: растровый треугольник")
    root.mainloop()


if __name__ == "__main__":
    main()
