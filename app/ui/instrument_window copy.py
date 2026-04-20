from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QFrame
)
from PyQt6.QtCore import Qt
# --- графические виджеты ---
from app.ui.widgets.price_graph_widget import PriceGraphWidget
from app.ui.widgets.oi_graph_widget import OiGraphWidget

# --- слой данных (SQL) ---
from script.instrument_repository import get_price_history, get_oi_history

# Окно аналитики инструмента
class InstrumentWindow(QWidget):
    """
    Плавающее окно аналитики инструмента.
    Пока содержит только каркас:
    - имя инструмента слева сверху
    - две области под будущие графики
    """

    # --- конструктор ---
    def __init__(self, name: str, parent=None):
        super().__init__(parent)

        self.name = name

        # --- флаги окна: плавающее, всегда поверх родителя ---
        self.setWindowFlags(
            # Qt.WindowType.Tool | Qt.WindowType.WindowStaysOnTopHint # --- для плавающего окна без рамки ---
            Qt.WindowType.Window | Qt.WindowType.WindowStaysOnTopHint # --- для обычного окна с рамкой ---
        )

        self.setWindowTitle(f"Анализ ОИ: {name}")
        self.resize(1400, 800)

        # --- открыть окно развернутым на весь экран ---
        self.showMaximized()

        # --- тёмный title bar как у главного окна ---
        from app.main import set_dark_title_bar
        set_dark_title_bar(int(self.winId()))

        # --- основной layout ---
        main_layout = QVBoxLayout(self)

        # --- заголовок с именем инструмента ---
        self.label_name = QLabel(name)
        self.label_name.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        self.label_name.setStyleSheet("font-size: 16px; font-weight: bold;")
        main_layout.addWidget(self.label_name)

        # --- зона под графики (один над другим) ---
        graphs_layout = QVBoxLayout()

        # Верхний график
        self.graph_top = QFrame()
        self.graph_top.setFrameShape(QFrame.Shape.Box)

        # Нижний график
        self.graph_bottom = QFrame()
        self.graph_bottom.setFrameShape(QFrame.Shape.Box)

        # заставляем занимать всё пространство
        graphs_layout.addWidget(self.graph_top, stretch=1)
        graphs_layout.addWidget(self.graph_bottom, stretch=1)

        main_layout.addLayout(graphs_layout, stretch=1)

    # --- метод для активации окна ---
    def activate(self):
        """Поднять окно поверх и дать ему фокус."""
        self.show()
        self.raise_()
        self.activateWindow()
