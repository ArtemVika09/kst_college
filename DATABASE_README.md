# Документация по базе данных

## Структура файлов

- `database_schema.sql` - SQL схема базы данных (для справки)
- `database.py` - Модуль для работы с базой данных
- `kst_bot.db` - Файл базы данных SQLite (создается автоматически)

## Использование

Все функции работы с базой данных вынесены в модуль `database.py`. 

### Основные функции:

#### Для педагогов:
- `database.is_pedagog_registered(user_id)` - проверка регистрации
- `database.register_pedagog(user_id, fio, password)` - регистрация
- `database.login_pedagog(fio, password)` - вход
- `database.get_pedagog_fio(user_id)` - получение ФИО

#### Для студентов:
- `database.is_student_registered(user_id)` - проверка регистрации
- `database.register_student(user_id, fio, group_name, password)` - регистрация
- `database.login_student(fio, password)` - вход
- `database.get_student_info(user_id)` - получение информации
- `database.get_student_group(user_id)` - получение группы
- `database.set_student_group(user_id, group_name)` - установка группы

#### Для опросов:
- `database.get_polls_list_pedagog()` - список опросов для педагогов
- `database.get_polls_list_student(user_group)` - список опросов для студентов
- `database.save_poll(...)` - сохранение опроса
- `database.get_student_user_ids_to_notify(target_groups)` - получение ID для уведомлений

#### Для заказов справок:
- `database.save_certificate_order(user_id, fio, group_name)` - сохранение заказа

## Инициализация

База данных инициализируется автоматически при запуске бота через функцию `database.init_db(CONFIG_DIR)`.

## Безопасность

Пароли хранятся в виде хешей SHA256. Функция `database.hash_password(password)` используется для хеширования.

