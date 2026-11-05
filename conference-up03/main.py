"""Application factory with lifespan-based storage initialization."""

import logging
import time
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.trustedhost import TrustedHostMiddleware

from config import ROOT, Settings, settings_from_env
from database import connection, init_db
from routers import attendance, auth, badges, participants, sections, stats

logger = logging.getLogger("conference")


def create_app(settings: Settings | None = None):
    cfg = settings or settings_from_env()

    @asynccontextmanager
    async def lifespan(app):
        init_db(cfg)
        logger.info("startup database_ready=true demo=%s", cfg.demo)
        yield
        logger.info("shutdown")

    app = FastAPI(
        title="Конференция — управление мероприятием",
        version="3.0.0",
        lifespan=lifespan,
        debug=False,
        docs_url=None if cfg.production else "/docs",
        redoc_url=None,
    )
    app.state.settings = cfg
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=list(cfg.allowed_hosts))

    @app.middleware("http")
    async def diagnostics(request: Request, call_next):
        if request.url.path == "/api/import":
            length = request.headers.get("content-length", "0")
            if not length.isdigit() or int(length) > 10 * 1024 * 1024:
                return JSONResponse(status_code=413, content={"detail": "Файл превышает 10 МБ"})
            chunks, size = [], 0
            async for chunk in request.stream():
                size += len(chunk)
                if size > 10 * 1024 * 1024:
                    return JSONResponse(status_code=413, content={"detail": "Файл превышает 10 МБ"})
                chunks.append(chunk)
            request._body = b"".join(chunks)
        start = time.perf_counter()
        request_id = uuid.uuid4().hex[:12]
        response = await call_next(request)
        response.headers.update(
            {
                "X-Request-ID": request_id,
                "X-Content-Type-Options": "nosniff",
                "X-Frame-Options": "DENY",
                "Referrer-Policy": "same-origin",
            }
        )
        if not request.url.path.startswith(("/docs", "/openapi")):
            response.headers["Content-Security-Policy"] = (
                "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; object-src 'none'; frame-ancestors 'none'; base-uri 'self'; form-action 'self'"
            )
        if request.url.path.startswith("/api"):
            response.headers["Cache-Control"] = "no-store"
        logger.info(
            "request=%s method=%s path=%s status=%s duration_ms=%.2f",
            request_id,
            request.method,
            request.url.path,
            response.status_code,
            (time.perf_counter() - start) * 1000,
        )
        return response

    @app.exception_handler(RequestValidationError)
    async def invalid(request, exc):
        fields = [".".join(str(v) for v in e["loc"][1:]) for e in exc.errors()]
        return JSONResponse(
            status_code=422,
            content={"detail": "Проверьте заполнение полей: " + ", ".join(dict.fromkeys(fields))},
        )

    @app.exception_handler(Exception)
    async def unexpected(request, exc):
        logger.error("unhandled exception type=%s path=%s", type(exc).__name__, request.url.path)
        return JSONResponse(
            status_code=500, content={"detail": "Ошибка сервера. Обратитесь к администратору"}
        )

    @app.get("/api/health", tags=["Состояние"])
    def health():
        with connection(cfg.db_path) as conn:
            conn.execute("SELECT 1 FROM users LIMIT 1")
        return {"status": "ok", "version": "3.0.0", "demo": cfg.demo}

    for router in [
        auth.router,
        participants.router,
        sections.router,
        attendance.router,
        badges.router,
        stats.router,
    ]:
        app.include_router(router)

    @app.get("/{legacy}.html", include_in_schema=False)
    def legacy_page(legacy: str):
        allowed = {"participants", "sections", "attendance", "badges", "reports"}
        return RedirectResponse("/#" + (legacy if legacy in allowed else "dashboard"))

    app.mount("/", StaticFiles(directory=ROOT / "frontend", html=True), name="frontend")
    return app


app = create_app()
if __name__ == "__main__":
    import os
    from logging.handlers import RotatingFileHandler

    import uvicorn

    (ROOT / "logs").mkdir(exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        handlers=[
            logging.StreamHandler(),
            RotatingFileHandler(
                ROOT / "logs" / "app.log", maxBytes=2_000_000, backupCount=3, encoding="utf-8"
            ),
        ],
    )
    uvicorn.run(
        app,
        host=os.getenv("APP_HOST", "127.0.0.1"),
        port=int(os.getenv("APP_PORT", "8000")),
        access_log=False,
    )
