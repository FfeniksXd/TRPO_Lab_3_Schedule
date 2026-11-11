import sys
from PySide6.QtWidgets import QApplication, QMainWindow, QTabWidget, QMessageBox
from db import Database
from ui.tab_schedule import ScheduleTab
from ui.tab_directories import DirectoriesTab
from ui.tab_reports import ReportsTab 

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Поддержка составления расписания учебных занятий")
        self.resize(1000, 700)

        try:
            self.db = Database()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось подключиться к БД:\n{e}")
            sys.exit(1)

        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)

        # Добавляем вкладки
        self.tabs.addTab(ScheduleTab(self.db), "Расписание")
        self.tabs.addTab(DirectoriesTab(self.db), "Справочники")
        self.tabs.addTab(ReportsTab(self.db), "Отчеты")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())