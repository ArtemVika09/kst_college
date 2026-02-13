"""
Модуль для работы с базой данных бота КСТ
"""
import sqlite3
import hashlib
from pathlib import Path
from typing import Optional, Tuple, Dict, List

# Путь к файлу базы данных
BOT_DIR = Path(__file__).resolve().parent
DB_FILE = BOT_DIR / "kst_bot.db"


def hash_password(password: str) -> str:
    """Хеширует пароль с помощью SHA256."""
    return hashlib.sha256(password.encode('utf-8')).hexdigest()


def init_db(config_dir: Path = None):
    """Создание всех таблиц базы данных."""
    if config_dir:
        config_dir.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    
    # Заказы справок
    cur.execute("""
        CREATE TABLE IF NOT EXISTS certificate_orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            fio TEXT NOT NULL,
            group_name TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    """)
    
    # Опросы
    cur.execute("""
        CREATE TABLE IF NOT EXISTS polls (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            type TEXT NOT NULL,
            title TEXT,
            question TEXT,
            options TEXT,
            link_or_file_id TEXT,
            created_at TEXT NOT NULL
        )
    """)
    
    # Группы студентов
    cur.execute("""
        CREATE TABLE IF NOT EXISTS user_groups (
            user_id INTEGER PRIMARY KEY,
            group_name TEXT NOT NULL
        )
    """)
    
    # Добавляем колонки для опросов, если их нет
    try:
        cur.execute("ALTER TABLE polls ADD COLUMN target_audience TEXT")
    except sqlite3.OperationalError:
        pass
    try:
        cur.execute("ALTER TABLE polls ADD COLUMN target_groups TEXT")
    except sqlite3.OperationalError:
        pass
    
    # Старая таблица педагогов (для совместимости)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS pedagog_users (
            user_id INTEGER PRIMARY KEY
        )
    """)
    
    # Таблица аутентификации педагогов
    cur.execute("""
        CREATE TABLE IF NOT EXISTS pedagog_auth (
            user_id INTEGER PRIMARY KEY,
            fio TEXT NOT NULL,
            password_hash TEXT NOT NULL
        )
    """)
    
    # Таблица аутентификации студентов
    cur.execute("""
        CREATE TABLE IF NOT EXISTS student_auth (
            user_id INTEGER PRIMARY KEY,
            fio TEXT NOT NULL,
            group_name TEXT NOT NULL,
            password_hash TEXT NOT NULL
        )
    """)
    
    # Расписание обедов по группам: дата, время начала и конца
    cur.execute("""
        CREATE TABLE IF NOT EXISTS lunch_schedule (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            group_name TEXT NOT NULL,
            schedule_date TEXT NOT NULL,
            start_time TEXT NOT NULL,
            end_time TEXT NOT NULL,
            note TEXT
        )
    """)
    
    # Создаем индексы для оптимизации
    try:
        cur.execute("CREATE INDEX IF NOT EXISTS idx_pedagog_auth_fio ON pedagog_auth(fio)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_student_auth_fio ON student_auth(fio)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_certificate_orders_user_id ON certificate_orders(user_id)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_polls_user_id ON polls(user_id)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_polls_target_audience ON polls(target_audience)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_lunch_schedule_group ON lunch_schedule(group_name)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_lunch_schedule_date ON lunch_schedule(schedule_date)")
    except sqlite3.OperationalError:
        pass
    
    # Записи на дни открытых дверей (мероприятия)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS open_doors_registrations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            event_index INTEGER NOT NULL,
            fio TEXT NOT NULL,
            contact TEXT,
            created_at TEXT NOT NULL
        )
    """)
    try:
        cur.execute("CREATE INDEX IF NOT EXISTS idx_open_doors_reg_user ON open_doors_registrations(user_id)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_open_doors_reg_event ON open_doors_registrations(event_index)")
    except sqlite3.OperationalError:
        pass
    
    # Пример расписания обедов для одной группы (если таблица пуста)
    cur.execute("SELECT COUNT(*) FROM lunch_schedule")
    if cur.fetchone()[0] == 0:
        from datetime import datetime, timedelta
        for i in range(5):
            d = (datetime.now() + timedelta(days=i)).strftime("%Y-%m-%d")
            cur.execute(
                "INSERT INTO lunch_schedule (group_name, schedule_date, start_time, end_time, note) VALUES (?, ?, ?, ?, ?)",
                ("СИП-113/25", d, "12:00", "12:30", "")
            )
    
    conn.commit()
    conn.close()


# ========== ФУНКЦИИ ДЛЯ ПЕДАГОГОВ ==========

def is_pedagog_registered(user_id: int) -> bool:
    """Проверяет, зарегистрирован ли пользователь как педагог."""
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM pedagog_auth WHERE user_id = ?", (user_id,))
    row = cur.fetchone()
    conn.close()
    return row is not None


def register_pedagog(user_id: int, fio: str, password: str):
    """Регистрирует педагога с ФИО и паролем."""
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    password_hash = hash_password(password)
    cur.execute("INSERT OR REPLACE INTO pedagog_auth (user_id, fio, password_hash) VALUES (?, ?, ?)", 
                (user_id, fio, password_hash))
    # Также добавляем в старую таблицу для совместимости
    cur.execute("INSERT OR IGNORE INTO pedagog_users (user_id) VALUES (?)", (user_id,))
    conn.commit()
    conn.close()


def login_pedagog(fio: str, password: str) -> Tuple[bool, int]:
    """Проверяет ФИО и пароль педагога. Возвращает (успех, user_id) или (False, 0)."""
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    password_hash = hash_password(password)
    cur.execute("SELECT user_id FROM pedagog_auth WHERE fio = ? AND password_hash = ?", (fio, password_hash))
    row = cur.fetchone()
    conn.close()
    if row:
        return (True, row[0])
    return (False, 0)


def login_pedagog_by_user_id(user_id: int, password: str) -> bool:
    """Проверяет пароль педагога по user_id (для входа уже зарегистрированного пользователя)."""
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    password_hash = hash_password(password)
    cur.execute("SELECT 1 FROM pedagog_auth WHERE user_id = ? AND password_hash = ?", (user_id, password_hash))
    row = cur.fetchone()
    conn.close()
    return row is not None


def get_pedagog_fio(user_id: int) -> str:
    """Возвращает ФИО педагога."""
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("SELECT fio FROM pedagog_auth WHERE user_id = ?", (user_id,))
    row = cur.fetchone()
    conn.close()
    return row[0] if row else ""


# ========== ФУНКЦИИ ДЛЯ СТУДЕНТОВ ==========

def is_student_registered(user_id: int) -> bool:
    """Проверяет, зарегистрирован ли пользователь как студент."""
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM student_auth WHERE user_id = ?", (user_id,))
    row = cur.fetchone()
    conn.close()
    return row is not None


def register_student(user_id: int, fio: str, group_name: str, password: str):
    """Регистрирует студента с ФИО, группой и паролем."""
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    password_hash = hash_password(password)
    cur.execute("INSERT OR REPLACE INTO student_auth (user_id, fio, group_name, password_hash) VALUES (?, ?, ?, ?)", 
                (user_id, fio, group_name, password_hash))
    # Также обновляем user_groups для совместимости
    cur.execute("INSERT OR REPLACE INTO user_groups (user_id, group_name) VALUES (?, ?)", (user_id, group_name))
    conn.commit()
    conn.close()


def login_student(fio: str, password: str) -> Tuple[bool, int]:
    """Проверяет ФИО и пароль студента. Возвращает (успех, user_id) или (False, 0)."""
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    password_hash = hash_password(password)
    cur.execute("SELECT user_id FROM student_auth WHERE fio = ? AND password_hash = ?", (fio, password_hash))
    row = cur.fetchone()
    conn.close()
    if row:
        return (True, row[0])
    return (False, 0)


def login_student_by_user_id(user_id: int, password: str) -> bool:
    """Проверяет пароль студента по user_id (для входа уже зарегистрированного пользователя)."""
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    password_hash = hash_password(password)
    cur.execute("SELECT 1 FROM student_auth WHERE user_id = ? AND password_hash = ?", (user_id, password_hash))
    row = cur.fetchone()
    conn.close()
    return row is not None


def get_student_info(user_id: int) -> Optional[Dict[str, str]]:
    """Возвращает информацию о студенте (ФИО, группа) или None."""
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("SELECT fio, group_name FROM student_auth WHERE user_id = ?", (user_id,))
    row = cur.fetchone()
    conn.close()
    if row:
        return {"fio": row[0], "group": row[1]}
    return None


def get_student_group(user_id: int) -> Optional[str]:
    """Возвращает группу пользователя из user_groups или None."""
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("SELECT group_name FROM user_groups WHERE user_id = ?", (user_id,))
    row = cur.fetchone()
    conn.close()
    return row[0] if row else None


def set_student_group(user_id: int, group_name: str):
    """Сохраняет группу пользователя (для раздела Опросы у студентов)."""
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("INSERT OR REPLACE INTO user_groups (user_id, group_name) VALUES (?, ?)", (user_id, group_name))
    conn.commit()
    conn.close()


# ========== ФУНКЦИИ ДЛЯ ОПРОСОВ ==========

def get_polls_list_pedagog() -> List[Tuple]:
    """Список всех опросов для раздела ПЕДАГОГАМ → Опросы."""
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("""SELECT id, type, title, question, created_at,
                   COALESCE(target_audience, '') as target_audience,
                   COALESCE(target_groups, '') as target_groups
                   FROM polls ORDER BY created_at DESC LIMIT 50""")
    rows = cur.fetchall()
    conn.close()
    return rows


def get_polls_list_student(user_group: Optional[str]) -> List[Tuple]:
    """Список опросов для студента (target_audience=student, группа в target_groups или не указана)."""
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("""SELECT id, type, title, question, options, link_or_file_id,
                   COALESCE(target_groups, '') as target_groups, created_at
                   FROM polls WHERE COALESCE(target_audience, '') = 'student' ORDER BY created_at DESC""")
    rows = cur.fetchall()
    conn.close()
    result = []
    for r in rows:
        tg = (r[6] or "").strip()
        groups_list = [g.strip() for g in tg.split(",") if g.strip()]
        if not groups_list or (user_group and user_group in groups_list):
            result.append(r)
    return result


def get_student_user_ids_to_notify(target_groups: Optional[str]) -> List[int]:
    """user_id студентов для уведомления о новом опросе (по target_groups)."""
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    if target_groups and target_groups.strip():
        groups = [g.strip() for g in target_groups.split(",") if g.strip()]
        placeholders = ",".join("?" * len(groups))
        cur.execute(f"SELECT user_id FROM user_groups WHERE group_name IN ({placeholders})", groups)
    else:
        cur.execute("SELECT user_id FROM user_groups")
    rows = cur.fetchall()
    conn.close()
    return [row[0] for row in rows]


def save_poll(user_id: int, poll_type: str, title: Optional[str], question: Optional[str], 
              options: Optional[str], link_or_file_id: Optional[str], 
              target_audience: Optional[str] = None, target_groups: Optional[str] = None):
    """Сохраняет опрос в базу данных."""
    from datetime import datetime
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute(
        """INSERT INTO polls (user_id, type, title, question, options, link_or_file_id, 
           created_at, target_audience, target_groups)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (user_id, poll_type, title, question, options, link_or_file_id, 
         datetime.now().isoformat(), target_audience, target_groups)
    )
    conn.commit()
    conn.close()


# ========== ФУНКЦИИ ДЛЯ ЗАКАЗОВ СПРАВОК ==========

def save_certificate_order(user_id: int, fio: str, group_name: str):
    """Сохраняет заказ справки в базу данных."""
    from datetime import datetime
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO certificate_orders (user_id, fio, group_name, created_at) VALUES (?, ?, ?, ?)",
        (user_id, fio, group_name, datetime.now().isoformat())
    )
    conn.commit()
    conn.close()


# ========== ЗАПИСЬ НА ДНИ ОТКРЫТЫХ ДВЕРЕЙ ==========

def is_registered_open_doors(user_id: int, event_index: int) -> bool:
    """Проверяет, записан ли пользователь на мероприятие (event_index — индекс в OPEN_DOORS_CARDS)."""
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute(
        "SELECT 1 FROM open_doors_registrations WHERE user_id = ? AND event_index = ?",
        (user_id, event_index)
    )
    row = cur.fetchone()
    conn.close()
    return row is not None


def save_open_doors_registration(user_id: int, event_index: int, fio: str, contact: str = "") -> None:
    """Сохраняет запись на мероприятие (день открытых дверей)."""
    from datetime import datetime
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute(
        """INSERT INTO open_doors_registrations (user_id, event_index, fio, contact, created_at)
           VALUES (?, ?, ?, ?, ?)""",
        (user_id, event_index, fio, (contact or "").strip(), datetime.now().isoformat())
    )
    conn.commit()
    conn.close()


# ========== РАСПИСАНИЕ ОБЕДОВ ==========

def get_lunch_schedule(
    group_name: str,
    from_date: Optional[str] = None,
    to_date: Optional[str] = None
) -> List[Tuple]:
    """
    Возвращает расписание обедов для группы.
    Каждая запись: (id, group_name, schedule_date, start_time, end_time, note).
    from_date, to_date — в формате YYYY-MM-DD; если не заданы — все записи группы.
    """
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    if from_date and to_date:
        cur.execute(
            """SELECT id, group_name, schedule_date, start_time, end_time, COALESCE(note, '')
               FROM lunch_schedule
               WHERE group_name = ? AND schedule_date >= ? AND schedule_date <= ?
               ORDER BY schedule_date, start_time""",
            (group_name, from_date, to_date)
        )
    elif from_date:
        cur.execute(
            """SELECT id, group_name, schedule_date, start_time, end_time, COALESCE(note, '')
               FROM lunch_schedule
               WHERE group_name = ? AND schedule_date >= ?
               ORDER BY schedule_date, start_time""",
            (group_name, from_date)
        )
    elif to_date:
        cur.execute(
            """SELECT id, group_name, schedule_date, start_time, end_time, COALESCE(note, '')
               FROM lunch_schedule
               WHERE group_name = ? AND schedule_date <= ?
               ORDER BY schedule_date, start_time""",
            (group_name, to_date)
        )
    else:
        cur.execute(
            """SELECT id, group_name, schedule_date, start_time, end_time, COALESCE(note, '')
               FROM lunch_schedule
               WHERE group_name = ?
               ORDER BY schedule_date, start_time""",
            (group_name,)
        )
    rows = cur.fetchall()
    conn.close()
    return rows


def save_lunch_slot(
    group_name: str,
    schedule_date: str,
    start_time: str,
    end_time: str,
    note: Optional[str] = None
) -> int:
    """Добавляет слот расписания обедов. schedule_date в формате YYYY-MM-DD. Возвращает id записи."""
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute(
        """INSERT INTO lunch_schedule (group_name, schedule_date, start_time, end_time, note)
           VALUES (?, ?, ?, ?, ?)""",
        (group_name, schedule_date, start_time, end_time, note or "")
    )
    row_id = cur.lastrowid
    conn.commit()
    conn.close()
    return row_id


def update_pedagog_user_id(old_user_id: int, new_user_id: int):
    """Обновляет user_id педагога (при входе с другого аккаунта)."""
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("UPDATE pedagog_auth SET user_id = ? WHERE user_id = ?", (new_user_id, old_user_id))
    conn.commit()
    conn.close()


def update_student_user_id(old_user_id: int, new_user_id: int):
    """Обновляет user_id студента (при входе с другого аккаунта)."""
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("UPDATE student_auth SET user_id = ? WHERE user_id = ?", (new_user_id, old_user_id))
    cur.execute("UPDATE user_groups SET user_id = ? WHERE user_id = ?", (new_user_id, old_user_id))
    conn.commit()
    conn.close()

