from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import uvicorn

from database import init_db
from routers import participants, sections, attendance, badges, stats

FRONTEND_DIR = Path("frontend")

app = FastAPI(title="Система управления конференцией", version="2.0.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Подключаем все маршруты
app.include_router(participants.router)
app.include_router(sections.router)
app.include_router(attendance.router)
app.include_router(badges.router)
app.include_router(stats.router)

# Статические файлы фронтенда
if FRONTEND_DIR.exists():
    app.mount("/", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="frontend")
    print(f"✓ Фронтенд загружен из: {FRONTEND_DIR.absolute()}")
else:
    print(f"⚠ Папка frontend не найдена: {FRONTEND_DIR.absolute()}")


if __name__ == "__main__":
    init_db()

    print("=" * 50)
    print("  Сервер конференции (SQLite)")
    print("=" * 50)
    print("  Адрес:  http://localhost:8080")
    print("  API:    /api/*")
    print("  Ctrl+C — остановить")
    print("=" * 50)

    uvicorn.run(app, host="0.0.0.0", port=8080, log_level="info")
