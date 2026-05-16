# pyrefly: ignore [missing-import]
from fastapi import FastAPI
# pyrefly: ignore [missing-import]
from fastapi.responses import HTMLResponse
# pyrefly: ignore [missing-import]
from fastapi.staticfiles import StaticFiles
from app.database.session import init_db
from app.api.routes.endpoints import router as http_router
from app.api.websockets.endpoints import router as ws_router

app = FastAPI()

app.mount("/css", StaticFiles(directory="frontend/css"), name="css")
app.mount("/js", StaticFiles(directory="frontend/js"), name="js")

# Initialize Database
init_db()

# Include Routers
app.include_router(http_router)
app.include_router(ws_router)

@app.get("/", response_class=HTMLResponse)
async def get():
    with open("frontend/index.html", encoding="utf-8") as f:
        return f.read()
