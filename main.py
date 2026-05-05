from fastapi import FastAPI, WebSocket, WebSocketDisconnect, UploadFile, File
from fastapi.responses import HTMLResponse, FileResponse
from typing import Dict
import json, datetime, sqlite3, bcrypt, os, uuid, random, smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

app = FastAPI()

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

SMTP_EMAIL = os.environ.get("SMTP_EMAIL", "iswordhakal00@gmail.com")
SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD", "rniqzdipzssbifsh")

# Store pending verifications: {email: {code, username, password, expires}}
pending_verifications: Dict[str, dict] = {}

def init_db():
    conn = sqlite3.connect("chat.db")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id       INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT,
            email    TEXT UNIQUE
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS room_messages (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            room      TEXT,
            sender    TEXT,
            text      TEXT,
            timestamp TEXT,
            edited    INTEGER DEFAULT 0
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS dm_messages (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            sender    TEXT,
            receiver  TEXT,
            text      TEXT,
            timestamp TEXT,
            edited    INTEGER DEFAULT 0
        )
    """)
    try:
        conn.execute("ALTER TABLE room_messages ADD COLUMN edited INTEGER DEFAULT 0")
    except:
        pass
    try:
        conn.execute("ALTER TABLE dm_messages ADD COLUMN edited INTEGER DEFAULT 0")
    except:
        pass
    try:
        conn.execute("ALTER TABLE users ADD COLUMN email TEXT")
    except:
        pass
    conn.commit()
    conn.close()

def register_user(username, password, email=""):
    try:
        hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
        conn = sqlite3.connect("chat.db")
        conn.execute("INSERT INTO users (username, password, email) VALUES (?, ?, ?)", (username, hashed, email))
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        return False

def login_user(username, password):
    conn = sqlite3.connect("chat.db")
    row = conn.execute("SELECT password FROM users WHERE username = ?", (username,)).fetchone()
    conn.close()
    if not row:
        return False
    return bcrypt.checkpw(password.encode(), row[0].encode())

def get_all_users():
    conn = sqlite3.connect("chat.db")
    rows = conn.execute("SELECT username FROM users").fetchall()
    conn.close()
    return [r[0] for r in rows]

def save_room_message(room, sender, text, timestamp):
    conn = sqlite3.connect("chat.db")
    cursor = conn.execute(
        "INSERT INTO room_messages (room, sender, text, timestamp) VALUES (?, ?, ?, ?)",
        (room, sender, text, timestamp)
    )
    msg_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return msg_id

def load_room_messages(room):
    conn = sqlite3.connect("chat.db")
    rows = conn.execute(
        "SELECT id, sender, text, timestamp, edited FROM room_messages WHERE room = ? ORDER BY id DESC LIMIT 50",
        (room,)
    ).fetchall()
    conn.close()
    return [{"id": r[0], "sender": r[1], "text": r[2], "timestamp": r[3], "edited": bool(r[4])} for r in reversed(rows)]

def save_dm(sender, receiver, text, timestamp):
    conn = sqlite3.connect("chat.db")
    cursor = conn.execute(
        "INSERT INTO dm_messages (sender, receiver, text, timestamp) VALUES (?, ?, ?, ?)",
        (sender, receiver, text, timestamp)
    )
    msg_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return msg_id

def load_dm(user1, user2):
    conn = sqlite3.connect("chat.db")
    rows = conn.execute("""
        SELECT id, sender, receiver, text, timestamp, edited FROM dm_messages
        WHERE (sender=? AND receiver=?) OR (sender=? AND receiver=?)
        ORDER BY id DESC LIMIT 50
    """, (user1, user2, user2, user1)).fetchall()
    conn.close()
    return [{"id": r[0], "sender": r[1], "receiver": r[2], "text": r[3], "timestamp": r[4], "edited": bool(r[5])} for r in reversed(rows)]

def edit_room_message(msg_id, username, new_text):
    conn = sqlite3.connect("chat.db")
    row = conn.execute("SELECT sender FROM room_messages WHERE id=?", (msg_id,)).fetchone()
    if not row or row[0] != username:
        conn.close()
        return False
    conn.execute("UPDATE room_messages SET text=?, edited=1 WHERE id=?", (new_text, msg_id))
    conn.commit()
    conn.close()
    return True

def delete_room_message(msg_id, username):
    conn = sqlite3.connect("chat.db")
    row = conn.execute("SELECT sender FROM room_messages WHERE id=?", (msg_id,)).fetchone()
    if not row or row[0] != username:
        conn.close()
        return False
    conn.execute("DELETE FROM room_messages WHERE id=?", (msg_id,))
    conn.commit()
    conn.close()
    return True

def edit_dm_message(msg_id, username, new_text):
    conn = sqlite3.connect("chat.db")
    row = conn.execute("SELECT sender FROM dm_messages WHERE id=?", (msg_id,)).fetchone()
    if not row or row[0] != username:
        conn.close()
        return False
    conn.execute("UPDATE dm_messages SET text=?, edited=1 WHERE id=?", (new_text, msg_id))
    conn.commit()
    conn.close()
    return True

def delete_dm_message(msg_id, username):
    conn = sqlite3.connect("chat.db")
    row = conn.execute("SELECT sender, receiver FROM dm_messages WHERE id=?", (msg_id,)).fetchone()
    if not row or row[0] != username:
        conn.close()
        return False
    conn.execute("DELETE FROM dm_messages WHERE id=?", (msg_id,))
    conn.commit()
    conn.close()
    return True

def search_messages(room, query):
    conn = sqlite3.connect("chat.db")
    rows = conn.execute(
        "SELECT id, sender, text, timestamp FROM room_messages WHERE room=? AND text LIKE ? ORDER BY id DESC LIMIT 20",
        (room, f"%{query}%")
    ).fetchall()
    conn.close()
    return [{"id": r[0], "sender": r[1], "text": r[2], "timestamp": r[3]} for r in reversed(rows)]

def send_verification_email(to_email, username, code):
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = "FastChat — Verify Your Email"
        msg["From"] = SMTP_EMAIL
        msg["To"] = to_email

        html = f"""
        <html>
        <body style="margin:0;padding:0;background:#0f1117;font-family:'Inter',sans-serif;">
          <div style="max-width:480px;margin:40px auto;background:#1a1d2e;border-radius:16px;border:1px solid #252840;overflow:hidden;">
            <div style="background:linear-gradient(135deg,#6c63ff,#ff4ecd);padding:32px;text-align:center;">
              <div style="font-size:2.5rem;">⚡</div>
              <h1 style="color:#fff;font-size:1.6rem;margin:8px 0 0;">FastChat</h1>
            </div>
            <div style="padding:32px;">
              <h2 style="color:#ffffff;margin:0 0 8px;">Hi {username}! 👋</h2>
              <p style="color:#7b82a0;margin:0 0 24px;">Thanks for joining FastChat! Enter this code to verify your email:</p>
              <div style="background:#0f1117;border-radius:12px;padding:24px;text-align:center;border:1px solid #252840;margin-bottom:24px;">
                <div style="letter-spacing:12px;font-size:2.2rem;font-weight:800;color:#6c63ff;">{code}</div>
              </div>
              <p style="color:#454a65;font-size:.82rem;margin:0;">⏱ This code expires in <strong style="color:#f0b232;">10 minutes</strong>.</p>
              <p style="color:#454a65;font-size:.82rem;margin:8px 0 0;">If you didn't create a FastChat account, ignore this email.</p>
            </div>
          </div>
        </body>
        </html>
        """

        msg.attach(MIMEText(html, "html"))

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(SMTP_EMAIL, SMTP_PASSWORD)
            server.sendmail(SMTP_EMAIL, to_email, msg.as_string())
        return True
    except Exception as e:
        print(f"Email error: {e}")
        return False

init_db()

ROOMS = ["general", "random", "tech"]

class Manager:
    def __init__(self):
        self.users: Dict[str, WebSocket] = {}
        self.rooms: Dict[str, Dict[str, WebSocket]] = {r: {} for r in ROOMS}

    async def connect(self, username, websocket):
        self.users[username] = websocket

    def disconnect(self, username):
        self.users.pop(username, None)
        for room in self.rooms:
            self.rooms[room].pop(username, None)

    async def send_to(self, username, message):
        ws = self.users.get(username)
        if ws:
            try:
                await ws.send_text(json.dumps(message))
            except:
                pass

    async def broadcast_room(self, room, message):
        dead = []
        for username, ws in self.rooms[room].items():
            try:
                await ws.send_text(json.dumps(message))
            except:
                dead.append(username)
        for u in dead:
            self.rooms[room].pop(u, None)

    def online_users(self):
        return list(self.users.keys())

    def users_in_room(self, room):
        return list(self.rooms[room].keys())

manager = Manager()

@app.get("/", response_class=HTMLResponse)
async def get():
    with open("index.html", encoding="utf-8") as f:
        return f.read()

@app.get("/check-username/{username}")
async def check_username(username: str):
    conn = sqlite3.connect("chat.db")
    row = conn.execute("SELECT id FROM users WHERE username = ?", (username,)).fetchone()
    conn.close()
    return {"available": row is None}

@app.post("/send-verification")
async def send_verification(data: dict):
    username = data.get("username", "").strip()
    email = data.get("email", "").strip()
    password = data.get("password", "").strip()

    if not username or not email or not password:
        return {"success": False, "error": "Missing fields"}

    # Check username not taken
    conn = sqlite3.connect("chat.db")
    row = conn.execute("SELECT id FROM users WHERE username = ?", (username,)).fetchone()
    conn.close()
    if row:
        return {"success": False, "error": "Username already taken"}

    # Generate 6-digit code
    code = str(random.randint(100000, 999999))
    expires = datetime.datetime.now() + datetime.timedelta(minutes=10)

    # Store pending
    pending_verifications[email] = {
        "code": code,
        "username": username,
        "password": password,
        "expires": expires
    }

    # Send email
    sent = send_verification_email(email, username, code)
    if not sent:
        return {"success": False, "error": "Failed to send email. Check your email address."}

    return {"success": True}

@app.post("/verify-code")
async def verify_code(data: dict):
    email = data.get("email", "").strip()
    code = data.get("code", "").strip()

    pending = pending_verifications.get(email)
    if not pending:
        return {"success": False, "error": "No verification pending. Please register again."}

    if datetime.datetime.now() > pending["expires"]:
        del pending_verifications[email]
        return {"success": False, "error": "Code expired. Please register again."}

    if pending["code"] != code:
        return {"success": False, "error": "Wrong code. Try again."}

    # Create account
    success = register_user(pending["username"], pending["password"], email)
    del pending_verifications[email]

    if not success:
        return {"success": False, "error": "Username already taken."}

    return {"success": True, "username": pending["username"]}

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

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()

    data = json.loads(await websocket.receive_text())
    action   = data.get("action")
    username = data.get("username", "").strip()
    password = data.get("password", "").strip()

    if not username or not password:
        await websocket.send_text(json.dumps({"type": "auth_fail", "text": "Username and password required."}))
        await websocket.close()
        return

    if action == "login":
        if not login_user(username, password):
            await websocket.send_text(json.dumps({"type": "auth_fail", "text": "Wrong username or password."}))
            await websocket.close()
            return
    else:
        await websocket.send_text(json.dumps({"type": "auth_fail", "text": "Please use the register form."}))
        await websocket.close()
        return

    await manager.connect(username, websocket)
    current_room = "general"
    manager.rooms[current_room][username] = websocket

    await websocket.send_text(json.dumps({
        "type": "auth_ok",
        "username": username,
        "rooms": ROOMS,
        "all_users": get_all_users(),
        "online_users": manager.online_users(),
    }))

    for u in list(manager.users.keys()):
        if u != username:
            await manager.send_to(u, {
                "type": "user_online",
                "username": username,
                "online_users": manager.online_users(),
                "all_users": get_all_users(),
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

    try:
        while True:
            data = json.loads(await websocket.receive_text())

            if data.get("type") == "typing":
                is_dm = data.get("to") is not None
                if is_dm:
                    await manager.send_to(data.get("to"), {"type": "typing", "username": username, "is_dm": True})
                else:
                    await manager.broadcast_room(current_room, {"type": "typing", "username": username, "room": current_room, "is_dm": False})

            elif data.get("type") == "switch_room":
                new_room = data.get("room")
                if new_room not in ROOMS:
                    continue
                manager.rooms[current_room].pop(username, None)
                await manager.broadcast_room(current_room, {
                    "type": "system", "text": f"{username} left #{current_room}",
                    "users": manager.users_in_room(current_room), "room": current_room, "timestamp": _now(),
                })
                current_room = new_room
                manager.rooms[current_room][username] = websocket
                history = load_room_messages(current_room)
                await websocket.send_text(json.dumps({"type": "history", "messages": history, "room": current_room}))
                await manager.broadcast_room(current_room, {
                    "type": "system", "text": f"{username} joined #{current_room}",
                    "users": manager.users_in_room(current_room), "room": current_room, "timestamp": _now(),
                })

            elif data.get("type") == "load_dm":
                other = data.get("with")
                messages = load_dm(username, other)
                await websocket.send_text(json.dumps({"type": "dm_history", "with": other, "messages": messages}))

            elif data.get("type") == "dm":
                receiver = data.get("to")
                text = data.get("text", "")
                ts = _now()
                msg_id = save_dm(username, receiver, text, ts)
                msg = {"type": "dm", "id": msg_id, "sender": username, "receiver": receiver, "text": text, "timestamp": ts, "edited": False}
                await manager.send_to(receiver, msg)
                await manager.send_to(username, msg)

            elif data.get("type") == "edit_message":
                msg_id = data.get("id")
                new_text = data.get("text", "").strip()
                is_dm = data.get("is_dm", False)
                if not new_text:
                    continue
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
                if is_dm:
                    other = data.get("other")
                    if delete_dm_message(msg_id, username):
                        msg = {"type": "message_deleted", "id": msg_id, "is_dm": True}
                        await manager.send_to(username, msg)
                        await manager.send_to(other, msg)
                else:
                    if delete_room_message(msg_id, username):
                        await manager.broadcast_room(current_room, {
                            "type": "message_deleted", "id": msg_id, "is_dm": False, "room": current_room
                        })

            elif data.get("type") == "search":
                query = data.get("query", "")
                results = search_messages(current_room, query)
                await websocket.send_text(json.dumps({"type": "search_results", "results": results, "query": query}))

            elif data.get("text"):
                text = data["text"]
                ts = _now()
                msg_id = save_room_message(current_room, username, text, ts)
                await manager.broadcast_room(current_room, {
                    "type": "message", "id": msg_id, "sender": username,
                    "text": text, "timestamp": ts, "room": current_room, "edited": False,
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
                "online_users": manager.online_users(), "all_users": get_all_users(),
            })

def _now():
    return datetime.datetime.now().strftime("%H:%M")