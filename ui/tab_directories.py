from PySide6.QtWidgets import (QWidget, QHBoxLayout, QVBoxLayout, QGroupBox, 
                               QListWidget, QListWidgetItem, QPushButton, 
                               QLineEdit, QMessageBox, QInputDialog,
                               QDialog, QFormLayout, QSpinBox, QComboBox,
                               QDialogButtonBox)
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon # Нужен для QListWidgetItem
import psycopg2


class ClassroomDialog(QDialog):
    """Окно добавления/редактирования аудитории: номер, вместимость, тип занятий"""
    def __init__(self, db, parent=None, number="", capacity=30, type_id=None):
        super().__init__(parent)
        self.setWindowTitle("Аудитория")
        self.setMinimumWidth(300)
        form = QFormLayout(self)

        self.number_edit = QLineEdit(number)

        self.capacity_spin = QSpinBox()
        self.capacity_spin.setRange(1, 1000)
        self.capacity_spin.setValue(capacity)
        self.capacity_spin.setSuffix(" мест")

        self.type_combo = QComboBox()
        for id, name in db.get_class_types():
            self.type_combo.addItem(name, id)
        if type_id is not None:
            self.type_combo.setCurrentIndex(self.type_combo.findData(type_id))

        form.addRow("Номер:", self.number_edit)
        form.addRow("Вместимость:", self.capacity_spin)
        form.addRow("Тип занятий:", self.type_combo)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        form.addRow(buttons)

    def get_data(self):
        return (self.number_edit.text().strip(),
                self.capacity_spin.value(),
                self.type_combo.currentData())


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
        # Для аудиторий ввод идёт через отдельное окно, поле ввода не нужно
        if item_type != "classroom":
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
        self.fill_rooms()

    def fill_list(self, list_widget, data):
        list_widget.clear()
        for item_id, name in data:
            item = QListWidgetItem(name)
            item.setData(Qt.UserRole, item_id) # Сохраняем ID в скрытом поле элемента
            list_widget.addItem(item)

    def fill_rooms(self):
        """Аудитории показываем с типом и вместимостью, полные данные храним в элементе"""
        list_widget = self.room_box['list']
        list_widget.clear()
        for rid, number, capacity, type_id, type_name in self.db.get_classrooms_full():
            item = QListWidgetItem(f"{number} — {type_name}, {capacity} мест")
            item.setData(Qt.UserRole, rid)
            item.setData(Qt.UserRole + 1, (number, capacity, type_id))
            list_widget.addItem(item)

    def add_item(self, item_type, line_edit, list_widget):
        if item_type == "classroom":
            dialog = ClassroomDialog(self.db, self)
            if dialog.exec() == QDialog.Accepted:
                data = dialog.get_data()
                if not data[0]:
                    return
                try:
                    self.db.add_classroom(*data)
                    self.load_all()
                except psycopg2.errors.UniqueViolation:
                    QMessageBox.warning(self, "Ошибка", "Такая аудитория уже существует!")
                except Exception as e:
                    QMessageBox.critical(self, "Ошибка БД", str(e))
            return

        text = line_edit.text().strip()
        if not text: return
        
        try:
            if item_type == "group": self.db.add_group(text)
            elif item_type == "teacher": self.db.add_teacher(text)
            elif item_type == "subject": self.db.add_subject(text)
            
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

        if item_type == "classroom":
            number, capacity, type_id = selected.data(Qt.UserRole + 1)
            dialog = ClassroomDialog(self.db, self, number, capacity, type_id)
            if dialog.exec() == QDialog.Accepted:
                data = dialog.get_data()
                if not data[0]:
                    return
                try:
                    self.db.update_classroom(item_id, *data)
                    self.load_all()
                except psycopg2.errors.UniqueViolation:
                    QMessageBox.warning(self, "Ошибка", "Такая аудитория уже существует!")
                except Exception as e:
                    QMessageBox.critical(self, "Ошибка БД", str(e))
            return

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
        if item_type == "classroom":
            text = selected.data(Qt.UserRole + 1)[0]  # только номер аудитории
        else:
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