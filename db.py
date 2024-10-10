import sqlite3

# Подключение к базе данных SQLite
conn = sqlite3.connect('votes.db', check_same_thread=False)
cursor = conn.cursor()

def init_db():
    # Создание таблицы для голосов
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS votes (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            candidate TEXT
        )
    ''')
    # Создание таблицы для кандидатов без поля гендера
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS candidates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            photo_url TEXT,
            description TEXT,
            link TEXT
        )
    ''')
    conn.commit()
