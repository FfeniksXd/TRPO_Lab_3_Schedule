import psycopg2

class Database:
    def __init__(self):
        self.conn_params = {
            "dbname": "laboratory_3_schedule", 
            "user": "postgres",
            "password": "7ujm7UJM",          
            "host": "localhost",
            "port": "5432"
        }

    def execute_query(self, query, params=None):
        with psycopg2.connect(**self.conn_params) as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, params)
                return cursor.fetchall()

    def execute_dml(self, query, params=None):
        with psycopg2.connect(**self.conn_params) as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, params)

    # --- МЕТОДЫ ДЛЯ СПРАВОЧНИКОВ ---
    def get_groups(self):
        return self.execute_query("SELECT id, name FROM groups ORDER BY name")

    def get_teachers(self):
        return self.execute_query("SELECT id, full_name FROM teachers ORDER BY full_name")

    def get_subjects(self):
        return self.execute_query("SELECT id, name FROM subjects ORDER BY name")

    def get_classrooms(self):
        return self.execute_query("SELECT id, number FROM classrooms ORDER BY number")

    def get_class_types(self):
        return self.execute_query("SELECT id, name FROM class_types ORDER BY name")

    # --- МЕТОДЫ ДЛЯ РАСПИСАНИЯ ---
    def get_schedule(self):
        """Возвращает расписание с расшифровкой ID в названия через JOIN"""
        query = """
            SELECT 
                s.id, s.lesson_date, s.pair_number,
                g.name AS group_name, t.full_name AS teacher_name,
                sub.name AS subject_name, c.number AS classroom,
                ct.name AS class_type
            FROM schedule s
            JOIN groups g ON s.group_id = g.id
            JOIN teachers t ON s.teacher_id = t.id
            JOIN subjects sub ON s.subject_id = sub.id
            JOIN classrooms c ON s.classroom_id = c.id
            JOIN class_types ct ON s.class_type_id = ct.id
            ORDER BY s.lesson_date, s.pair_number
        """
        return self.execute_query(query)

    def add_schedule(self, data):
        """Добавляет занятие. Если есть конфликт (накладка), БД выбросит ошибку UniqueViolation"""
        query = """
            INSERT INTO schedule 
            (group_id, teacher_id, subject_id, classroom_id, class_type_id, lesson_date, pair_number)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        self.execute_dml(query, data)

    def delete_schedule(self, s_id):
        self.execute_dml("DELETE FROM schedule WHERE id = %s", (s_id,))

        # --- МЕТОДЫ ДЛЯ ДОБАВЛЕНИЯ СПРАВОЧНИКОВ ---
    def add_group(self, name):
        self.execute_dml("INSERT INTO groups (name) VALUES (%s)", (name,))
    
    def add_teacher(self, name):
        self.execute_dml("INSERT INTO teachers (full_name) VALUES (%s)", (name,))
        
    def add_subject(self, name):
        self.execute_dml("INSERT INTO subjects (name) VALUES (%s)", (name,))
        
    def add_classroom(self, number):
        self.execute_dml("INSERT INTO classrooms (number) VALUES (%s)", (number,))

        # --- МЕТОД ДЛЯ ОТЧЕТОВ ---
    def get_report_data(self, report_type):
        """Возвращает заголовки и данные для выбранного отчета"""
        
        # 1. Нагрузка преподавателей
        if report_type == "teacher_load":
            query = """
                SELECT t.full_name AS teacher, COUNT(s.id) AS lesson_count
                FROM teachers t
                LEFT JOIN schedule s ON t.id = s.teacher_id
                GROUP BY t.full_name
                ORDER BY lesson_count DESC, t.full_name
            """
            headers = ["Преподаватель", "Количество пар"]
            
        # 2. Занятость аудиторий
        elif report_type == "classroom_usage":
            query = """
                SELECT c.number AS classroom, COUNT(s.id) AS usage_count
                FROM classrooms c
                LEFT JOIN schedule s ON c.id = s.classroom_id
                GROUP BY c.number
                ORDER BY usage_count DESC, c.number
            """
            headers = ["Аудитория", "Количество занятий"]
            
        # 3. Распределение по видам занятий
        elif report_type == "class_types":
            query = """
                SELECT ct.name AS class_type, COUNT(s.id) AS count
                FROM class_types ct
                LEFT JOIN schedule s ON ct.id = s.class_type_id
                GROUP BY ct.name
                ORDER BY count DESC
            """
            headers = ["Вид занятия", "Количество"]
            
        # 4. Количество занятий по группам
        elif report_type == "group_load":
            query = """
                SELECT g.name AS group_name, COUNT(s.id) AS lesson_count
                FROM groups g
                LEFT JOIN schedule s ON g.id = s.group_id
                GROUP BY g.name
                ORDER BY lesson_count DESC, g.name
            """
            headers = ["Группа", "Количество занятий"]
            
        else:
            return [], []

        data = self.execute_query(query)
        return headers, data

        # --- МЕТОДЫ ДЛЯ РЕДАКТИРОВАНИЯ И УДАЛЕНИЯ СПРАВОЧНИКОВ ---
    def update_group(self, id, name):
        self.execute_dml("UPDATE groups SET name = %s WHERE id = %s", (name, id))
    def delete_group(self, id):
        self.execute_dml("DELETE FROM groups WHERE id = %s", (id,))

    def update_teacher(self, id, name):
        self.execute_dml("UPDATE teachers SET full_name = %s WHERE id = %s", (name, id))
    def delete_teacher(self, id):
        self.execute_dml("DELETE FROM teachers WHERE id = %s", (id,))

    def update_subject(self, id, name):
        self.execute_dml("UPDATE subjects SET name = %s WHERE id = %s", (name, id))
    def delete_subject(self, id):
        self.execute_dml("DELETE FROM subjects WHERE id = %s", (id,))

    def update_classroom(self, id, number):
        self.execute_dml("UPDATE classrooms SET number = %s WHERE id = %s", (number, id))
    def delete_classroom(self, id):
        self.execute_dml("DELETE FROM classrooms WHERE id = %s", (id,))



    # ==========================================
    # 
    # ==========================================

    def get_free_classrooms(self, date, pair):
        """Идея 1: Поиск свободных аудиторий на конкретную дату и пару.
        Использует подзапрос NOT IN."""
        query = """
            SELECT c.number
            FROM classrooms c
            WHERE c.id NOT IN (
                SELECT classroom_id 
                FROM schedule 
                WHERE lesson_date = %s AND pair_number = %s
            )
            ORDER BY c.number
        """
        return self.execute_query(query, (date, pair))

    def get_compact_schedule(self):
        """Идея 3: Компактное расписание на день в виде текстовой строки.
        Использует агрегатную функцию STRING_AGG (склеивание строк)."""
        query = """
            SELECT 
                g.name AS group_name,
                s.lesson_date,
                STRING_AGG(
                    s.pair_number || '. ' || sub.name || ' (' || c.number || ')', 
                    ' | ' ORDER BY s.pair_number
                ) AS daily_schedule
            FROM schedule s
            JOIN groups g ON s.group_id = g.id
            JOIN subjects sub ON s.subject_id = sub.id
            JOIN classrooms c ON s.classroom_id = c.id
            GROUP BY g.name, s.lesson_date
            ORDER BY s.lesson_date DESC, g.name
        """
        headers = ["Группа", "Дата", "Расписание на день"]
        return headers, self.execute_query(query)

    def get_daily_load(self):
        """Идея 4: Общая загруженность учебных дней.
        Использует CTE (Common Table Expressions) — конструкцию WITH."""
        query = """
            WITH DailyLoad AS (
                SELECT lesson_date, COUNT(id) as pairs_count
                FROM schedule
                GROUP BY lesson_date
            )
            SELECT lesson_date, pairs_count
            FROM DailyLoad
            ORDER BY lesson_date
        """
        headers = ["Дата", "Всего пар в вузе"]
        return headers, self.execute_query(query)

        # --- МЕТОДЫ ДЛЯ ФИЛЬТРАЦИИ И РЕДАКТИРОВАНИЯ РАСПИСАНИЯ ---
    def get_schedule_filtered(self, group_id=None, teacher_id=None, classroom_id=None):
        """Возвращает расписание с учетом выбранных фильтров"""
        query = """
            SELECT 
                s.id, s.lesson_date, s.pair_number,
                g.name AS group_name, t.full_name AS teacher_name,
                sub.name AS subject_name, c.number AS classroom,
                ct.name AS class_type,
                s.group_id, s.teacher_id, s.subject_id, s.classroom_id, s.class_type_id
            FROM schedule s
            JOIN groups g ON s.group_id = g.id
            JOIN teachers t ON s.teacher_id = t.id
            JOIN subjects sub ON s.subject_id = sub.id
            JOIN classrooms c ON s.classroom_id = c.id
            JOIN class_types ct ON s.class_type_id = ct.id
            WHERE 1=1
        """
        params = []
        
        # Динамически добавляем условия
        if group_id:
            query += " AND s.group_id = %s"
            params.append(group_id)
        if teacher_id:
            query += " AND s.teacher_id = %s"
            params.append(teacher_id)
        if classroom_id:
            query += " AND s.classroom_id = %s"
            params.append(classroom_id)

        query += " ORDER BY s.lesson_date, s.pair_number"
        return self.execute_query(query, tuple(params))

    def update_schedule(self, s_id, data):
        """Обновляет запись в расписании"""
        query = """
            UPDATE schedule SET 
            group_id=%s, teacher_id=%s, subject_id=%s, classroom_id=%s, 
            class_type_id=%s, lesson_date=%s, pair_number=%s
            WHERE id=%s
        """
        self.execute_dml(query, data + (s_id,))

    # --- ИДЕЯ 4: СВОБОДНЫЕ ПРЕПОДАВАТЕЛИ ---
    def get_free_teachers(self, date, pair):
        """Поиск преподавателей, у которых нет пары в указанное время"""
        query = """
            SELECT full_name
            FROM teachers
            WHERE id NOT IN (
                SELECT teacher_id 
                FROM schedule 
                WHERE lesson_date = %s AND pair_number = %s
            )
            ORDER BY full_name
        """
        return self.execute_query(query, (date, pair))