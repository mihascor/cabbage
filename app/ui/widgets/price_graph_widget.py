# Рисует график цены для выбранного инструмента.
from PyQt6.QtWidgets import QWidget
from PyQt6.QtGui import QPainter, QPen, QColor
from PyQt6.QtCore import Qt


class PriceGraphWidget(QWidget):
    """
    График цены в виде горизонтальных баров:
    high — верхняя точка, low — нижняя точка.
    Данные задаются методом set_data().
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.data = []  # List[(date, high, low)]

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

        # --- определяем диапазон цен ---
        highs = [row[1] for row in self.data]
        lows = [row[2] for row in self.data]

        max_price = max(highs)
        min_price = min(lows)
        price_range = max_price - min_price if max_price != min_price else 1

        # --- перо ---
        pen = QPen(QColor("#6fa8dc"))  # светло-синий
        pen.setWidth(3)
        painter.setPen(pen)

        count = len(self.data)

        for idx, (_, high, low) in enumerate(self.data):
            # X координата равномерно распределена
            x = left_margin + int((idx / (count - 1)) * w) if count > 1 else left_margin

            # Перевод цены в координаты Y
            y_high = top_margin + int((max_price - high) / price_range * h)
            y_low = top_margin + int((max_price - low) / price_range * h)

            painter.drawLine(x, y_high, x, y_low)
