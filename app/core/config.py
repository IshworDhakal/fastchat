import os

DATA_DIR = os.environ.get("RAILWAY_VOLUME_MOUNT_PATH", ".")
DB_PATH = os.path.join(DATA_DIR, "chat.db")
UPLOAD_DIR = os.path.join(DATA_DIR, "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

ADMINS = ["Ishwor123"]
ROOMS = ["general", "random", "tech"]
