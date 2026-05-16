import bcrypt
import sqlite3
from app.database.session import get_db_connection
from app.core.config import ADMINS

def register_user(username, password):
    try:
        hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
        is_admin = 1 if username in ADMINS else 0
        conn = get_db_connection()
        conn.execute("INSERT INTO users (username, password, is_admin) VALUES (?, ?, ?)", (username, hashed, is_admin))
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        return False

def login_user(username, password):
    conn = get_db_connection()
    row = conn.execute("SELECT password, is_banned FROM users WHERE username = ?", (username,)).fetchone()
    conn.close()
    if not row: return False
    if row[1]: return "banned"
    return bcrypt.checkpw(password.encode(), row[0].encode())

def get_all_users():
    conn = get_db_connection()
    rows = conn.execute("SELECT username, is_admin, is_banned FROM users").fetchall()
    conn.close()
    return [{"username": r[0], "is_admin": bool(r[1]), "is_banned": bool(r[2])} for r in rows]

def is_admin(username):
    if username in ADMINS: return True
    conn = get_db_connection()
    row = conn.execute("SELECT is_admin FROM users WHERE username = ?", (username,)).fetchone()
    conn.close()
    return bool(row[0]) if row else False

def ban_user(username):
    conn = get_db_connection()
    conn.execute("UPDATE users SET is_banned = 1 WHERE username = ?", (username,))
    conn.commit()
    conn.close()

def unban_user(username):
    conn = get_db_connection()
    conn.execute("UPDATE users SET is_banned = 0 WHERE username = ?", (username,))
    conn.commit()
    conn.close()

def make_admin(username):
    conn = get_db_connection()
    conn.execute("UPDATE users SET is_admin = 1 WHERE username = ?", (username,))
    conn.commit()
    conn.close()

def remove_admin(username):
    conn = get_db_connection()
    conn.execute("UPDATE users SET is_admin = 0 WHERE username = ?", (username,))
    conn.commit()
    conn.close()

def check_username_available(username: str):
    conn = get_db_connection()
    row = conn.execute("SELECT id FROM users WHERE username = ?", (username,)).fetchone()
    conn.close()
    return row is None

def delete_user(username):
    conn = get_db_connection()
    conn.execute("DELETE FROM users WHERE username = ?", (username,))
    conn.commit()
    conn.close()
