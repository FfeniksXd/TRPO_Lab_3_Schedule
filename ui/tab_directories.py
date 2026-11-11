from PySide6.QtWidgets import (QWidget, QHBoxLayout, QVBoxLayout, QGroupBox, 
                               QListWidget, QListWidgetItem, QPushButton, 
                               QLineEdit, QMessageBox, QInputDialog)
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon # Нужен для QListWidgetItem
import psycopg2

class DirectoriesTab(QWidget):
    def __init__(self, db):
        super().__init__()
        self.db = db
        self.setup_ui()
        self.load_all()

    def setup_ui(self):
        layout = QHBoxLayout(self)
        
        self.group_box = self.create_dir_block("Группы", "group")
        layout.addWidget(self.group_box['widget'])
        
        self.teacher_box = self.create_dir_block("Преподаватели", "teacher")
        layout.addWidget(self.teacher_box['widget'])
        
        self.subject_box = self.create_dir_block("Предметы", "subject")
        layout.addWidget(self.subject_box['widget'])
        
        self.room_box = self.create_dir_block("Аудитории", "classroom")
        layout.addWidget(self.room_box['widget'])

    def create_dir_block(self, title, item_type):
        group = QGroupBox(title)
        v_layout = QVBoxLayout(group)
        
        list_widget = QListWidget()
        v_layout.addWidget(list_widget)
        
        # Поле для добавления
        input_layout = QHBoxLayout()
        line_edit = QLineEdit()
        line_edit.setPlaceholderText("Новое значение...")
        btn_add = QPushButton("Добавить")
        input_layout.addWidget(line_edit)
        input_layout.addWidget(btn_add)
        v_layout.addLayout(input_layout)

        # Кнопки редактирования и удаления
        btn_layout = QHBoxLayout()
        btn_edit = QPushButton("Изменить")
        btn_delete = QPushButton("Удалить")
        btn_layout.addWidget(btn_edit)
        btn_layout.addWidget(btn_delete)
        v_layout.addLayout(btn_layout)
        
        # Обработка нажатий
        btn_add.clicked.connect(lambda: self.add_item(item_type, line_edit, list_widget))
        btn_edit.clicked.connect(lambda: self.edit_item(item_type, list_widget))
        btn_delete.clicked.connect(lambda: self.delete_item(item_type, list_widget))
        
        return {'widget': group, 'list': list_widget}

    def load_all(self):
        self.fill_list(self.group_box['list'], self.db.get_groups())
        self.fill_list(self.teacher_box['list'], self.db.get_teachers())
        self.fill_list(self.subject_box['list'], self.db.get_subjects())
        self.fill_list(self.room_box['list'], self.db.get_classrooms())

    def fill_list(self, list_widget, data):
        list_widget.clear()
        for item_id, name in data:
            item = QListWidgetItem(name)
            item.setData(Qt.UserRole, item_id) # Сохраняем ID в скрытом поле элемента
            list_widget.addItem(item)

    def add_item(self, item_type, line_edit, list_widget):
        text = line_edit.text().strip()
        if not text: return
        
        try:
            if item_type == "group": self.db.add_group(text)
            elif item_type == "teacher": self.db.add_teacher(text)
            elif item_type == "subject": self.db.add_subject(text)
            elif item_type == "classroom": self.db.add_classroom(text)
            
            line_edit.clear()
            self.load_all()
        except psycopg2.errors.UniqueViolation:
            QMessageBox.warning(self, "Ошибка", "Такое значение уже существует!")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка БД", str(e))

    def edit_item(self, item_type, list_widget):
        selected = list_widget.currentItem()
        if not selected:
            QMessageBox.information(self, "Внимание", "Выберите элемент для редактирования.")
            return

        item_id = selected.data(Qt.UserRole)
        old_text = selected.text()

        # Вызываем стандартное окно ввода текста
        new_text, ok = QInputDialog.getText(self, "Редактирование", 
                                            "Введите новое значение:", text=old_text)
        
        if ok and new_text.strip():
            new_text = new_text.strip()
            try:
                if item_type == "group": self.db.update_group(item_id, new_text)
                elif item_type == "teacher": self.db.update_teacher(item_id, new_text)
                elif item_type == "subject": self.db.update_subject(item_id, new_text)
                elif item_type == "classroom": self.db.update_classroom(item_id, new_text)
                
                self.load_all()
            except psycopg2.errors.UniqueViolation:
                QMessageBox.warning(self, "Ошибка", "Такое значение уже существует!")
            except Exception as e:
                QMessageBox.critical(self, "Ошибка БД", str(e))

    def delete_item(self, item_type, list_widget):
        selected = list_widget.currentItem()
        if not selected:
            QMessageBox.information(self, "Внимание", "Выберите элемент для удаления.")
            return

        item_id = selected.data(Qt.UserRole)
        text = selected.text()

        reply = QMessageBox.question(self, "Подтверждение", 
                                     f"Удалить '{text}'?\nВНИМАНИЕ: Если этот элемент используется в расписании, он удалится вместе со всеми занятиями!",
                                     QMessageBox.Yes | QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            try:
                if item_type == "group": self.db.delete_group(item_id)
                elif item_type == "teacher": self.db.delete_teacher(item_id)
                elif item_type == "subject": self.db.delete_subject(item_id)
                elif item_type == "classroom": self.db.delete_classroom(item_id)
                
                self.load_all()
            except Exception as e:
                QMessageBox.critical(self, "Ошибка БД", str(e))