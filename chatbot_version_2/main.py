"""
Sanjivni backend - FastAPI application.

Run alone (API only):   python main.py
Used by the website:    the project root main.py imports this folder's routers.
"""
import os
from contextlib import asynccontextmanager
from pathlib import Path

from dotenv import load_dotenv

# Load .env from this folder no matter where the app is started from.
load_dotenv(Path(__file__).resolve().parent / ".env")

import uvicorn  # noqa: E402
from fastapi import FastAPI  # noqa: E402
from starlette.middleware.sessions import SessionMiddleware  # noqa: E402

from api.auth import router as auth_router  # noqa: E402
from api.chat import router as chat_router  # noqa: E402
from database.queries import check_database_connection  # noqa: E402
from mcp_app.register_tools import register_all_tools  # noqa: E402
from src.logger import get_logger  # noqa: E402

logger = get_logger(__name__)

SESSION_SECRET_KEY = os.getenv("SESSION_SECRET_KEY")
if not SESSION_SECRET_KEY:
    raise RuntimeError(
        "SESSION_SECRET_KEY is missing. Set it in your .env file "
        "before starting the application."
    )


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """Startup: fill the MCP tool registry once."""
    count = register_all_tools()
    logger.info("Registered %s MCP tools.", count)
    yield


app = FastAPI(
    title="Sanjivni MCP",
    description="AI-powered healthcare platform with MCP architecture",
    version="1.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    SessionMiddleware,
    secret_key=SESSION_SECRET_KEY,
    same_site="lax",
    https_only=os.getenv("SESSION_HTTPS_ONLY", "false").lower() == "true",
    max_age=int(os.getenv("SESSION_MAX_AGE_SECONDS", str(8 * 60 * 60))),
)

app.include_router(chat_router)
app.include_router(auth_router)


@app.get("/")
def root():
    return {"application": "Sanjivni MCP", "status": "running"}


@app.get("/health")
def health_check():
    return {"application": "Sanjivni MCP", "status": "healthy"}


@app.get("/health/database")
def database_health_check():
    try:
        result = check_database_connection()
        if result and result.get("status") == 1:
            return {"database": "connected", "status": "healthy"}
        return {"database": "error", "status": "unhealthy"}
    except Exception:
        logger.exception("Database health check failed.")
        return {"database": "connection_failed", "status": "unhealthy"}


if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
