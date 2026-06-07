import logging
from contextlib import asynccontextmanager

from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse

from .config import settings
from .database import init_db
from .routers import channels, transactions, users, webhooks, admin
from .routers.auth import router as auth_router
from .orders.router import router as orders_router
from .payments.router import router as payments_router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(title="Aurum Ads — Telegram Ad Exchange", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(channels.router, prefix="/api/channels", tags=["channels"])
app.include_router(orders_router, prefix="/api", tags=["orders"])
app.include_router(payments_router, prefix="/api", tags=["payments"])
app.include_router(transactions.router, prefix="/api/transactions", tags=["transactions"])
app.include_router(users.router, prefix="/api/users", tags=["users"])
app.include_router(webhooks.router, prefix="/api/webhooks", tags=["webhooks"])
app.include_router(admin.router, prefix="/api/admin", tags=["admin"])
app.include_router(auth_router, prefix="/api", tags=["auth"])

STATIC_DIR = Path(__file__).parent / "static"


@app.get("/miniapp/{full_path:path}")
async def miniapp_spa(full_path: str):
    fp = STATIC_DIR / full_path
    if fp.is_file():
        return FileResponse(fp)
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/miniapp")
async def miniapp_index():
    return FileResponse(STATIC_DIR / "index.html")


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    if isinstance(exc, HTTPException):
        raise exc
    logger.error("Unhandled error: %s %s", type(exc).__name__, exc, exc_info=True)
    return JSONResponse(status_code=500, content={"error": "Internal server error"})


@app.get("/health")
async def health():
    return {"status": "ok"}
