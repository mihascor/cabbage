from PyQt6.QtWidgets import QWidget, QPushButton, QVBoxLayout, QHBoxLayout, QTextEdit, QLabel
from PyQt6.QtCore import QThread, pyqtSignal
from datetime import datetime
import json
import os

from script import parser_moex


SETTINGS_FILE = r"C:\cabbage\data\last_run.json"


class ParserWorker(QThread):
    log_signal = pyqtSignal(str)
    finished_signal = pyqtSignal()

    def run(self):
        try:
            parser_moex.main(log_callback=self.log_signal.emit)
        except Exception as e:
            self.log_signal.emit(f"Ошибка: {e}")
        finally:
            self.finished_signal.emit()


class ParserTab(QWidget):
    def __init__(self):
        super().__init__()

        layout = QVBoxLayout()

        # --- Верхняя строка ---
        top_layout = QHBoxLayout()

        self.btn = QPushButton("Запустить парсер")
        self.btn.clicked.connect(self.run_parser)

        self.last_run_label = QLabel("Последний запуск: —")

        top_layout.addWidget(self.btn)
        top_layout.addWidget(self.last_run_label)
        top_layout.addStretch()

        # --- Логи ---
        self.log = QTextEdit()
        self.log.setReadOnly(True)

        layout.addLayout(top_layout)
        layout.addWidget(self.log)

        self.setLayout(layout)

        self.load_last_run()

    # -------------------------
    # ЛОГИКА
    # -------------------------

    def run_parser(self):
        self.log.append("Запуск parser_moex...")

        self.worker = ParserWorker()
        self.worker.log_signal.connect(self.log.append)
        self.worker.finished_signal.connect(self.on_finished)

        self.worker.start()

    def on_finished(self):
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        self.save_last_run(now)
        self.last_run_label.setText(f"Последний запуск: {now}")

        self.log.append("Готово")

    # -------------------------
    # СОХРАНЕНИЕ ВРЕМЕНИ
    # -------------------------

    def save_last_run(self, value):
        with open(SETTINGS_FILE, "w") as f:
            json.dump({"last_run": value}, f)

    def load_last_run(self):
        if not os.path.exists(SETTINGS_FILE):
            return

        with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)

        self.last_run_label.setText(
            f"Последний запуск: {data.get('last_run', '—')}"
        )