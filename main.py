from fastapi import FastAPI, WebSocket, WebSocketDisconnect, UploadFile, File
from fastapi.responses import HTMLResponse, FileResponse
from typing import Dict
import json, datetime, sqlite3, bcrypt, os, uuid, asyncio

app = FastAPI()

DATA_DIR = os.environ.get("RAILWAY_VOLUME_MOUNT_PATH", ".")
DB_PATH = os.path.join(DATA_DIR, "chat.db")
UPLOAD_DIR = os.path.join(DATA_DIR, "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

ADMINS = ["Ishwor123"]

def init_db():
    conn = sqlite3.connect(DB_PATH)
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

def register_user(username, password):
    try:
        hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
        is_admin = 1 if username in ADMINS else 0
        conn = sqlite3.connect(DB_PATH)
        conn.execute("INSERT INTO users (username, password, is_admin) VALUES (?, ?, ?)", (username, hashed, is_admin))
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        return False

def login_user(username, password):
    conn = sqlite3.connect(DB_PATH)
    row = conn.execute("SELECT password, is_banned FROM users WHERE username = ?", (username,)).fetchone()
    conn.close()
    if not row: return False
    if row[1]: return "banned"
    return bcrypt.checkpw(password.encode(), row[0].encode())

def get_all_users():
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute("SELECT username, is_admin, is_banned FROM users").fetchall()
    conn.close()
    return [{"username": r[0], "is_admin": bool(r[1]), "is_banned": bool(r[2])} for r in rows]

def is_admin(username):
    if username in ADMINS: return True
    conn = sqlite3.connect(DB_PATH)
    row = conn.execute("SELECT is_admin FROM users WHERE username = ?", (username,)).fetchone()
    conn.close()
    return bool(row[0]) if row else False

def ban_user(username):
    conn = sqlite3.connect(DB_PATH)
    conn.execute("UPDATE users SET is_banned = 1 WHERE username = ?", (username,))
    conn.commit(); conn.close()

def unban_user(username):
    conn = sqlite3.connect(DB_PATH)
    conn.execute("UPDATE users SET is_banned = 0 WHERE username = ?", (username,))
    conn.commit(); conn.close()

def make_admin(username):
    conn = sqlite3.connect(DB_PATH)
    conn.execute("UPDATE users SET is_admin = 1 WHERE username = ?", (username,))
    conn.commit(); conn.close()

def remove_admin(username):
    conn = sqlite3.connect(DB_PATH)
    conn.execute("UPDATE users SET is_admin = 0 WHERE username = ?", (username,))
    conn.commit(); conn.close()

def save_room_message(room, sender, text, timestamp, reply_to=None, reply_text=None, reply_sender=None):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.execute(
        "INSERT INTO room_messages (room, sender, text, timestamp, reply_to, reply_text, reply_sender) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (room, sender, text, timestamp, reply_to, reply_text, reply_sender)
    )
    msg_id = cursor.lastrowid
    conn.commit(); conn.close()
    return msg_id

def load_room_messages(room):
    conn = sqlite3.connect(DB_PATH)
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
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.execute(
        "INSERT INTO dm_messages (sender, receiver, text, timestamp, reply_to, reply_text, reply_sender) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (sender, receiver, text, timestamp, reply_to, reply_text, reply_sender)
    )
    msg_id = cursor.lastrowid
    conn.commit(); conn.close()
    return msg_id

def load_dm(user1, user2):
    conn = sqlite3.connect(DB_PATH)
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
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute("SELECT emoji, username FROM reactions WHERE msg_id=? AND msg_type=?", (msg_id, msg_type)).fetchall()
    conn.close()
    result = {}
    for emoji, username in rows:
        if emoji not in result: result[emoji] = []
        result[emoji].append(username)
    return result

def toggle_reaction(msg_id, username, emoji, msg_type="room"):
    conn = sqlite3.connect(DB_PATH)
    row = conn.execute("SELECT id FROM reactions WHERE msg_id=? AND username=? AND emoji=? AND msg_type=?",
                       (msg_id, username, emoji, msg_type)).fetchone()
    if row:
        conn.execute("DELETE FROM reactions WHERE id=?", (row[0],))
    else:
        conn.execute("INSERT INTO reactions (msg_id, username, emoji, msg_type) VALUES (?, ?, ?, ?)",
                     (msg_id, username, emoji, msg_type))
    conn.commit(); conn.close()
    return get_reactions(msg_id, msg_type)

def edit_room_message(msg_id, username, new_text):
    conn = sqlite3.connect(DB_PATH)
    row = conn.execute("SELECT sender FROM room_messages WHERE id=?", (msg_id,)).fetchone()
    if not row or row[0] != username: conn.close(); return False
    conn.execute("UPDATE room_messages SET text=?, edited=1 WHERE id=?", (new_text, msg_id))
    conn.commit(); conn.close(); return True

def delete_room_message_admin(msg_id):
    conn = sqlite3.connect(DB_PATH)
    conn.execute("DELETE FROM room_messages WHERE id=?", (msg_id,))
    conn.commit(); conn.close(); return True

def delete_room_message(msg_id, username):
    conn = sqlite3.connect(DB_PATH)
    row = conn.execute("SELECT sender FROM room_messages WHERE id=?", (msg_id,)).fetchone()
    if not row or row[0] != username: conn.close(); return False
    conn.execute("DELETE FROM room_messages WHERE id=?", (msg_id,))
    conn.commit(); conn.close(); return True

def edit_dm_message(msg_id, username, new_text):
    conn = sqlite3.connect(DB_PATH)
    row = conn.execute("SELECT sender FROM dm_messages WHERE id=?", (msg_id,)).fetchone()
    if not row or row[0] != username: conn.close(); return False
    conn.execute("UPDATE dm_messages SET text=?, edited=1 WHERE id=?", (new_text, msg_id))
    conn.commit(); conn.close(); return True

def delete_dm_message(msg_id, username):
    conn = sqlite3.connect(DB_PATH)
    row = conn.execute("SELECT sender, receiver FROM dm_messages WHERE id=?", (msg_id,)).fetchone()
    if not row or row[0] != username: conn.close(); return False
    conn.execute("DELETE FROM dm_messages WHERE id=?", (msg_id,))
    conn.commit(); conn.close(); return True

def search_messages(room, query):
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute(
        "SELECT id, sender, text, timestamp FROM room_messages WHERE room=? AND text LIKE ? ORDER BY id DESC LIMIT 20",
        (room, f"%{query}%")
    ).fetchall()
    conn.close()
    return [{"id": r[0], "sender": r[1], "text": r[2], "timestamp": r[3]} for r in reversed(rows)]

def create_poll(room, creator, question, options, timestamp):
    conn = sqlite3.connect(DB_PATH)
    votes = json.dumps({opt: [] for opt in options})
    cursor = conn.execute(
        "INSERT INTO polls (room, creator, question, options, votes, timestamp) VALUES (?, ?, ?, ?, ?, ?)",
        (room, creator, question, json.dumps(options), votes, timestamp)
    )
    poll_id = cursor.lastrowid
    conn.commit(); conn.close()
    return poll_id

def get_poll(poll_id):
    conn = sqlite3.connect(DB_PATH)
    row = conn.execute("SELECT id, room, creator, question, options, votes, timestamp, active FROM polls WHERE id=?", (poll_id,)).fetchone()
    conn.close()
    if not row: return None
    return {"id": row[0], "room": row[1], "creator": row[2], "question": row[3],
            "options": json.loads(row[4]), "votes": json.loads(row[5]),
            "timestamp": row[6], "active": bool(row[7])}

def vote_poll(poll_id, username, option):
    conn = sqlite3.connect(DB_PATH)
    row = conn.execute("SELECT votes FROM polls WHERE id=?", (poll_id,)).fetchone()
    if not row: conn.close(); return None
    votes = json.loads(row[0])
    for opt in votes:
        if username in votes[opt]:
            votes[opt].remove(username)
    if option in votes:
        votes[option].append(username)
    conn.execute("UPDATE polls SET votes=? WHERE id=?", (json.dumps(votes), poll_id))
    conn.commit(); conn.close()
    return votes

def get_room_polls(room):
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute("SELECT id, creator, question, options, votes, timestamp, active FROM polls WHERE room=? ORDER BY id DESC LIMIT 10", (room,)).fetchall()
    conn.close()
    return [{"id": r[0], "creator": r[1], "question": r[2], "options": json.loads(r[3]),
             "votes": json.loads(r[4]), "timestamp": r[5], "active": bool(r[6])} for r in rows]

def create_private_room(name, password, creator):
    try:
        hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
        conn = sqlite3.connect(DB_PATH)
        conn.execute("INSERT INTO private_rooms (name, password, creator) VALUES (?, ?, ?)", (name, hashed, creator))
        conn.commit(); conn.close()
        return True
    except sqlite3.IntegrityError:
        return False

def verify_private_room(name, password):
    conn = sqlite3.connect(DB_PATH)
    row = conn.execute("SELECT password FROM private_rooms WHERE name=?", (name,)).fetchone()
    conn.close()
    if not row: return False
    return bcrypt.checkpw(password.encode(), row[0].encode())

def get_private_rooms():
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute("SELECT name, creator FROM private_rooms").fetchall()
    conn.close()
    return [{"name": r[0], "creator": r[1]} for r in rows]

init_db()

ROOMS = ["general", "random", "tech"]

class Manager:
    def __init__(self):
        self.users: Dict[str, WebSocket] = {}
        self.rooms: Dict[str, Dict[str, WebSocket]] = {r: {} for r in ROOMS}
        self.private_room_members: Dict[str, set] = {}

    async def connect(self, username, websocket):
        self.users[username] = websocket

    def disconnect(self, username):
        self.users.pop(username, None)
        for room in self.rooms:
            self.rooms[room].pop(username, None)

    async def send_to(self, username, message):
        ws = self.users.get(username)
        if ws:
            try: await ws.send_text(json.dumps(message))
            except: pass

    async def broadcast_room(self, room, message):
        if room not in self.rooms: return
        dead = []
        for username, ws in self.rooms[room].items():
            try: await ws.send_text(json.dumps(message))
            except: dead.append(username)
        for u in dead: self.rooms[room].pop(u, None)

    async def broadcast_all(self, message):
        for username in list(self.users.keys()):
            await self.send_to(username, message)

    def online_users(self):
        return list(self.users.keys())

    def users_in_room(self, room):
        return list(self.rooms.get(room, {}).keys())

    def ensure_room(self, room):
        if room not in self.rooms:
            self.rooms[room] = {}

manager = Manager()

@app.get("/", response_class=HTMLResponse)
async def get():
    with open("index.html", encoding="utf-8") as f:
        return f.read()

@app.get("/check-username/{username}")
async def check_username(username: str):
    conn = sqlite3.connect(DB_PATH)
    row = conn.execute("SELECT id FROM users WHERE username = ?", (username,)).fetchone()
    conn.close()
    return {"available": row is None}

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    ext = file.filename.split(".")[-1].lower()
    if ext not in ["jpg", "jpeg", "png", "gif", "webp"]:
        return {"error": "Invalid file type."}
    filename = f"{uuid.uuid4()}.{ext}"
    path = os.path.join(UPLOAD_DIR, filename)
    with open(path, "wb") as f:
        content = await file.read()
        f.write(content)
    return {"url": f"/uploads/{filename}"}

@app.get("/uploads/{filename}")
async def get_upload(filename: str):
    path = os.path.join(UPLOAD_DIR, filename)
    if not os.path.exists(path):
        return {"error": "Not found"}
    return FileResponse(path)

@app.get("/logo.png")
async def get_logo():
    return FileResponse("logo.png")

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()

    data = json.loads(await websocket.receive_text())
    action   = data.get("action")
    username = data.get("username", "").strip()
    password = data.get("password", "").strip()

    if not username or not password:
        await websocket.send_text(json.dumps({"type": "auth_fail", "text": "Username and password required."}))
        await websocket.close(); return

    if action == "register":
        if not register_user(username, password):
            await websocket.send_text(json.dumps({"type": "auth_fail", "text": "Username already taken."}))
            await websocket.close(); return
    elif action == "login":
        result = login_user(username, password)
        if result == "banned":
            await websocket.send_text(json.dumps({"type": "auth_fail", "text": "You have been banned from GufGaff."}))
            await websocket.close(); return
        if not result:
            await websocket.send_text(json.dumps({"type": "auth_fail", "text": "Wrong username or password."}))
            await websocket.close(); return

    await manager.connect(username, websocket)
    current_room = "general"
    manager.rooms[current_room][username] = websocket
    user_is_admin = is_admin(username)
    all_users = get_all_users()
    private_rooms = get_private_rooms()

    await websocket.send_text(json.dumps({
        "type": "auth_ok",
        "username": username,
        "rooms": ROOMS,
        "all_users": [u["username"] for u in all_users if not u["is_banned"]],
        "online_users": manager.online_users(),
        "is_admin": user_is_admin,
        "users_data": all_users,
        "private_rooms": private_rooms,
    }))

    for u in list(manager.users.keys()):
        if u != username:
            await manager.send_to(u, {
                "type": "user_online",
                "username": username,
                "online_users": manager.online_users(),
                "all_users": [u2["username"] for u2 in get_all_users() if not u2["is_banned"]],
            })

    history = load_room_messages(current_room)
    await websocket.send_text(json.dumps({"type": "history", "messages": history, "room": current_room}))

    await manager.broadcast_room(current_room, {
        "type": "system",
        "text": f"{username} joined #{current_room}",
        "users": manager.users_in_room(current_room),
        "room": current_room,
        "timestamp": _now(),
    })

    async def keepalive():
        while True:
            await asyncio.sleep(25)
            try: await websocket.send_text('{"type":"ping"}')
            except: break

    asyncio.create_task(keepalive())

    try:
        while True:
            data = json.loads(await websocket.receive_text())

            if data.get("type") == "ping":
                await websocket.send_text('{"type":"pong"}')
                continue

            elif data.get("type") == "typing":
                is_dm = data.get("to") is not None
                if is_dm:
                    await manager.send_to(data.get("to"), {"type": "typing", "username": username, "is_dm": True})
                else:
                    await manager.broadcast_room(current_room, {"type": "typing", "username": username, "room": current_room, "is_dm": False})

            elif data.get("type") == "switch_room":
                new_room = data.get("room")
                if new_room not in ROOMS and new_room not in [r["name"] for r in get_private_rooms()]:
                    continue
                manager.rooms[current_room].pop(username, None)
                await manager.broadcast_room(current_room, {
                    "type": "system", "text": f"{username} left #{current_room}",
                    "users": manager.users_in_room(current_room), "room": current_room, "timestamp": _now(),
                })
                current_room = new_room
                manager.ensure_room(current_room)
                manager.rooms[current_room][username] = websocket
                history = load_room_messages(current_room)
                polls = get_room_polls(current_room)
                await websocket.send_text(json.dumps({"type": "history", "messages": history, "room": current_room}))
                await websocket.send_text(json.dumps({"type": "polls_list", "polls": polls, "room": current_room}))
                await manager.broadcast_room(current_room, {
                    "type": "system", "text": f"{username} joined #{current_room}",
                    "users": manager.users_in_room(current_room), "room": current_room, "timestamp": _now(),
                })

            elif data.get("type") == "join_private_room":
                room_name = data.get("room")
                password = data.get("password", "")
                if verify_private_room(room_name, password):
                    manager.rooms[current_room].pop(username, None)
                    current_room = room_name
                    manager.ensure_room(current_room)
                    manager.rooms[current_room][username] = websocket
                    history = load_room_messages(current_room)
                    await websocket.send_text(json.dumps({"type": "join_private_ok", "room": room_name}))
                    await websocket.send_text(json.dumps({"type": "history", "messages": history, "room": current_room}))
                    await manager.broadcast_room(current_room, {
                        "type": "system", "text": f"{username} joined #{current_room}",
                        "users": manager.users_in_room(current_room), "room": current_room, "timestamp": _now(),
                    })
                else:
                    await websocket.send_text(json.dumps({"type": "join_private_fail", "text": "Wrong password!"}))

            elif data.get("type") == "create_private_room":
                room_name = data.get("room", "").strip()
                room_password = data.get("password", "").strip()
                if not room_name or not room_password:
                    continue
                if create_private_room(room_name, room_password, username):
                    manager.ensure_room(room_name)
                    private_rooms = get_private_rooms()
                    await manager.broadcast_all({
                        "type": "private_room_created",
                        "room": {"name": room_name, "creator": username},
                        "private_rooms": private_rooms,
                    })
                else:
                    await websocket.send_text(json.dumps({"type": "error", "text": "Room name already taken!"}))

            elif data.get("type") == "load_dm":
                other = data.get("with")
                messages = load_dm(username, other)
                await websocket.send_text(json.dumps({"type": "dm_history", "with": other, "messages": messages}))

            elif data.get("type") == "dm":
                receiver = data.get("to")
                text = data.get("text", "")
                reply_to = data.get("reply_to")
                reply_text = data.get("reply_text")
                reply_sender = data.get("reply_sender")
                ts = _now()
                msg_id = save_dm(username, receiver, text, ts, reply_to, reply_text, reply_sender)
                msg = {"type": "dm", "id": msg_id, "sender": username, "receiver": receiver,
                       "text": text, "timestamp": ts, "edited": False,
                       "reply_to": reply_to, "reply_text": reply_text, "reply_sender": reply_sender,
                       "reactions": {}}
                await manager.send_to(receiver, msg)
                await manager.send_to(username, msg)

            elif data.get("type") == "react":
                msg_id = data.get("id")
                emoji = data.get("emoji")
                msg_type = data.get("msg_type", "room")
                reactions = toggle_reaction(msg_id, username, emoji, msg_type)
                react_msg = {"type": "reaction_update", "id": msg_id, "reactions": reactions, "msg_type": msg_type}
                if msg_type == "room":
                    await manager.broadcast_room(current_room, react_msg)
                else:
                    other = data.get("other")
                    await manager.send_to(username, react_msg)
                    await manager.send_to(other, react_msg)

            elif data.get("type") == "create_poll":
                question = data.get("question", "").strip()
                options = data.get("options", [])
                if not question or len(options) < 2:
                    continue
                ts = _now()
                poll_id = create_poll(current_room, username, question, options, ts)
                poll = get_poll(poll_id)
                await manager.broadcast_room(current_room, {
                    "type": "new_poll",
                    "poll": poll,
                    "room": current_room,
                })

            elif data.get("type") == "vote_poll":
                poll_id = data.get("poll_id")
                option = data.get("option")
                votes = vote_poll(poll_id, username, option)
                if votes is not None:
                    await manager.broadcast_room(current_room, {
                        "type": "poll_update",
                        "poll_id": poll_id,
                        "votes": votes,
                    })

            elif data.get("type") == "edit_message":
                msg_id = data.get("id")
                new_text = data.get("text", "").strip()
                is_dm = data.get("is_dm", False)
                if not new_text: continue
                if is_dm:
                    other = data.get("other")
                    if edit_dm_message(msg_id, username, new_text):
                        msg = {"type": "message_edited", "id": msg_id, "text": new_text, "is_dm": True}
                        await manager.send_to(username, msg)
                        await manager.send_to(other, msg)
                else:
                    if edit_room_message(msg_id, username, new_text):
                        await manager.broadcast_room(current_room, {
                            "type": "message_edited", "id": msg_id, "text": new_text, "is_dm": False, "room": current_room
                        })

            elif data.get("type") == "delete_message":
                msg_id = data.get("id")
                is_dm = data.get("is_dm", False)
                force = data.get("force", False)
                if is_dm:
                    other = data.get("other")
                    if delete_dm_message(msg_id, username):
                        msg = {"type": "message_deleted", "id": msg_id, "is_dm": True}
                        await manager.send_to(username, msg)
                        await manager.send_to(other, msg)
                else:
                    if force and is_admin(username):
                        delete_room_message_admin(msg_id)
                        await manager.broadcast_room(current_room, {
                            "type": "message_deleted", "id": msg_id, "is_dm": False, "room": current_room
                        })
                    elif delete_room_message(msg_id, username):
                        await manager.broadcast_room(current_room, {
                            "type": "message_deleted", "id": msg_id, "is_dm": False, "room": current_room
                        })

            elif data.get("type") == "search":
                query = data.get("query", "")
                results = search_messages(current_room, query)
                await websocket.send_text(json.dumps({"type": "search_results", "results": results, "query": query}))

            elif data.get("type") == "admin_delete_user":
                if not is_admin(username): continue
                target = data.get("username")
                if target in ADMINS: continue
                if target in manager.users:
                    await manager.send_to(target, {"type": "force_logout", "text": "Your account has been deleted by an admin."})
                    manager.disconnect(target)
                conn = sqlite3.connect(DB_PATH)
                conn.execute("DELETE FROM users WHERE username = ?", (target,))
                conn.commit(); conn.close()
                await manager.broadcast_all({
                    "type": "system_admin",
                    "text": f"🗑️ {target}'s account was deleted by admin.",
                    "users_data": get_all_users(),
                })

            elif data.get("type") == "admin_ban":
                if not is_admin(username): continue
                target = data.get("username")
                if target in ADMINS: continue
                ban_user(target)
                if target in manager.users:
                    await manager.send_to(target, {"type": "force_logout", "text": "You have been banned by an admin."})
                    manager.disconnect(target)
                await manager.broadcast_all({"type": "system_admin", "text": f"🚫 {target} has been banned.", "users_data": get_all_users()})

            elif data.get("type") == "admin_unban":
                if not is_admin(username): continue
                target = data.get("username")
                unban_user(target)
                await manager.broadcast_all({"type": "system_admin", "text": f"✅ {target} has been unbanned.", "users_data": get_all_users()})

            elif data.get("type") == "admin_make_admin":
                if not is_admin(username): continue
                target = data.get("username")
                make_admin(target)
                await manager.send_to(target, {"type": "promoted", "text": "You have been made an admin! 👑"})
                await manager.broadcast_all({"type": "system_admin", "text": f"👑 {target} has been made an admin.", "users_data": get_all_users()})

            elif data.get("type") == "admin_remove_admin":
                if not is_admin(username): continue
                target = data.get("username")
                if target in ADMINS: continue
                remove_admin(target)
                await manager.broadcast_all({"type": "system_admin", "text": f"👤 {target} admin role removed.", "users_data": get_all_users()})

            elif data.get("type") == "admin_kick":
                if not is_admin(username): continue
                target = data.get("username")
                if target in manager.users:
                    await manager.send_to(target, {"type": "force_logout", "text": "You have been kicked by an admin."})
                    manager.disconnect(target)
                await manager.broadcast_all({"type": "system_admin", "text": f"👢 {target} was kicked.", "users_data": get_all_users()})

            elif data.get("type") == "admin_get_users":
                if not is_admin(username): continue
                await websocket.send_text(json.dumps({
                    "type": "admin_users_list",
                    "users_data": get_all_users(),
                    "online_users": manager.online_users(),
                }))

            elif data.get("type") == "call_offer":
                target = data.get("to")
                await manager.send_to(target, {"type": "call_offer", "from": username, "offer": data.get("offer"), "callType": data.get("callType", "video")})

            elif data.get("type") == "call_answer":
                target = data.get("to")
                await manager.send_to(target, {"type": "call_answer", "from": username, "answer": data.get("answer")})

            elif data.get("type") == "call_ice":
                target = data.get("to")
                await manager.send_to(target, {"type": "call_ice", "from": username, "candidate": data.get("candidate")})

            elif data.get("type") == "call_reject":
                target = data.get("to")
                await manager.send_to(target, {"type": "call_reject", "from": username})

            elif data.get("type") == "call_end":
                target = data.get("to")
                await manager.send_to(target, {"type": "call_end", "from": username})

            elif data.get("text"):
                text = data["text"]
                reply_to = data.get("reply_to")
                reply_text = data.get("reply_text")
                reply_sender = data.get("reply_sender")
                ts = _now()
                msg_id = save_room_message(current_room, username, text, ts, reply_to, reply_text, reply_sender)
                await manager.broadcast_room(current_room, {
                    "type": "message", "id": msg_id, "sender": username,
                    "text": text, "timestamp": ts, "room": current_room, "edited": False,
                    "reply_to": reply_to, "reply_text": reply_text, "reply_sender": reply_sender,
                    "reactions": {},
                })

    except WebSocketDisconnect:
        manager.disconnect(username)
        await manager.broadcast_room(current_room, {
            "type": "system", "text": f"{username} left the chat",
            "users": manager.users_in_room(current_room), "room": current_room, "timestamp": _now(),
        })
        for u in list(manager.users.keys()):
            await manager.send_to(u, {
                "type": "user_offline", "username": username,
                "online_users": manager.online_users(),
                "all_users": [u2["username"] for u2 in get_all_users() if not u2["is_banned"]],
            })

def _now():
    return datetime.datetime.now().strftime("%H:%M")