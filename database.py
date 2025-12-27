# file: database.py
import sqlite3
import hashlib
from datetime import datetime
from config import DB_FILE


class Database:
    def __init__(self):
        self.init_db()

    # В методе init_db удалите создание таблицы link_clicks:
    def init_db(self):
        """Инициализация базы данных"""
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()

        print("🔄 Инициализация базы данных...")

        # Таблица заметок
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS notes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                title TEXT,
                hashtag TEXT UNIQUE,
                message_id INTEGER,
                chat_id INTEGER,
                views INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Таблица пользовательских видео для аддонов
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS addon_videos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                addon_category TEXT,
                addon_index INTEGER,
                user_id INTEGER,
                youtube_url TEXT,
                title TEXT,
                description TEXT DEFAULT '',
                likes INTEGER DEFAULT 0,
                dislikes INTEGER DEFAULT 0,
                views INTEGER DEFAULT 0,
                verified BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Таблица лайков видео
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS video_likes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                video_id INTEGER,
                user_id INTEGER,
                is_like BOOLEAN,  -- TRUE = like, FALSE = dislike
                UNIQUE(video_id, user_id)
            )
        ''')

        # Таблица для статистики заметок
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS note_stats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                note_id INTEGER,
                user_id INTEGER,
                action TEXT,  -- 'view', 'search', 'open'
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (note_id) REFERENCES notes(id) ON DELETE CASCADE
            )
        ''')

        # УДАЛЕНО: Таблица для статистики ссылок (GitHub, YouTube)

        # Таблица для статистики видео
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS video_stats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                video_id INTEGER,
                user_id INTEGER,
                action TEXT,  -- 'view', 'like', 'dislike', 'add'
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (video_id) REFERENCES addon_videos(id) ON DELETE CASCADE
            )
        ''')
        # В методе init_db() добавьте после создания таблицы video_stats:

        # Таблица для статистики просмотров аддонов
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

        # Индекс для быстрого поиска


        # Индексы для быстрого поиска
        try:
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_videos_addon ON addon_videos(addon_category, addon_index)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_videos_user ON addon_videos(user_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_note_stats_note ON note_stats(note_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_video_stats_video ON video_stats(video_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_addon_stats_cat ON addon_stats(category, addon_index)')
        except Exception as e:
            print(f"⚠️ Ошибка при создании индексов: {e}")

        conn.commit()
        conn.close()
        print("✅ База данных инициализирована")

    # ========== ЗАМЕТКИ ==========

    def save_note(self, user_id, title, message_id, chat_id):
        """Сохраняем только метаданные заметки"""
        hashtag = self._generate_hashtag(title, user_id)
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        try:
            cursor.execute('''
                INSERT INTO notes (user_id, title, hashtag, message_id, chat_id)
                VALUES (?, ?, ?, ?, ?)
            ''', (user_id, title, hashtag, message_id, chat_id))
            conn.commit()
            note_id = cursor.lastrowid
            print(f"✅ Сохранена заметка: user_id={user_id}, title='{title}', note_id={note_id}")
        except Exception as e:
            print(f"❌ Ошибка при сохранении заметки: {e}")
            raise
        finally:
            conn.close()
        return note_id, hashtag

    def get_user_notes(self, user_id, limit=20):
        """Получаем только метаданные заметок пользователя"""
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        try:
            cursor.execute('''
                SELECT id, title, hashtag, views, created_at 
                FROM notes 
                WHERE user_id = ? 
                ORDER BY created_at DESC 
                LIMIT ?
            ''', (user_id, limit))
            notes = cursor.fetchall()
            print(f"📊 Получено {len(notes)} заметок пользователя {user_id}")
            return notes
        except Exception as e:
            print(f"❌ Ошибка при получении заметок пользователя {user_id}: {e}")
            return []
        finally:
            conn.close()

    def get_note(self, note_id):
        """Получаем метаданные заметки"""
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        try:
            cursor.execute('SELECT * FROM notes WHERE id = ?', (note_id,))
            note = cursor.fetchone()
            print(f"📄 Получена заметка {note_id}")
            return note
        except Exception as e:
            print(f"❌ Ошибка при получении заметки {note_id}: {e}")
            return None
        finally:
            conn.close()

    def search_notes(self, user_id, query):
        """Поиск заметок по названию или хэштегу"""
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        try:
            cursor.execute('''
                SELECT id, title, hashtag, views, created_at 
                FROM notes 
                WHERE user_id = ? AND (title LIKE ? OR hashtag LIKE ?)
                ORDER BY created_at DESC
            ''', (user_id, f'%{query}%', f'%{query}%'))
            notes = cursor.fetchall()
            print(f"🔍 Найдено {len(notes)} заметок по запросу '{query}' для пользователя {user_id}")
            return notes
        except Exception as e:
            print(f"❌ Ошибка при поиске заметок: {e}")
            return []
        finally:
            conn.close()

    def _generate_hashtag(self, title, user_id):
        """Генерируем уникальный хэштег"""
        base = f"{title}_{user_id}_{datetime.now().timestamp()}"
        hashtag = f"tag{hashlib.md5(base.encode()).hexdigest()[:8]}"
        print(f"🏷️ Сгенерирован хэштег: {hashtag}")
        return hashtag

    def increment_note_views(self, note_id):
        """Увеличение счетчика просмотров заметки"""
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        try:
            cursor.execute('UPDATE notes SET views = views + 1 WHERE id = ?', (note_id,))
            conn.commit()
            return True
        except Exception as e:
            print(f"❌ Ошибка при увеличении просмотров заметки: {e}")
            return False
        finally:
            conn.close()

    def get_note_views(self, note_id):
        """Получение количества просмотров заметки"""
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        try:
            cursor.execute('SELECT views FROM notes WHERE id = ?', (note_id,))
            result = cursor.fetchone()
            return result[0] if result else 0
        except Exception as e:
            print(f"❌ Ошибка при получении просмотров заметки: {e}")
            return 0
        finally:
            conn.close()

    # ========== ВИДЕО ==========

    def add_video(self, category, index, user_id, youtube_url, title):
        """Добавление пользовательского видео"""
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        try:
            cursor.execute('''
                INSERT INTO addon_videos 
                (addon_category, addon_index, user_id, youtube_url, title)
                VALUES (?, ?, ?, ?, ?)
            ''', (category, index, user_id, youtube_url, title))
            conn.commit()
            video_id = cursor.lastrowid
            print(f"✅ Добавлено видео: user_id={user_id}, video_id={video_id}, аддон={category}/{index}")
            return True, video_id
        except Exception as e:
            print(f"❌ Ошибка при добавлении видео: {e}")
            return False, f"Ошибка базы данных: {str(e)}"
        finally:
            conn.close()

    def get_videos(self, category, index, limit=20):
        """Получение видео для аддона"""
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        try:
            cursor.execute('''
                SELECT id, user_id, youtube_url, title, description, likes, dislikes, views, verified, created_at
                FROM addon_videos
                WHERE addon_category = ? AND addon_index = ?
                ORDER BY likes DESC, created_at DESC
                LIMIT ?
            ''', (category, index, limit))
            videos = cursor.fetchall()
            print(f"📊 Получено {len(videos)} видео для аддона {category}/{index}")
            return videos
        except Exception as e:
            print(f"❌ Ошибка при получении видео: {e}")
            return []
        finally:
            conn.close()

    def get_video_by_id(self, video_id):
        """Получение видео по ID"""
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        try:
            cursor.execute('''
                SELECT id, addon_category, addon_index, user_id, youtube_url, title, 
                       description, likes, dislikes, views, verified, created_at
                FROM addon_videos
                WHERE id = ?
            ''', (video_id,))
            video = cursor.fetchone()
            print(f"📊 Получено видео {video_id}")
            return video
        except Exception as e:
            print(f"❌ Ошибка при получении видео {video_id}: {e}")
            return None
        finally:
            conn.close()

    def rate_video(self, video_id, user_id, is_like):
        """Лайк или дизлайк видео"""
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        try:
            # Проверяем, не оценивал ли уже
            cursor.execute('SELECT COUNT(*) FROM video_likes WHERE video_id = ? AND user_id = ?',
                           (video_id, user_id))

            if cursor.fetchone()[0] > 0:
                # Обновляем существующую оценку
                cursor.execute('UPDATE video_likes SET is_like = ? WHERE video_id = ? AND user_id = ?',
                               (is_like, video_id, user_id))

                # Получаем старую оценку
                cursor.execute('SELECT is_like FROM video_likes WHERE video_id = ? AND user_id = ?',
                               (video_id, user_id))
                old_is_like = cursor.fetchone()[0]

                # Обновляем счетчики
                if old_is_like and not is_like:  # был лайк, стал дизлайк
                    cursor.execute('UPDATE addon_videos SET likes = likes - 1, dislikes = dislikes + 1 WHERE id = ?',
                                   (video_id,))
                elif not old_is_like and is_like:  # был дизлайк, стал лайк
                    cursor.execute('UPDATE addon_videos SET likes = likes + 1, dislikes = dislikes - 1 WHERE id = ?',
                                   (video_id,))
            else:
                # Добавляем новую оценку
                cursor.execute('INSERT INTO video_likes (video_id, user_id, is_like) VALUES (?, ?, ?)',
                               (video_id, user_id, is_like))

                # Обновляем счетчики
                if is_like:
                    cursor.execute('UPDATE addon_videos SET likes = likes + 1 WHERE id = ?', (video_id,))
                else:
                    cursor.execute('UPDATE addon_videos SET dislikes = dislikes + 1 WHERE id = ?', (video_id,))

            conn.commit()
            action = "лайк" if is_like else "дизлайк"
            print(f"{'👍' if is_like else '👎'} Пользователь {user_id} поставил {action} видео {video_id}")
            return True, f"{'Лайк' if is_like else 'Дизлайк'} учтен"
        except Exception as e:
            print(f"❌ Ошибка при оценке видео {video_id} пользователем {user_id}: {e}")
            return False, f"Ошибка: {str(e)}"
        finally:
            conn.close()

    def get_user_rating(self, video_id, user_id):
        """Получение оценки пользователя для видео"""
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        try:
            cursor.execute('SELECT is_like FROM video_likes WHERE video_id = ? AND user_id = ?',
                           (video_id, user_id))
            result = cursor.fetchone()
            if result:
                return result[0]  # True = like, False = dislike
            return None
        except Exception as e:
            print(f"❌ Ошибка при получении оценки пользователя: {e}")
            return None
        finally:
            conn.close()

    def delete_video(self, video_id, user_id):
        """Удаление видео пользователем"""
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        try:
            # Пользователь может удалить только свое видео
            cursor.execute('DELETE FROM addon_videos WHERE id = ? AND user_id = ?',
                           (video_id, user_id))
            # Удаляем связанные оценки
            cursor.execute('DELETE FROM video_likes WHERE video_id = ?', (video_id,))
            conn.commit()
            deleted = cursor.rowcount > 0
            if deleted:
                print(f"🗑️ Удалено видео {video_id} пользователем {user_id}")
            return deleted
        except Exception as e:
            print(f"❌ Ошибка при удалении видео {video_id}: {e}")
            return False
        finally:
            conn.close()

    def delete_addon(category, index):
        """Удаление аддона (для админов)"""
        addons = get_addons(category)
        if index < 0 or index >= len(addons):
            return False

        deleted_name = addons[index]["name"]
        ADDONS_DATA[category].pop(index)

        # Если в категории больше нет аддонов, удаляем категорию
        if not ADDONS_DATA[category]:
            del ADDONS_DATA[category]

        save_data()
        print(f"🗑️ Удален аддон: {deleted_name} из {category}")
        return True

    def get_total_videos(self):
        """Получение общего количества видео"""
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        try:
            cursor.execute('SELECT COUNT(*) FROM addon_videos')
            count = cursor.fetchone()[0]
            return count
        except Exception as e:
            print(f"❌ Ошибка при получении количества видео: {e}")
            return 0
        finally:
            conn.close()

    # ========== СТАТИСТИКА ==========

    def log_note_action(self, note_id, user_id, action):
        """Логирование действий с заметками"""
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        try:
            cursor.execute('''
                INSERT INTO note_stats (note_id, user_id, action)
                VALUES (?, ?, ?)
            ''', (note_id, user_id, action))
            conn.commit()
            return True
        except Exception as e:
            print(f"❌ Ошибка при логировании действия с заметкой: {e}")
            return False
        finally:
            conn.close()

    def log_video_action(self, video_id, user_id, action):
        """Логирование действий с видео"""
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        try:
            cursor.execute('''
                INSERT INTO video_stats (video_id, user_id, action)
                VALUES (?, ?, ?)
            ''', (video_id, user_id, action))
            conn.commit()
            return True
        except Exception as e:
            print(f"❌ Ошибка при логировании действия с видео: {e}")
            return False
        finally:
            conn.close()
    # В класс Database добавьте после методов для видео:

    def increment_addon_views(self, category, addon_index):
        """Увеличение счетчика просмотров аддона"""
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        try:
            # Пытаемся обновить существующую запись
            cursor.execute('''
                UPDATE addon_stats 
                SET views = views + 1 
                WHERE category = ? AND addon_index = ?
            ''', (category, addon_index))

            # Если записи не было, создаем новую
            if cursor.rowcount == 0:
                cursor.execute('''
                    INSERT INTO addon_stats (category, addon_index, views)
                    VALUES (?, ?, 1)
                ''', (category, addon_index))

            conn.commit()
            return True
        except Exception as e:
            print(f"❌ Ошибка при увеличении просмотров аддона {category}/{addon_index}: {e}")
            return False
        finally:
            conn.close()

    def get_addon_views(self, category, addon_index):
        """Получение количества просмотров аддона"""
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        try:
            cursor.execute('''
                SELECT views FROM addon_stats 
                WHERE category = ? AND addon_index = ?
            ''', (category, addon_index))
            result = cursor.fetchone()
            return result[0] if result else 0
        except Exception as e:
            print(f"❌ Ошибка при получении просмотров аддона: {e}")
            return 0
        finally:
            conn.close()

    def get_top_addons_by_views(self, limit=10, days=30):
        """Получение топ аддонов по просмотрам"""
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        try:
            query = '''
                SELECT 
                    category,
                    addon_index,
                    views,
                    created_at
                FROM addon_stats
                WHERE created_at >= datetime('now', ?)
                ORDER BY views DESC
                LIMIT ?
            '''
            params = [f'-{days} days', limit]

            cursor.execute(query, params)
            addons = cursor.fetchall()
            return addons
        except Exception as e:
            print(f"❌ Ошибка при получении топ аддонов: {e}")
            return []
        finally:
            conn.close()

    def get_overall_stats(self):
        """Общая статистика бота"""
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        try:
            stats = {}

            # Статистика заметок
            cursor.execute('SELECT COUNT(*), SUM(views) FROM notes')
            notes_result = cursor.fetchone()
            stats['notes'] = {
                'total': notes_result[0] or 0,
                'total_views': notes_result[1] or 0
            }

            # Статистика видео
            cursor.execute('SELECT COUNT(*), SUM(views), SUM(likes), SUM(dislikes) FROM addon_videos')
            videos_result = cursor.fetchone()
            stats['videos'] = {
                'total': videos_result[0] or 0,
                'total_views': videos_result[1] or 0,
                'total_likes': videos_result[2] or 0,
                'total_dislikes': videos_result[3] or 0
            }

            # Статистика аддонов (НОВОЕ)
            cursor.execute('SELECT COUNT(*), SUM(views) FROM addon_stats')
            addons_result = cursor.fetchone()
            stats['addons'] = {
                'total': addons_result[0] or 0,
                'total_views': addons_result[1] or 0
            }

            # Статистика пользователей
            cursor.execute('SELECT COUNT(DISTINCT user_id) FROM notes')
            notes_users = cursor.fetchone()[0] or 0
            cursor.execute('SELECT COUNT(DISTINCT user_id) FROM addon_videos')
            videos_users = cursor.fetchone()[0] or 0
            cursor.execute('SELECT COUNT(DISTINCT user_id) FROM video_likes')
            likes_users = cursor.fetchone()[0] or 0

            stats['users'] = {
                'notes': notes_users,
                'videos': videos_users,
                'likes': likes_users
            }

            return stats
        except Exception as e:
            print(f"❌ Ошибка при получении общей статистики: {e}")
            return {}
        finally:
            conn.close()

    def get_video_stats(self, video_id=None, days=7):
        """Получение статистики по видео"""
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        try:
            query = '''
                SELECT 
                    video_id,
                    action,
                    COUNT(*) as count,
                    COUNT(DISTINCT user_id) as unique_users
                FROM video_stats
                WHERE created_at >= datetime('now', ?)
            '''
            params = [f'-{days} days']

            if video_id:
                query += ' AND video_id = ?'
                params.append(video_id)

            query += ' GROUP BY video_id, action ORDER BY video_id, action'

            cursor.execute(query, params)
            stats = cursor.fetchall()

            result = {}
            for stat in stats:
                vid = stat[0]
                if vid not in result:
                    result[vid] = {}
                result[vid][stat[1]] = {
                    'count': stat[2],
                    'unique_users': stat[3]
                }

            return result
        except Exception as e:
            print(f"❌ Ошибка при получении статистики видео: {e}")
            return {}
        finally:
            conn.close()

    # В функции get_top_videos в database.py ИСПРАВЬТЕ запрос:
    def get_top_videos(self, category=None, index=None, limit=10, days=30):
        """Получение топ видео по просмотрам"""
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        try:
            query = '''
                SELECT 
                    v.id,
                    v.title,
                    v.youtube_url,
                    v.views,
                    v.likes,
                    v.dislikes,
                    v.addon_category,   # <- ДОБАВЬТЕ это поле
                    v.addon_index       # <- ДОБАВЬТЕ это поле
                FROM addon_videos v
                WHERE v.created_at >= datetime('now', ?)
            '''
            # ... остальной код функции без изменений

            params = [f'-{days} days']

            if category and index is not None:
                query += ' AND v.addon_category = ? AND v.addon_index = ?'
                params.extend([category, index])

            query += '''
                GROUP BY v.id
                ORDER BY v.views DESC, v.likes DESC
                LIMIT ?
            '''
            params.append(limit)

            cursor.execute(query, params)
            videos = cursor.fetchall()

            return videos
        except Exception as e:
            print(f"❌ Ошибка при получении топ видео: {e}")
            return []
        finally:
            conn.close()


# В database.py добавьте в класс Database новые методы:

# Добавьте после метода get_link_stats в классе Database:

    def get_addon_link_stats(self, category, index, days=30):
        """Получение статистики кликов по ссылкам для конкретного аддона"""
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        try:
            query = '''
                SELECT 
                    link_type,
                    COUNT(*) as total_clicks,
                    COUNT(DISTINCT user_id) as unique_users,
                    COUNT(CASE WHEN created_at >= datetime('now', ?) THEN 1 END) as recent_clicks
                FROM link_clicks
                WHERE addon_category = ? AND addon_index = ?
                GROUP BY link_type
                ORDER BY link_type
            '''
            params = [f'-{days} days', category, index]

            cursor.execute(query, params)
            stats = cursor.fetchall()

            result = {}
            for stat in stats:
                link_type = stat[0]
                result[link_type] = {
                    'total_clicks': stat[1],
                    'unique_users': stat[2],
                    'recent_clicks': stat[3]
                }

            return result
        except Exception as e:
            print(f"❌ Ошибка при получении статистики ссылок аддона: {e}")
            return {}
        finally:
            conn.close()


    def get_addon_video_stats(self, category, index, days=30):
        """Получение статистики по видео для конкретного аддона"""
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        try:
            # Статистика по добавленным видео
            cursor.execute('''
                SELECT 
                    COUNT(*) as total_videos,
                    SUM(views) as total_views,
                    SUM(likes) as total_likes,
                    SUM(dislikes) as total_dislikes
                FROM addon_videos
                WHERE addon_category = ? AND addon_index = ?
            ''', (category, index))

            video_stats = cursor.fetchone()

            # Статистика по действиям с видео за период
            cursor.execute('''
                SELECT 
                    vs.action,
                    COUNT(*) as count,
                    COUNT(DISTINCT vs.user_id) as unique_users
                FROM video_stats vs
                JOIN addon_videos av ON vs.video_id = av.id
                WHERE av.addon_category = ? 
                  AND av.addon_index = ?
                  AND vs.created_at >= datetime('now', ?)
                GROUP BY vs.action
            ''', (category, index, f'-{days} days'))

            recent_actions = {}
            for row in cursor.fetchall():
                action = row[0]
                recent_actions[action] = {
                    'count': row[1],
                    'unique_users': row[2]
                }

            return {
                'total_videos': video_stats[0] or 0,
                'total_views': video_stats[1] or 0,
                'total_likes': video_stats[2] or 0,
                'total_dislikes': video_stats[3] or 0,
                'recent_actions': recent_actions
            }
        except Exception as e:
            print(f"❌ Ошибка при получении статистики видео аддона: {e}")
            return {}
        finally:
            conn.close()
# Создаем глобальный экземпляр базы данных
db = Database()