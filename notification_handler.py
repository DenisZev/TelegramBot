"""
Файл для обработки уведомлений о новых заказах.
"""

# Этот файл может содержать дополнительные функции, которые помогут управлять
# подписками на уведомления, хранить информацию о пользователях и т.д.

import sqlite3

def init_db():
    """Инициализация базы данных для хранения информации о пользователях."""
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS users
                      (user_id INTEGER PRIMARY KEY, username TEXT)''')
    conn.commit()
    conn.close()

def subscribe_user(user_id, username):
    """Подписка пользователя на уведомления."""
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute("INSERT OR REPLACE INTO users (user_id, username) VALUES (?, ?)",
                   (user_id, username))
    conn.commit()
    conn.close()

def get_subscribed_users():
    """Получение списка всех подписанных пользователей."""
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute("SELECT user_id, username FROM users")
    users = cursor.fetchall()
    conn.close()
    return users