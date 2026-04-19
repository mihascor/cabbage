from PyQt6.QtWidgets import QApplication, QMainWindow, QTabWidget
from script.update_price_history import need_update, run_update

from app.ui.parser_tab import ParserTab
from app.ui.table_tab import TableTab

import ctypes
import logging
import os
import sys

# --- глобальный перехват всех исключений ---
def global_exception_hook(exctype, value, traceback):
    import logging

    logging.exception("Глобальная ошибка", exc_info=(exctype, value, traceback))

    print(f"Ошибка: {value}")  # попадёт в лог через stdout


# --- настройка логирования ---
LOG_DIR = r"C:\cabbage\logs"
os.makedirs(LOG_DIR, exist_ok=True)

logging.basicConfig(
    filename=os.path.join(LOG_DIR, "app.log"),
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    encoding="utf-8"
)

# перехват print → в лог
class StreamToLogger:
    def __init__(self, level):
        self.level = level

    def write(self, message):
        message = message.strip()
        if message:
            logging.log(self.level, message)

    def flush(self):
        pass


sys.stdout = StreamToLogger(logging.INFO)
sys.stderr = StreamToLogger(logging.ERROR)


# --- Включение тёмного title bar в Windows ---
def set_dark_title_bar(hwnd):
    DWMWA_USE_IMMERSIVE_DARK_MODE = 20
    value = ctypes.c_int(1)
    ctypes.windll.dwmapi.DwmSetWindowAttribute(
        hwnd,
        DWMWA_USE_IMMERSIVE_DARK_MODE,
        ctypes.byref(value),
        ctypes.sizeof(value)
    )


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Анализ ОИ")
        self.resize(800, 600)

        tabs = QTabWidget()
        tabs.addTab(ParserTab(), "Парсер")
        tabs.addTab(TableTab(), "Таблица - ОИ")

        tabs.setCurrentIndex(1)  # ← открыть вторую вкладку

        self.setCentralWidget(tabs)

# --- Запуск приложения ---
def run_app():
    try:

        # --- проверка необходимости обновления цен ---
        if need_update():
            run_update()
            
        app = QApplication([])
        # --- подключаем глобальный перехват ---
        sys.excepthook = global_exception_hook

        # --- тёмная тема ---
        app.setStyleSheet("""
        /* --- Общий фон --- */
        QWidget {
            background-color: #2b2b2b;
            color: #dddddd;
            font-size: 14px;
        }

        /* --- Вкладки --- */
        QTabWidget::pane {
            border: 1px solid #444;
        }

        QTabBar::tab {
            background: #3c3f41;
            padding: 6px 12px;
            border: 1px solid #444;
            margin-right: 2px;
        }

        QTabBar::tab:selected {
            background: #2b2b2b;
            border-bottom: 2px solid #6a9fb5;
        }

        QTabBar::tab:hover {
            background: #505354;
        }

        /* --- Кнопка --- */
        QPushButton {
            background-color: #3c3f41;
            border: 1px solid #555;
            padding: 6px 12px;
            border-radius: 4px;
        }

        QPushButton:hover {
            background-color: #505354;
        }

        QPushButton:pressed {
            background-color: #2b2b2b;
        }

        /* --- Логи --- */
        QTextEdit {
            background-color: #1e1e1e;
            border: 1px solid #444;
            padding: 5px;
        }

        /* --- Таблица --- */
        QTableWidget {
            background-color: #2b2b2b;
            gridline-color: #444;
            selection-background-color: #3c3f41;
        }

        /* --- Верхний header --- */
        QHeaderView::section {
            background-color: #3c3f41;
            color: #dddddd;
            border: 1px solid #444;
            padding: 4px;
        }

        /* --- Левый header (нумерация строк) --- */
        QTableCornerButton::section {
            background-color: #3c3f41;
            border: 1px solid #444;
        }                                                  
        """)

        window = MainWindow()
        window.showMaximized()

        # --- тёмный title bar ---
        set_dark_title_bar(int(window.winId()))

        app.exec()

    except Exception as e:
        logging.exception("Критическая ошибка приложения")
        raise

if __name__ == "__main__":
    run_app()