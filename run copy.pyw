from PyQt6.QtWidgets import QApplication
from app.main import run_app
import sys

run_app()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    sys.exit(app.exec())