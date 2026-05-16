import json
import asyncio
import datetime
# pyrefly: ignore [missing-import]
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.api.websockets.manager import manager
from app.core.config import ROOMS, ADMINS
from app.services import user_service, chat_service

router = APIRouter()

def _now():
    return datetime.datetime.now().isoformat(timespec="seconds")

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()

    data_text = await websocket.receive_text()
    try:
        data = json.loads(data_text)
    except json.JSONDecodeError:
        await websocket.close()
        return

    action   = data.get("action")
    username = data.get("username", "").strip()
    password = data.get("password", "").strip()

    if not username or not password:
        await websocket.send_text(json.dumps({"type": "auth_fail", "text": "Username and password required."}))
        await websocket.close()
        return

    if action == "register":
        if not user_service.register_user(username, password):
            await websocket.send_text(json.dumps({"type": "auth_fail", "text": "Username already taken."}))
            await websocket.close()
            return
    elif action == "login":
        result = user_service.login_user(username, password)
        if result == "banned":
            await websocket.send_text(json.dumps({"type": "auth_fail", "text": "You have been banned from GufGaff."}))
            await websocket.close()
            return
        if not result:
            await websocket.send_text(json.dumps({"type": "auth_fail", "text": "Wrong username or password."}))
            await websocket.close()
            return

    await manager.connect(username, websocket)
    current_room = "general"
    manager.rooms[current_room][username] = websocket
    user_is_admin = user_service.is_admin(username)
    all_users = user_service.get_all_users()
    private_rooms = chat_service.get_private_rooms()

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
                "all_users": [u2["username"] for u2 in user_service.get_all_users() if not u2["is_banned"]],
            })

    history = chat_service.load_room_messages(current_room)
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
            try:
                await websocket.send_text('{"type":"ping"}')
            except Exception:
                break

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
                if new_room not in ROOMS and new_room not in [r["name"] for r in chat_service.get_private_rooms()]:
                    continue
                manager.rooms[current_room].pop(username, None)
                await manager.broadcast_room(current_room, {
                    "type": "system", "text": f"{username} left #{current_room}",
                    "users": manager.users_in_room(current_room), "room": current_room, "timestamp": _now(),
                })
                current_room = new_room
                manager.ensure_room(current_room)
                manager.rooms[current_room][username] = websocket
                history = chat_service.load_room_messages(current_room)
                polls = chat_service.get_room_polls(current_room)
                await websocket.send_text(json.dumps({"type": "history", "messages": history, "room": current_room}))
                await websocket.send_text(json.dumps({"type": "polls_list", "polls": polls, "room": current_room}))
                await manager.broadcast_room(current_room, {
                    "type": "system", "text": f"{username} joined #{current_room}",
                    "users": manager.users_in_room(current_room), "room": current_room, "timestamp": _now(),
                })

            elif data.get("type") == "join_private_room":
                room_name = data.get("room")
                password = data.get("password", "")
                if chat_service.verify_private_room(room_name, password):
                    manager.rooms[current_room].pop(username, None)
                    current_room = room_name
                    manager.ensure_room(current_room)
                    manager.rooms[current_room][username] = websocket
                    history = chat_service.load_room_messages(current_room)
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
                if chat_service.create_private_room(room_name, room_password, username):
                    manager.ensure_room(room_name)
                    private_rooms = chat_service.get_private_rooms()
                    await manager.broadcast_all({
                        "type": "private_room_created",
                        "room": {"name": room_name, "creator": username},
                        "private_rooms": private_rooms,
                    })
                else:
                    await websocket.send_text(json.dumps({"type": "error", "text": "Room name already taken!"}))

            elif data.get("type") == "load_dm":
                other = data.get("with")
                messages = chat_service.load_dm(username, other)
                await websocket.send_text(json.dumps({"type": "dm_history", "with": other, "messages": messages}))

            elif data.get("type") == "dm":
                receiver = data.get("to")
                text = data.get("text", "")
                reply_to = data.get("reply_to")
                reply_text = data.get("reply_text")
                reply_sender = data.get("reply_sender")
                ts = _now()
                msg_id = chat_service.save_dm(username, receiver, text, ts, reply_to, reply_text, reply_sender)
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
                reactions = chat_service.toggle_reaction(msg_id, username, emoji, msg_type)
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
                poll_id = chat_service.create_poll(current_room, username, question, options, ts)
                poll = chat_service.get_poll(poll_id)
                await manager.broadcast_room(current_room, {
                    "type": "new_poll",
                    "poll": poll,
                    "room": current_room,
                })

            elif data.get("type") == "vote_poll":
                poll_id = data.get("poll_id")
                option = data.get("option")
                votes = chat_service.vote_poll(poll_id, username, option)
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
                    if chat_service.edit_dm_message(msg_id, username, new_text):
                        msg = {"type": "message_edited", "id": msg_id, "text": new_text, "is_dm": True}
                        await manager.send_to(username, msg)
                        await manager.send_to(other, msg)
                else:
                    if chat_service.edit_room_message(msg_id, username, new_text):
                        await manager.broadcast_room(current_room, {
                            "type": "message_edited", "id": msg_id, "text": new_text, "is_dm": False, "room": current_room
                        })

            elif data.get("type") == "delete_message":
                msg_id = data.get("id")
                is_dm = data.get("is_dm", False)
                force = data.get("force", False)
                if is_dm:
                    other = data.get("other")
                    if chat_service.delete_dm_message(msg_id, username):
                        msg = {"type": "message_deleted", "id": msg_id, "is_dm": True}
                        await manager.send_to(username, msg)
                        await manager.send_to(other, msg)
                else:
                    if force and user_service.is_admin(username):
                        chat_service.delete_room_message_admin(msg_id)
                        await manager.broadcast_room(current_room, {
                            "type": "message_deleted", "id": msg_id, "is_dm": False, "room": current_room
                        })
                    elif chat_service.delete_room_message(msg_id, username):
                        await manager.broadcast_room(current_room, {
                            "type": "message_deleted", "id": msg_id, "is_dm": False, "room": current_room
                        })

            elif data.get("type") == "search":
                query = data.get("query", "")
                results = chat_service.search_messages(current_room, query)
                await websocket.send_text(json.dumps({"type": "search_results", "results": results, "query": query}))

            elif data.get("type") == "admin_delete_user":
                if not user_service.is_admin(username): continue
                target = data.get("username")
                if target in ADMINS: continue
                if target in manager.users:
                    await manager.send_to(target, {"type": "force_logout", "text": "Your account has been deleted by an admin."})
                    manager.disconnect(target)
                user_service.delete_user(target)
                await manager.broadcast_all({
                    "type": "system_admin",
                    "text": f"🗑️ {target}'s account was deleted by admin.",
                    "users_data": user_service.get_all_users(),
                })

            elif data.get("type") == "admin_ban":
                if not user_service.is_admin(username): continue
                target = data.get("username")
                if target in ADMINS: continue
                user_service.ban_user(target)
                if target in manager.users:
                    await manager.send_to(target, {"type": "force_logout", "text": "You have been banned by an admin."})
                    manager.disconnect(target)
                await manager.broadcast_all({"type": "system_admin", "text": f"🚫 {target} has been banned.", "users_data": user_service.get_all_users()})

            elif data.get("type") == "admin_unban":
                if not user_service.is_admin(username): continue
                target = data.get("username")
                user_service.unban_user(target)
                await manager.broadcast_all({"type": "system_admin", "text": f"✅ {target} has been unbanned.", "users_data": user_service.get_all_users()})

            elif data.get("type") == "admin_make_admin":
                if not user_service.is_admin(username): continue
                target = data.get("username")
                user_service.make_admin(target)
                await manager.send_to(target, {"type": "promoted", "text": "You have been made an admin! 👑"})
                await manager.broadcast_all({"type": "system_admin", "text": f"👑 {target} has been made an admin.", "users_data": user_service.get_all_users()})

            elif data.get("type") == "admin_remove_admin":
                if not user_service.is_admin(username): continue
                target = data.get("username")
                if target in ADMINS: continue
                user_service.remove_admin(target)
                await manager.broadcast_all({"type": "system_admin", "text": f"👤 {target} admin role removed.", "users_data": user_service.get_all_users()})

            elif data.get("type") == "admin_kick":
                if not user_service.is_admin(username): continue
                target = data.get("username")
                if target in manager.users:
                    await manager.send_to(target, {"type": "force_logout", "text": "You have been kicked by an admin."})
                    manager.disconnect(target)
                await manager.broadcast_all({"type": "system_admin", "text": f"👢 {target} was kicked.", "users_data": user_service.get_all_users()})

            elif data.get("type") == "admin_get_users":
                if not user_service.is_admin(username): continue
                await websocket.send_text(json.dumps({
                    "type": "admin_users_list",
                    "users_data": user_service.get_all_users(),
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
                msg_id = chat_service.save_room_message(current_room, username, text, ts, reply_to, reply_text, reply_sender)
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
                "all_users": [u2["username"] for u2 in user_service.get_all_users() if not u2["is_banned"]],
            })
