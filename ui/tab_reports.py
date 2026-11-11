from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QComboBox, 
                               QPushButton, QTableWidget, QTableWidgetItem, 
                               QHeaderView, QLabel, QDateEdit, QSpinBox, QGroupBox)
from PySide6.QtCore import Qt, QDate

class ReportsTab(QWidget):
    def __init__(self, db):
        super().__init__()
        self.db = db
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # --- БЛОК 1: Аналитические отчеты ---
        group_report = QGroupBox("Аналитические отчеты")
        report_layout = QHBoxLayout(group_report)
        
        self.report_combo = QComboBox()
        # Базовые отчеты
        self.report_combo.addItem("Нагрузка преподавателей (простая)", "teacher_load")
        self.report_combo.addItem("Занятость аудиторий", "classroom_usage")
        self.report_combo.addItem("Распределение по видам занятий", "class_types")
        # Продвинутые отчеты
        self.report_combo.addItem("Общая загруженность дней (CTE / WITH)", "daily_load")
        self.report_combo.addItem("Компактное расписание групп (STRING_AGG)", "compact_schedule")
        
        report_layout.addWidget(self.report_combo)
        
        self.btn_generate = QPushButton("Сформировать")
        report_layout.addWidget(self.btn_generate)
        report_layout.addStretch()
        layout.addWidget(group_report)

        # --- БЛОК 2: Поиск свободных ресурсов ---
        group_free = QGroupBox("Поиск свободных ресурсов на время")
        free_layout = QHBoxLayout(group_free)
        
        self.date_edit = QDateEdit()
        self.date_edit.setDisplayFormat("dd.MM.yyyy")
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDate(QDate.currentDate())
        
        self.pair_spin = QSpinBox()
        self.pair_spin.setRange(1, 8)
        self.pair_spin.setSuffix(" пара")
        
        self.btn_find_free_rooms = QPushButton("Свободные аудитории")
        self.btn_find_free_teachers = QPushButton("Свободные преподаватели")
        
        free_layout.addWidget(QLabel("Дата:"))
        free_layout.addWidget(self.date_edit)
        free_layout.addWidget(QLabel("Пара:"))
        free_layout.addWidget(self.pair_spin)
        free_layout.addWidget(self.btn_find_free_rooms)
        free_layout.addWidget(self.btn_find_free_teachers)
        free_layout.addStretch()
        layout.addWidget(group_free)

        # --- БЛОК 3: Таблица для вывода ---
        self.table = QTableWidget()
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.table)

        # Подключаем кнопки к функциям
        self.btn_generate.clicked.connect(self.generate_report)
        self.btn_find_free_rooms.clicked.connect(self.find_free_classrooms)
        self.btn_find_free_teachers.clicked.connect(self.find_free_teachers)

    def generate_report(self):
        report_type = self.report_combo.currentData()
        
        # Вызов нужного метода из БД
        if report_type == "compact_schedule":
            headers, data = self.db.get_compact_schedule()
        elif report_type == "daily_load":
            headers, data = self.db.get_daily_load()
        else:
            # Старые простые отчеты (нагрузка преподавателей, аудиторий и т.д.)
            headers, data = self.db.get_report_data(report_type)
        
        self.update_table(headers, data)

    def find_free_classrooms(self):
        date = self.date_edit.date().toPython()
        pair = self.pair_spin.value()
        
        data = self.db.get_free_classrooms(date, pair)
        
        # Формируем таблицу из одного столбца
        headers = ["Свободные аудитории"]
        # Превращаем список кортежей [('301',), ('402',)] в [('Аудитория 301',), ('Аудитория 402',)]
        formatted_data = [(f"Аудитория {row[0]}",) for row in data]
        
        self.update_table(headers, formatted_data)

    def find_free_teachers(self):
        date = self.date_edit.date().toPython()
        pair = self.pair_spin.value()
        
        data = self.db.get_free_teachers(date, pair)
        
        # Формируем таблицу из одного столбца
        headers = ["Свободные преподаватели"]
        formatted_data = [(f"{row[0]}",) for row in data]
        
        self.update_table(headers, formatted_data)

    def update_table(self, headers, data):
        """Универсальный метод для заполнения таблицы"""
        self.table.setColumnCount(len(headers))
        self.table.setHorizontalHeaderLabels(headers)
        self.table.setRowCount(len(data))
        
        for row_idx, row_data in enumerate(data):
            for col_idx, cell_data in enumerate(row_data):
                # Если это объект даты (datetime.date), форматируем его в строку
                if hasattr(cell_data, 'strftime'):
                    text = cell_data.strftime("%d.%m.%Y")
                else:
                    text = str(cell_data)
                    
                item = QTableWidgetItem(text)
                
                # Выравниваем числа по центру для красоты
                if isinstance(cell_data, int):
                    item.setTextAlignment(Qt.AlignCenter)
                    
                self.table.setItem(row_idx, col_idx, item)