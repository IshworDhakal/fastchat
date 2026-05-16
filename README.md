# GuffGaff

GuffGaff is a real-time chat application built with a FastAPI backend and a vanilla HTML/CSS/JS frontend. It supports modern messaging features including real-time communication via WebSockets, multimedia sharing, private rooms, and peer-to-peer audio/video calling.

## Features

- **Real-Time Messaging**: Built on FastAPI WebSockets for instant message delivery.
- **Channels & Private Rooms**: Create public channels or secure private rooms with passwords.
- **Direct Messaging**: One-on-one private conversations.
- **Audio & Video Calling**: Peer-to-peer WebRTC based calling for seamless communication.
- **Rich Media**: Support for image uploads, previews, and emoji reactions.
- **Admin Panel**: Comprehensive moderation tools including kick, ban, unban, promote, demote, and delete users.
- **Polls**: Create interactive polls within rooms.
- **Message Options**: Search, pin messages, reply to messages, and export chat history.
- **Authentication**: Secure user registration and login with password strength validation.

## Tech Stack

- **Backend**: Python 3, FastAPI, WebSockets
- **Database**: SQLite (`chat.db`)
- **Frontend**: Vanilla HTML5, CSS3, JavaScript (ES6+)

## Project Structure

```
guffgaff/
├── app/
│   ├── api/
│   │   ├── routes/
│   │   │   └── endpoints.py      # HTTP routes (auth, uploads, etc.)
│   │   └── websockets/
│   │       ├── endpoints.py      # WebSocket endpoints for real-time chat
│   │       └── manager.py        # Connection manager
│   ├── core/
│   │   └── config.py             # Application configuration
│   ├── database/
│   │   └── session.py            # SQLite database initialization and sessions
│   ├── services/
│   │   ├── chat_service.py       # Chat business logic
│   │   └── user_service.py       # User management and authentication logic
│   └── main.py                   # FastAPI application entry point
├── frontend/
│   ├── css/
│   │   └── main.css              # Styling
│   ├── js/
│   │   └── app.js                # Frontend logic (WebSockets, WebRTC, UI state)
│   └── index.html                # Main application interface
├── uploads/                      # Directory for user-uploaded images
└── chat.db                       # SQLite Database
```

## Getting Started

### Prerequisites

- Python 3.8+
- pip (Python package installer)

### Installation

1. **Clone the repository (or navigate to the directory):**
   ```bash
   cd /path/to/guffgaff
   ```

2. **Create a virtual environment (recommended):**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use: venv\Scripts\activate
   ```

3. **Install dependencies:**
   *(Ensure you have `fastapi`, `uvicorn`, `websockets`, and any other required libraries installed)*
   ```bash
   pip install fastapi uvicorn websockets python-multipart sqlalchemy
   ```

4. **Run the application:**
   ```bash
   uvicorn app.main:app --reload
   ```

5. **Access the application:**
   Open your web browser and navigate to `http://localhost:8000`.

## Usage

- **Register/Login**: Create an account on the landing page to start chatting.
- **Create Rooms**: Click the `+` icon next to Channels or Private Rooms to create new spaces.
- **Calls**: Click the video or audio icon on a user's profile to initiate a WebRTC call.
- **Admin**: If you have admin privileges, an Admin Panel icon will appear in your user profile section on the bottom left.
