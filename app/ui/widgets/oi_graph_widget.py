# Рисует график ОИ для выбранного инструмента.
from PyQt6.QtWidgets import QWidget
from PyQt6.QtGui import QPainter, QPen, QColor
from PyQt6.QtCore import Qt


class OiGraphWidget(QWidget):
    """
    График ОИ:
    coef_fl — красная линия
    coef_ul — светло-синяя линия
    Диапазон Y: -20 .. 20
    Данные задаются методом set_data().
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.data = []  # List[(date, coef_fl, coef_ul)]

    # ------------------------------------------------------------
    # Передача данных в виджет
    # ------------------------------------------------------------
    def set_data(self, data):
        self.data = data
        self.update()

    # ------------------------------------------------------------
    # Отрисовка
    # ------------------------------------------------------------
    def paintEvent(self, event):
        if not self.data:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # --- отступы ---
        left_margin = 5
        right_margin = 20
        top_margin = 5
        bottom_margin = 5

        w = self.width() - left_margin - right_margin
        h = self.height() - top_margin - bottom_margin

        count = len(self.data)

        # --- подготовка пера ---
        pen_fl = QPen(QColor("red"))
        pen_fl.setWidth(3)

        pen_ul = QPen(QColor("#6fa8dc"))
        pen_ul.setWidth(3)

        # --- функция перевода значения в Y координату ---
        def value_to_y(value):
            # диапазон -20 .. 20
            return top_margin + int((20 - value) / 40 * h)

        # --- рисуем линии ---
        for i in range(count - 1):
            x1 = left_margin + int((i / (count - 1)) * w)
            x2 = left_margin + int(((i + 1) / (count - 1)) * w)

            _, fl1, ul1 = self.data[i]
            _, fl2, ul2 = self.data[i + 1]

            # coef_fl линия
            painter.setPen(pen_fl)
            painter.drawLine(x1, value_to_y(fl1), x2, value_to_y(fl2))

            # coef_ul линия
            painter.setPen(pen_ul)
            painter.drawLine(x1, value_to_y(ul1), x2, value_to_y(ul2))
