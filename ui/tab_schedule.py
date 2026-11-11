from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, 
                               QTableWidgetItem, QHeaderView, QPushButton, 
                               QDialog, QFormLayout, QMessageBox, QComboBox, 
                               QDateEdit, QSpinBox, QLabel)
from PySide6.QtCore import Qt, QDate
import psycopg2

class ScheduleDialog(QDialog):
    def __init__(self, db, parent=None, data=None):
        super().__init__(parent)
        self.db = db
        self.setWindowTitle("Редактирование занятия" if data else "Добавление занятия")
        self.setMinimumWidth(350)

        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.date_edit = QDateEdit()
        self.date_edit.setDisplayFormat("dd.MM.yyyy")
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDate(QDate.currentDate())

        self.pair_spin = QSpinBox()
        self.pair_spin.setRange(1, 8)
        self.pair_spin.setSuffix(" пара")

        self.group_combo = QComboBox()
        self.teacher_combo = QComboBox()
        self.subject_combo = QComboBox()
        self.classroom_combo = QComboBox()
        self.type_combo = QComboBox()

        for id, name in self.db.get_groups(): self.group_combo.addItem(name, id)
        for id, name in self.db.get_teachers(): self.teacher_combo.addItem(name, id)
        for id, name in self.db.get_subjects(): self.subject_combo.addItem(name, id)
        for id, name in self.db.get_classrooms(): self.classroom_combo.addItem(name, id)
        for id, name in self.db.get_class_types(): self.type_combo.addItem(name, id)

        form.addRow("Дата:", self.date_edit)
        form.addRow("Пара:", self.pair_spin)
        form.addRow("Группа:", self.group_combo)
        form.addRow("Предмет:", self.subject_combo)
        form.addRow("Преподаватель:", self.teacher_combo)
        form.addRow("Аудитория:", self.classroom_combo)
        form.addRow("Вид занятия:", self.type_combo)
        layout.addLayout(form)

        # Если передали данные (редактирование), заполняем поля
        if data:
            # data = (id, date, pair, group_name, teacher_name, sub_name, room, type_name, group_id, teacher_id, sub_id, room_id, type_id)
            self.date_edit.setDate(data[1])
            self.pair_spin.setValue(data[2])
            self.group_combo.setCurrentIndex(self.group_combo.findData(data[8]))
            self.teacher_combo.setCurrentIndex(self.teacher_combo.findData(data[9]))
            self.subject_combo.setCurrentIndex(self.subject_combo.findData(data[10]))
            self.classroom_combo.setCurrentIndex(self.classroom_combo.findData(data[11]))
            self.type_combo.setCurrentIndex(self.type_combo.findData(data[12]))

        btn_layout = QHBoxLayout()
        self.save_btn = QPushButton("Сохранить")
        self.cancel_btn = QPushButton("Отмена")
        btn_layout.addWidget(self.save_btn)
        btn_layout.addWidget(self.cancel_btn)
        layout.addLayout(btn_layout)

        self.save_btn.clicked.connect(self.accept)
        self.cancel_btn.clicked.connect(self.reject)

    def get_data(self):
        return (
            self.group_combo.currentData(), self.teacher_combo.currentData(),
            self.subject_combo.currentData(), self.classroom_combo.currentData(),
            self.type_combo.currentData(), self.date_edit.date().toPython(),
            self.pair_spin.value()
        )

class ScheduleTab(QWidget):
    def __init__(self, db):
        super().__init__()
        self.db = db
        self.setup_ui()
        self.load_data()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # --- Панель фильтров ---
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("Фильтры:"))
        
        self.filter_group = QComboBox()
        self.filter_group.addItem("Все группы", None)
        for id, name in self.db.get_groups(): self.filter_group.addItem(name, id)
        
        self.filter_teacher = QComboBox()
        self.filter_teacher.addItem("Все преподаватели", None)
        for id, name in self.db.get_teachers(): self.filter_teacher.addItem(name, id)

        self.filter_room = QComboBox()
        self.filter_room.addItem("Все аудитории", None)
        for id, name in self.db.get_classrooms(): self.filter_room.addItem(name, id)
        
        self.btn_apply_filter = QPushButton("Применить")
        
        filter_layout.addWidget(self.filter_group)
        filter_layout.addWidget(self.filter_teacher)
        filter_layout.addWidget(self.filter_room)
        filter_layout.addWidget(self.btn_apply_filter)
        filter_layout.addStretch()
        layout.addLayout(filter_layout)

        # --- Панель кнопок ---
        btn_layout = QHBoxLayout()
        self.btn_add = QPushButton("Добавить занятие")
        self.btn_delete = QPushButton("Удалить занятие")
        self.btn_reset = QPushButton("Сбросить фильтры")
        
        btn_layout.addWidget(self.btn_add)
        btn_layout.addWidget(self.btn_delete)
        btn_layout.addWidget(self.btn_reset)
        layout.addLayout(btn_layout)

        # --- Таблица ---
        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels(["ID", "Дата", "Пара", "Группа", "Предмет", "Преподаватель", "Аудитория", "Тип"])
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(5, QHeaderView.Stretch)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSortingEnabled(True) # Включаем сортировку по клику на заголовок
        self.table.hideColumn(0)
        layout.addWidget(self.table)

        # Подключение сигналов
        self.btn_add.clicked.connect(self.add_record)
        self.btn_delete.clicked.connect(self.delete_record)
        self.btn_apply_filter.clicked.connect(self.load_data)
        self.btn_reset.clicked.connect(self.reset_filters)
        self.table.cellDoubleClicked.connect(self.edit_record) # Двойной клик для редактирования

    def load_data(self):
        # Получаем ID из фильтров (если выбрано "Все...", там будет None)
        g_id = self.filter_group.currentData()
        t_id = self.filter_teacher.currentData()
        r_id = self.filter_room.currentData()

        data = self.db.get_schedule_filtered(g_id, t_id, r_id)
        
        self.table.setSortingEnabled(False) # Отключаем сортировку на время заполнения
        self.table.setRowCount(len(data))
        for row_idx, row_data in enumerate(data):
            self.table.setItem(row_idx, 0, QTableWidgetItem(str(row_data[0])))
            self.table.setItem(row_idx, 1, QTableWidgetItem(row_data[1].strftime("%d.%m.%Y")))
            self.table.setItem(row_idx, 2, QTableWidgetItem(str(row_data[2])))
            self.table.setItem(row_idx, 3, QTableWidgetItem(row_data[3]))
            self.table.setItem(row_idx, 4, QTableWidgetItem(row_data[5])) # Предмет
            self.table.setItem(row_idx, 5, QTableWidgetItem(row_data[4])) # Преподаватель
            self.table.setItem(row_idx, 6, QTableWidgetItem(row_data[6]))
            self.table.setItem(row_idx, 7, QTableWidgetItem(row_data[7]))
        self.table.setSortingEnabled(True)

    def reset_filters(self):
        self.filter_group.setCurrentIndex(0)
        self.filter_teacher.setCurrentIndex(0)
        self.filter_room.setCurrentIndex(0)
        self.load_data()

    def add_record(self):
        dialog = ScheduleDialog(self.db, self)
        if dialog.exec() == QDialog.Accepted:
            self.save_to_db(dialog.get_data(), is_new=True)

    def edit_record(self, row, col):
        # Получаем ID записи из скрытой колонки
        s_id = int(self.table.item(row, 0).text())
        
        # Нам нужны полные данные для окна (включая ID для комбобоксов)
        # Делаем быстрый запрос по ID
        data = self.db.execute_query("""
            SELECT s.id, s.lesson_date, s.pair_number, NULL, NULL, NULL, NULL, NULL,
                   s.group_id, s.teacher_id, s.subject_id, s.classroom_id, s.class_type_id
            FROM schedule s WHERE s.id = %s
        """, (s_id,))[0]

        dialog = ScheduleDialog(self.db, self, data=data)
        if dialog.exec() == QDialog.Accepted:
            new_data = dialog.get_data()
            try:
                self.db.update_schedule(s_id, new_data)
                self.load_data()
            except psycopg2.errors.UniqueViolation as e:
                self.show_conflict_error(e)

    def delete_record(self):
        selected_row = self.table.currentRow()
        if selected_row == -1:
            QMessageBox.information(self, "Внимание", "Выберите занятие для удаления.")
            return
        s_id = int(self.table.item(selected_row, 0).text())
        
        reply = QMessageBox.question(self, "Подтверждение", "Удалить выбранное занятие?", QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.db.delete_schedule(s_id)
            self.load_data()

    def save_to_db(self, data, is_new=True):
        try:
            self.db.add_schedule(data)
            self.load_data()
        except psycopg2.errors.UniqueViolation as e:
            self.show_conflict_error(e)

    def show_conflict_error(self, e):
        error_msg = str(e)
        if 'unique_teacher_time' in error_msg:
            QMessageBox.critical(self, "Конфликт расписания", "Этот преподаватель уже ведет пару в это время!")
        elif 'unique_classroom_time' in error_msg:
            QMessageBox.critical(self, "Конфликт расписания", "Эта аудитория уже занята в это время!")
        elif 'unique_group_time' in error_msg:
            QMessageBox.critical(self, "Конфликт расписания", "У этой группы уже есть занятие в это время!")
        else:
            QMessageBox.critical(self, "Ошибка", "Нарушено ограничение уникальности.")

    def showEvent(self, event):
        super().showEvent(event)
        self.load_data()