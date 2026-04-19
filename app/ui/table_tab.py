import json
import os

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QTableWidget,
    QTableWidgetItem,
    QComboBox
)

from script.load_table import load_open_interest
from PyQt6.QtGui import QColor, QFont
from PyQt6.QtWidgets import QPushButton, QWidget, QHBoxLayout
from app.ui.instrument_window import InstrumentWindow

# Вкладка "Таблица"
class TableTab(QWidget):
    def __init__(self):
        super().__init__()

        # --- файл для хранения сигналов ---
        self.signals_file = r"C:\cabbage\data\signals.json"

        layout = QVBoxLayout()

        self.table = QTableWidget()
        layout.addWidget(self.table)

        self.setLayout(layout)

        # --- хранилище открытых плавающих окон по name ---
        self.instrument_windows = {}

        self.signals_state = self.load_signals_state()
        self.load_data()

    #  --- функции для сохранения и загрузки состояния сигналов ---
    def load_signals_state(self):
        if not os.path.exists(self.signals_file):
            return {}
        try:
            with open(self.signals_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
        
    def save_signals_state(self, state: dict):
        os.makedirs(os.path.dirname(self.signals_file), exist_ok=True)
        with open(self.signals_file, "w", encoding="utf-8") as f:
            json.dump(state, f, ensure_ascii=False, indent=2)

# --- функция для обработки нажатия кнопки выбора ---
    def toggle_choice(self, row_idx, name, btn_choice):
        state = self.signals_state.get(name, False)
        new_state = not state

        self.signals_state[name] = new_state
        self.save_signals_state(self.signals_state)

        # обновляем кнопку
        btn_choice.setText("Yes" if new_state else "No")

        # обновляем строку
        for col in range(0, 5):  # только первые 5 колонок
            item = self.table.item(row_idx, col)
            if item:
                if new_state:
                    item.setBackground(QColor("#797a7a"))
                else:
                    item.setBackground(QColor("#2b2b2b"))
        # обновляем кнопку
        if new_state:
            btn_choice.setStyleSheet("background-color: #797a7a;")
        else:
            btn_choice.setStyleSheet("")

    # --- открытие плавающего окна анализа ---
    def open_instrument_window(self, name: str):
        # если окно уже открыто — просто активируем
        if name in self.instrument_windows:
            self.instrument_windows[name].activate()
            return

        # иначе создаём новое и сохраняем ссылку
        window = InstrumentWindow(name)
        self.instrument_windows[name] = window
        window.show()

    # -------------------------------
    # Загрузка данных в таблицу
    # -------------------------------
    def load_data(self):
        columns, rows = load_open_interest()

        # --- настройка таблицы ---
        self.table.setColumnCount(len(columns))
        self.table.setRowCount(len(rows))
        self.table.setHorizontalHeaderLabels(columns)

        # --- добавляем колонку "Направление" ---
        signal_col = self.table.columnCount()
        self.table.insertColumn(signal_col)
        self.table.setHorizontalHeaderItem(
            signal_col,
            QTableWidgetItem("Направление")
        )

        # --- добавляем колонку "Кооф ФЛ" ---
        coef_fl_col = self.table.columnCount()
        self.table.insertColumn(coef_fl_col)
        self.table.setHorizontalHeaderItem(
            coef_fl_col,
            QTableWidgetItem("Кооф ФЛ")
        )

        # --- добавляем колонку "Кооф ЮЛ" ---
        coef_ul_col = self.table.columnCount()
        self.table.insertColumn(coef_ul_col)
        self.table.setHorizontalHeaderItem(
            coef_ul_col,
            QTableWidgetItem("Кооф ЮЛ")
        )

        # --- добавляем колонку "Выбор" ---
        choice_col = self.table.columnCount()
        self.table.insertColumn(choice_col)
        self.table.setHorizontalHeaderItem(
            choice_col,
            QTableWidgetItem("Выбор")
        )

        # --- добавляем колонку "Анализ ОИ" ---
        analysis_col = self.table.columnCount()
        self.table.insertColumn(analysis_col)
        self.table.setHorizontalHeaderItem(
            analysis_col,
            QTableWidgetItem("Анализ ОИ")
        )

        bold_font = QFont()
        bold_font.setBold(True)

        # --- заполняем таблицу данными ---
        for row_idx, row_data in enumerate(rows):
            name = str(row_data[0]) # ⚠️ если name в 0-й колонке
            for col_idx, value in enumerate(row_data):
                self.table.setItem(
                    row_idx,
                    col_idx,
                    QTableWidgetItem(str(value))
                )

            try:
                private_long = float(row_data[1])
                private_shorts = float(row_data[2])
                legal_long = float(row_data[3])
                legal_shorts = float(row_data[4])

                max_fl = max(private_long, private_shorts)
                min_fl = min(private_long, private_shorts)
                coef_fl = round(max_fl / min_fl, 1) if min_fl != 0 else max_fl

                max_ul = max(legal_long, legal_shorts)
                min_ul = min(legal_long, legal_shorts)
                coef_ul = round(max_ul / min_ul, 1) if min_ul != 0 else max_ul

            except Exception:
                coef_fl = ""
                coef_ul = ""

            # --- Кооф ФЛ ---
            item_fl = QTableWidgetItem(str(coef_fl))
            if isinstance(coef_fl, (int, float)) and coef_fl > 2:
                item_fl.setBackground(QColor("#949075"))
                item_fl.setForeground(QColor("black"))
                item_fl.setFont(bold_font)
            self.table.setItem(row_idx, coef_fl_col, item_fl)           

            # --- Кооф ЮЛ ---
            item_ul = QTableWidgetItem(str(coef_ul))
            if isinstance(coef_ul, (int, float)) and coef_ul > 3:
                item_ul.setBackground(QColor("#949075"))
                item_ul.setForeground(QColor("black"))
                item_ul.setFont(bold_font)
            self.table.setItem(row_idx, coef_ul_col, item_ul)

            # --- Направление (авто) ---
            direction_item = QTableWidgetItem()

            try:
                if legal_long > legal_shorts:
                    direction_item.setText("LONG")
                    direction_item.setBackground(QColor("#2e7d32"))
                    direction_item.setForeground(QColor("white"))
                else:
                    direction_item.setText("SHORT")
                    direction_item.setBackground(QColor("#c62828"))
                    direction_item.setForeground(QColor("black"))
            except Exception:
                direction_item.setText("")

            self.table.setItem(row_idx, signal_col, direction_item)

            # --- КНОПКА: Выбор ---
            is_selected = self.signals_state.get(name, False)
            btn_choice = QPushButton("Yes" if is_selected else "No")

            choice_container = QWidget()
            choice_layout = QHBoxLayout(choice_container)
            choice_layout.setContentsMargins(0, 0, 0, 0)
            choice_layout.addWidget(btn_choice)

            self.table.setCellWidget(row_idx, choice_col, choice_container)

            # ===============================
            # ВОССТАНОВЛЕНИЕ СОСТОЯНИЯ КНОПКИ
            # ===============================
            if self.signals_state.get(name, False):
                btn_choice.setText("Yes")
                btn_choice.setStyleSheet("background-color: #797a7a;")

                for col in range(0, 5):  # только первые 5 колонок
                    item = self.table.item(row_idx, col)
                    if item:
                        item.setBackground(QColor("#797a7a"))

            btn_choice.clicked.connect(
                lambda _, r=row_idx, n=name, b=btn_choice:
                self.toggle_choice(r, n, b)
            )

            # --- КНОПКА: Анализ ОИ ---
            btn_analysis = QPushButton("Анализ")

            analysis_container = QWidget()
            analysis_layout = QHBoxLayout(analysis_container)
            analysis_layout.setContentsMargins(0, 0, 0, 0)
            analysis_layout.addWidget(btn_analysis)

            self.table.setCellWidget(row_idx, analysis_col, analysis_container)

            # --- подключение кнопки к открытию плавающего окна ---
            btn_analysis.clicked.connect(
                lambda _, n=name: self.open_instrument_window(n)
            )



    