# file: migrate_stats.py
import sqlite3
from config import DB_FILE

def migrate_database():
    """Миграция базы данных для добавления статистики - без link_clicks"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    try:
        # Добавляем новые таблицы
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS note_stats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                note_id INTEGER,
                user_id INTEGER,
                action TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (note_id) REFERENCES notes(id) ON DELETE CASCADE
            )
        ''')

        # УДАЛЕНО: таблица link_clicks

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS video_stats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                video_id INTEGER,
                user_id INTEGER,
                action TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (video_id) REFERENCES addon_videos(id) ON DELETE CASCADE
            )
        ''')
        # В migrate_stats.py добавьте создание таблицы addon_stats:

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS addon_stats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category TEXT NOT NULL,
                addon_index INTEGER NOT NULL,
                views INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(category, addon_index)
            )
        ''')

        cursor.execute('CREATE INDEX IF NOT EXISTS idx_addon_stats_cat ON addon_stats(category, addon_index)')
        # Добавляем поля views
        try:
            cursor.execute('ALTER TABLE notes ADD COLUMN views INTEGER DEFAULT 0')
            print("✅ Добавлено поле views в таблицу notes")
        except:
            print("⚠️ Поле views уже существует в таблице notes")

        try:
            cursor.execute('ALTER TABLE addon_videos ADD COLUMN views INTEGER DEFAULT 0')
            print("✅ Добавлено поле views в таблицу addon_videos")
        except:
            print("⚠️ Поле views уже существует в таблице addon_videos")

        # Создаем индексы
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_note_stats_note ON note_stats(note_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_video_stats_video ON video_stats(video_id)')

        conn.commit()
        print("✅ Миграция базы данных завершена успешно!")

    except Exception as e:
        print(f"❌ Ошибка при миграции: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    migrate_database()