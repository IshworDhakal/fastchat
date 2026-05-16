import json
import sqlite3
import bcrypt
from app.database.session import get_db_connection

def save_room_message(room, sender, text, timestamp, reply_to=None, reply_text=None, reply_sender=None):
    conn = get_db_connection()
    cursor = conn.execute(
        "INSERT INTO room_messages (room, sender, text, timestamp, reply_to, reply_text, reply_sender) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (room, sender, text, timestamp, reply_to, reply_text, reply_sender)
    )
    msg_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return msg_id

def load_room_messages(room):
    conn = get_db_connection()
    rows = conn.execute(
        "SELECT id, sender, text, timestamp, edited, reply_to, reply_text, reply_sender FROM room_messages WHERE room = ? ORDER BY id DESC LIMIT 50",
        (room,)
    ).fetchall()
    conn.close()
    messages = [{"id": r[0], "sender": r[1], "text": r[2], "timestamp": r[3], "edited": bool(r[4]),
                 "reply_to": r[5], "reply_text": r[6], "reply_sender": r[7]} for r in reversed(rows)]
    for msg in messages:
        msg["reactions"] = get_reactions(msg["id"], "room")
    return messages

def save_dm(sender, receiver, text, timestamp, reply_to=None, reply_text=None, reply_sender=None):
    conn = get_db_connection()
    cursor = conn.execute(
        "INSERT INTO dm_messages (sender, receiver, text, timestamp, reply_to, reply_text, reply_sender) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (sender, receiver, text, timestamp, reply_to, reply_text, reply_sender)
    )
    msg_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return msg_id

def load_dm(user1, user2):
    conn = get_db_connection()
    rows = conn.execute("""
        SELECT id, sender, receiver, text, timestamp, edited, reply_to, reply_text, reply_sender FROM dm_messages
        WHERE (sender=? AND receiver=?) OR (sender=? AND receiver=?)
        ORDER BY id DESC LIMIT 50
    """, (user1, user2, user2, user1)).fetchall()
    conn.close()
    messages = [{"id": r[0], "sender": r[1], "receiver": r[2], "text": r[3], "timestamp": r[4],
                 "edited": bool(r[5]), "reply_to": r[6], "reply_text": r[7], "reply_sender": r[8]} for r in reversed(rows)]
    for msg in messages:
        msg["reactions"] = get_reactions(msg["id"], "dm")
    return messages

def get_reactions(msg_id, msg_type="room"):
    conn = get_db_connection()
    rows = conn.execute("SELECT emoji, username FROM reactions WHERE msg_id=? AND msg_type=?", (msg_id, msg_type)).fetchall()
    conn.close()
    result = {}
    for emoji, username in rows:
        if emoji not in result: result[emoji] = []
        result[emoji].append(username)
    return result

def toggle_reaction(msg_id, username, emoji, msg_type="room"):
    conn = get_db_connection()
    row = conn.execute("SELECT id FROM reactions WHERE msg_id=? AND username=? AND emoji=? AND msg_type=?",
                       (msg_id, username, emoji, msg_type)).fetchone()
    if row:
        conn.execute("DELETE FROM reactions WHERE id=?", (row[0],))
    else:
        conn.execute("INSERT INTO reactions (msg_id, username, emoji, msg_type) VALUES (?, ?, ?, ?)",
                     (msg_id, username, emoji, msg_type))
    conn.commit()
    conn.close()
    return get_reactions(msg_id, msg_type)

def edit_room_message(msg_id, username, new_text):
    conn = get_db_connection()
    row = conn.execute("SELECT sender FROM room_messages WHERE id=?", (msg_id,)).fetchone()
    if not row or row[0] != username: 
        conn.close()
        return False
    conn.execute("UPDATE room_messages SET text=?, edited=1 WHERE id=?", (new_text, msg_id))
    conn.commit()
    conn.close()
    return True

def delete_room_message_admin(msg_id):
    conn = get_db_connection()
    conn.execute("DELETE FROM room_messages WHERE id=?", (msg_id,))
    conn.commit()
    conn.close()
    return True

def delete_room_message(msg_id, username):
    conn = get_db_connection()
    row = conn.execute("SELECT sender FROM room_messages WHERE id=?", (msg_id,)).fetchone()
    if not row or row[0] != username: 
        conn.close()
        return False
    conn.execute("DELETE FROM room_messages WHERE id=?", (msg_id,))
    conn.commit()
    conn.close()
    return True

def edit_dm_message(msg_id, username, new_text):
    conn = get_db_connection()
    row = conn.execute("SELECT sender FROM dm_messages WHERE id=?", (msg_id,)).fetchone()
    if not row or row[0] != username: 
        conn.close()
        return False
    conn.execute("UPDATE dm_messages SET text=?, edited=1 WHERE id=?", (new_text, msg_id))
    conn.commit()
    conn.close()
    return True

def delete_dm_message(msg_id, username):
    conn = get_db_connection()
    row = conn.execute("SELECT sender, receiver FROM dm_messages WHERE id=?", (msg_id,)).fetchone()
    if not row or row[0] != username: 
        conn.close()
        return False
    conn.execute("DELETE FROM dm_messages WHERE id=?", (msg_id,))
    conn.commit()
    conn.close()
    return True

def search_messages(room, query):
    conn = get_db_connection()
    rows = conn.execute(
        "SELECT id, sender, text, timestamp FROM room_messages WHERE room=? AND text LIKE ? ORDER BY id DESC LIMIT 20",
        (room, f"%{query}%")
    ).fetchall()
    conn.close()
    return [{"id": r[0], "sender": r[1], "text": r[2], "timestamp": r[3]} for r in reversed(rows)]

def create_poll(room, creator, question, options, timestamp):
    conn = get_db_connection()
    votes = json.dumps({opt: [] for opt in options})
    cursor = conn.execute(
        "INSERT INTO polls (room, creator, question, options, votes, timestamp) VALUES (?, ?, ?, ?, ?, ?)",
        (room, creator, question, json.dumps(options), votes, timestamp)
    )
    poll_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return poll_id

def get_poll(poll_id):
    conn = get_db_connection()
    row = conn.execute("SELECT id, room, creator, question, options, votes, timestamp, active FROM polls WHERE id=?", (poll_id,)).fetchone()
    conn.close()
    if not row: return None
    return {"id": row[0], "room": row[1], "creator": row[2], "question": row[3],
            "options": json.loads(row[4]), "votes": json.loads(row[5]),
            "timestamp": row[6], "active": bool(row[7])}

def vote_poll(poll_id, username, option):
    conn = get_db_connection()
    row = conn.execute("SELECT votes FROM polls WHERE id=?", (poll_id,)).fetchone()
    if not row: 
        conn.close()
        return None
    votes = json.loads(row[0])
    for opt in votes:
        if username in votes[opt]:
            votes[opt].remove(username)
    if option in votes:
        votes[option].append(username)
    conn.execute("UPDATE polls SET votes=? WHERE id=?", (json.dumps(votes), poll_id))
    conn.commit()
    conn.close()
    return votes

def get_room_polls(room):
    conn = get_db_connection()
    rows = conn.execute("SELECT id, creator, question, options, votes, timestamp, active FROM polls WHERE room=? ORDER BY id DESC LIMIT 10", (room,)).fetchall()
    conn.close()
    return [{"id": r[0], "creator": r[1], "question": r[2], "options": json.loads(r[3]),
             "votes": json.loads(r[4]), "timestamp": r[5], "active": bool(r[6])} for r in rows]

def create_private_room(name, password, creator):
    try:
        hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
        conn = get_db_connection()
        conn.execute("INSERT INTO private_rooms (name, password, creator) VALUES (?, ?, ?)", (name, hashed, creator))
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        return False

def verify_private_room(name, password):
    conn = get_db_connection()
    row = conn.execute("SELECT password FROM private_rooms WHERE name=?", (name,)).fetchone()
    conn.close()
    if not row: return False
    return bcrypt.checkpw(password.encode(), row[0].encode())

def get_private_rooms():
    conn = get_db_connection()
    rows = conn.execute("SELECT name, creator FROM private_rooms").fetchall()
    conn.close()
    return [{"name": r[0], "creator": r[1]} for r in rows]
