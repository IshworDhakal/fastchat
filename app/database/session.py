import sqlite3
from app.core.config import DB_PATH

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    return conn

def init_db():
    conn = get_db_connection()
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id       INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT,
            is_admin INTEGER DEFAULT 0,
            is_banned INTEGER DEFAULT 0
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS room_messages (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            room      TEXT,
            sender    TEXT,
            text      TEXT,
            timestamp TEXT,
            edited    INTEGER DEFAULT 0,
            reply_to  INTEGER DEFAULT NULL,
            reply_text TEXT DEFAULT NULL,
            reply_sender TEXT DEFAULT NULL
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS dm_messages (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            sender    TEXT,
            receiver  TEXT,
            text      TEXT,
            timestamp TEXT,
            edited    INTEGER DEFAULT 0,
            reply_to  INTEGER DEFAULT NULL,
            reply_text TEXT DEFAULT NULL,
            reply_sender TEXT DEFAULT NULL
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS reactions (
            id       INTEGER PRIMARY KEY AUTOINCREMENT,
            msg_id   INTEGER,
            username TEXT,
            emoji    TEXT,
            msg_type TEXT DEFAULT 'room'
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS polls (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            room      TEXT,
            creator   TEXT,
            question  TEXT,
            options   TEXT,
            votes     TEXT DEFAULT '{}',
            timestamp TEXT,
            active    INTEGER DEFAULT 1
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS private_rooms (
            id       INTEGER PRIMARY KEY AUTOINCREMENT,
            name     TEXT UNIQUE,
            password TEXT,
            creator  TEXT
        )
    """)
    # migrations
    for col in ["edited","reply_to","reply_text","reply_sender"]:
        try: conn.execute(f"ALTER TABLE room_messages ADD COLUMN {col} {'INTEGER DEFAULT 0' if col=='edited' else 'INTEGER DEFAULT NULL' if col=='reply_to' else 'TEXT DEFAULT NULL'}")
        except: pass
    for col in ["edited","reply_to","reply_text","reply_sender"]:
        try: conn.execute(f"ALTER TABLE dm_messages ADD COLUMN {col} {'INTEGER DEFAULT 0' if col=='edited' else 'INTEGER DEFAULT NULL' if col=='reply_to' else 'TEXT DEFAULT NULL'}")
        except: pass
    try: conn.execute("ALTER TABLE users ADD COLUMN is_admin INTEGER DEFAULT 0")
    except: pass
    try: conn.execute("ALTER TABLE users ADD COLUMN is_banned INTEGER DEFAULT 0")
    except: pass
    conn.commit()
    conn.close()
