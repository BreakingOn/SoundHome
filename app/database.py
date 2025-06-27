import sqlite3
from sqlite3 import Error
from datetime import datetime


def get_db_connection():
    conn = None
    try:
        conn = sqlite3.connect('music_db.sqlite')
        conn.row_factory = sqlite3.Row  
        print("Подключение к SQLite успешно!")
        return conn
    except Error as e:
        print(f"Ошибка подключения: {e}")
        raise


def init_db():
    commands = [
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            login TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            is_admin BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS tracks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            artist TEXT NOT NULL,
            genre TEXT,
            is_original BOOLEAN DEFAULT FALSE,
            found_by INTEGER NOT NULL,
            found_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (found_by) REFERENCES users(id)
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS discussions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            track_id INTEGER NOT NULL,
            created_by INTEGER NOT NULL,
            title TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (track_id) REFERENCES tracks(id),
            FOREIGN KEY (created_by) REFERENCES users(id)
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS comments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            discussion_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            content TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (discussion_id) REFERENCES discussions(id),
            FOREIGN KEY (user_id) REFERENCES users(id)
        );
        """
    ]
    
    conn = get_db_connection()
    cursor = conn.cursor()
    for command in commands:
        cursor.execute(command)
    conn.commit()
    conn.close()
    print("Таблицы созданы!")

def create_user_simple(login: str, password: str):
    """Простая регистрация пользователя"""
    conn = get_db_connection()
    try:
        conn.execute(
            "INSERT INTO users (login, password, username) VALUES (?, ?, ?)",
            (login, password, f"user_{login}")  
        )
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def check_user_simple(login: str, password: str):
    """Простая проверка авторизации"""
    conn = get_db_connection()
    user = conn.execute(
        "SELECT * FROM users WHERE login = ? AND password = ?",
        (login, password)
    ).fetchone()
    conn.close()
    return user

def save_track(user_id: int, title: str, artist: str, is_original: bool):
    """Сохраняет найденный трек в базу данных"""
    conn = get_db_connection()
    try:
        conn.execute(
            """INSERT INTO tracks 
            (title, artist, is_original, found_by) 
            VALUES (?, ?, ?, ?)""",
            (title, artist, is_original, user_id)
        )
        conn.commit()
        return True
    except Error as e:
        print(f"Ошибка сохранения трека: {e}")
        return False
    finally:
        conn.close()

def get_user_tracks(user_id: int):
    """Получает все треки, найденные пользователем"""
    conn = get_db_connection()
    try:
        tracks = conn.execute(
            """SELECT id, title, artist, is_original, found_at 
            FROM tracks WHERE found_by = ? 
            ORDER BY found_at DESC""",
            (user_id,)
        ).fetchall()
        return tracks
    except Error as e:
        print(f"Ошибка получения треков: {e}")
        return []
    finally:
        conn.close()

def get_user_by_login(login: str):
    """Получает пользователя по логину"""
    conn = get_db_connection()
    user = conn.execute(
        "SELECT * FROM users WHERE login = ?",
        (login,)
    ).fetchone()
    conn.close()
    return user

def create_discussion(user_id: int, track_id: int, title: str):
    """Создает новое обсуждение"""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """INSERT INTO discussions 
            (track_id, created_by, title) 
            VALUES (?, ?, ?)""",
            (track_id, user_id, title)
        )
        discussion_id = cursor.lastrowid
        conn.commit()
        return discussion_id
    except Error as e:
        print(f"Ошибка создания обсуждения: {e}")
        return None
    finally:
        conn.close()

def get_all_discussions():
    """Получает все обсуждения с информацией о треке и авторе"""
    conn = get_db_connection()
    try:
        return conn.execute(
            """SELECT d.id, d.title, d.created_at, 
                  t.title as track_title, t.artist as track_artist,
                  u.username as author
            FROM discussions d
            JOIN tracks t ON d.track_id = t.id
            JOIN users u ON d.created_by = u.id
            ORDER BY d.created_at DESC"""
        ).fetchall()
    except Error as e:
        print(f"Ошибка получения обсуждений: {e}")
        return []
    finally:
        conn.close()

def get_discussion_stats():
    """Получает статистику форума"""
    conn = get_db_connection()
    try:
        total_discussions = conn.execute(
            "SELECT COUNT(*) FROM discussions"
        ).fetchone()[0]
        
        total_comments = conn.execute(
            "SELECT COUNT(*) FROM comments"
        ).fetchone()[0]
        
        return {
            "total_discussions": total_discussions,
            "total_comments": total_comments
        }
    except Error as e:
        print(f"Ошибка получения статистики: {e}")
        return {"total_discussions": 0, "total_comments": 0}
    finally:
        conn.close()

def create_discussion(track_id: int, created_by: int, title: str):
    """Создает новое обсуждение и возвращает его ID"""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """INSERT INTO discussions 
            (track_id, created_by, title) 
            VALUES (?, ?, ?)""",
            (track_id, created_by, title)
        )
        discussion_id = cursor.lastrowid
        conn.commit()
        return discussion_id
    except Error as e:
        print(f"Ошибка создания обсуждения: {e}")
        return None
    finally:
        conn.close()

def get_discussion(discussion_id: int):
    """Получает обсуждение с информацией о треке и авторе"""
    conn = get_db_connection()
    try:
        return conn.execute(
            """SELECT d.id, d.title, d.created_at,
                  t.title as track_title, t.artist as track_artist,
                  u.username as author
            FROM discussions d
            JOIN tracks t ON d.track_id = t.id
            JOIN users u ON d.created_by = u.id
            WHERE d.id = ?""",
            (discussion_id,)
        ).fetchone()
    except Error as e:
        print(f"Ошибка получения обсуждения: {e}")
        return None
    finally:
        conn.close()

def get_comments(discussion_id: int):
    """Получает все комментарии к обсуждению"""
    conn = get_db_connection()
    try:
        return conn.execute(
            """SELECT c.id, c.content, c.created_at,
                  u.username as author
            FROM comments c
            JOIN users u ON c.user_id = u.id
            WHERE c.discussion_id = ?
            ORDER BY c.created_at DESC""",
            (discussion_id,)
        ).fetchall()
    except Error as e:
        print(f"Ошибка получения комментариев: {e}")
        return []
    finally:
        conn.close()

def add_comment(discussion_id: int, user_id: int, content: str):
    """Добавляет комментарий к обсуждению"""
    conn = get_db_connection()
    try:
        conn.execute(
            """INSERT INTO comments 
            (discussion_id, user_id, content) 
            VALUES (?, ?, ?)""",
            (discussion_id, user_id, content)
        )
        conn.commit()
        return True
    except Error as e:
        print(f"Ошибка добавления комментария: {e}")
        return False
    finally:
        conn.close()


def create_admin_account():
    """Создает административный аккаунт по умолчанию"""
    conn = get_db_connection()
    try:
        conn.execute(
            "INSERT OR IGNORE INTO users (username, login, password, is_admin) VALUES (?, ?, ?, ?)",
            ("admin", "admin1", "1", True)
        )
        conn.commit()
    except Error as e:
        print(f"Ошибка создания админского аккаунта: {e}")
    finally:
        conn.close()

def get_all_comments():
    """Получает все комментарии с информацией об авторе и обсуждении"""
    conn = get_db_connection()
    try:
        return conn.execute(
            """SELECT c.id, c.content, c.created_at,
                  u.username as author,
                  d.title as discussion_title,
                  d.id as discussion_id
            FROM comments c
            JOIN users u ON c.user_id = u.id
            JOIN discussions d ON c.discussion_id = d.id
            ORDER BY c.created_at DESC"""
        ).fetchall()
    except Error as e:
        print(f"Ошибка получения комментариев: {e}")
        return []
    finally:
        conn.close()

def delete_comment(comment_id: int):
    """Удаляет комментарий из БД"""
    conn = get_db_connection()
    try:
        conn.execute("DELETE FROM comments WHERE id = ?", (comment_id,))
        conn.commit()
        return True
    except Error as e:
        print(f"Ошибка удаления комментария: {e}")
        return False
    finally:
        conn.close()

create_admin_account()

init_db()