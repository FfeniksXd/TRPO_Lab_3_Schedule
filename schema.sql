-- Создание базы данных (выполнить отдельно, если её нет)
-- CREATE DATABASE laboratory_3_schedule;

CREATE TABLE groups (id SERIAL PRIMARY KEY, name VARCHAR(50) NOT NULL UNIQUE);
CREATE TABLE teachers (id SERIAL PRIMARY KEY, full_name VARCHAR(200) NOT NULL UNIQUE);
CREATE TABLE subjects (id SERIAL PRIMARY KEY, name VARCHAR(150) NOT NULL UNIQUE);
CREATE TABLE classrooms (id SERIAL PRIMARY KEY, number VARCHAR(20) NOT NULL UNIQUE);
CREATE TABLE class_types (id SERIAL PRIMARY KEY, name VARCHAR(50) NOT NULL UNIQUE);

CREATE TABLE schedule (
    id            SERIAL PRIMARY KEY,
    group_id      INT NOT NULL REFERENCES groups(id) ON DELETE CASCADE,
    teacher_id    INT NOT NULL REFERENCES teachers(id) ON DELETE CASCADE,
    subject_id    INT NOT NULL REFERENCES subjects(id) ON DELETE CASCADE,
    classroom_id  INT NOT NULL REFERENCES classrooms(id) ON DELETE CASCADE,
    class_type_id INT NOT NULL REFERENCES class_types(id) ON DELETE CASCADE,
    lesson_date   DATE NOT NULL,
    pair_number   SMALLINT NOT NULL CHECK (pair_number BETWEEN 1 AND 8),

    -- ОГРАНИЧЕНИЯ ИЗ ЗАДАНИЯ:
    CONSTRAINT unique_teacher_time UNIQUE (lesson_date, pair_number, teacher_id),
    CONSTRAINT unique_classroom_time UNIQUE (lesson_date, pair_number, classroom_id),
    CONSTRAINT unique_group_time UNIQUE (lesson_date, pair_number, group_id)
);

-- Базовые данные
INSERT INTO class_types (name) VALUES ('Лекция'), ('Практика'), ('Лабораторная');
INSERT INTO groups (name) VALUES ('ИУ7-11Б'), ('ИУ7-12Б'), ('МЗО-319БВ-24');
INSERT INTO teachers (full_name) VALUES ('Иванов И.И.'), ('Петров П.П.'), ('Сидорова А.А.');
INSERT INTO subjects (name) VALUES ('Базы данных'), ('Программирование'), ('Высшая математика');
INSERT INTO classrooms (number) VALUES ('301'), ('402'), ('Актовый зал');