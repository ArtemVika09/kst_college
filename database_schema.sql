-- Схема базы данных для бота КСТ
-- SQLite Database Schema

-- Таблица заказов справок
CREATE TABLE IF NOT EXISTS certificate_orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    fio TEXT NOT NULL,
    group_name TEXT NOT NULL,
    created_at TEXT NOT NULL
);

-- Таблица опросов
CREATE TABLE IF NOT EXISTS polls (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    type TEXT NOT NULL,
    title TEXT,
    question TEXT,
    options TEXT,
    link_or_file_id TEXT,
    created_at TEXT NOT NULL,
    target_audience TEXT,
    target_groups TEXT
);

-- Таблица групп студентов (для уведомлений)
CREATE TABLE IF NOT EXISTS user_groups (
    user_id INTEGER PRIMARY KEY,
    group_name TEXT NOT NULL
);

-- Старая таблица педагогов (для совместимости)
CREATE TABLE IF NOT EXISTS pedagog_users (
    user_id INTEGER PRIMARY KEY
);

-- Таблица аутентификации педагогов
CREATE TABLE IF NOT EXISTS pedagog_auth (
    user_id INTEGER PRIMARY KEY,
    fio TEXT NOT NULL,
    password_hash TEXT NOT NULL
);

-- Таблица аутентификации студентов
CREATE TABLE IF NOT EXISTS student_auth (
    user_id INTEGER PRIMARY KEY,
    fio TEXT NOT NULL,
    group_name TEXT NOT NULL,
    password_hash TEXT NOT NULL
);

-- Индексы для оптимизации запросов
CREATE INDEX IF NOT EXISTS idx_pedagog_auth_fio ON pedagog_auth(fio);
CREATE INDEX IF NOT EXISTS idx_student_auth_fio ON student_auth(fio);
CREATE INDEX IF NOT EXISTS idx_certificate_orders_user_id ON certificate_orders(user_id);
CREATE INDEX IF NOT EXISTS idx_polls_user_id ON polls(user_id);
CREATE INDEX IF NOT EXISTS idx_polls_target_audience ON polls(target_audience);

