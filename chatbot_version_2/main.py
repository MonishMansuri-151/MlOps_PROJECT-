import os
from api.auth import router as auth_router
from api.chat import router as chat_router
from fastapi import FastAPI
from starlette.middleware.sessions import SessionMiddleware
import uvicorn
from database.queries import check_database_connection
from src.logger import get_logger

logger = get_logger(__name__)

SESSION_SECRET_KEY = os.getenv("SESSION_SECRET_KEY")

if not SESSION_SECRET_KEY:
    raise RuntimeError(
        "SESSION_SECRET_KEY is missing. "
        "Set it in your .env file before starting the application."
    )

app = FastAPI(
    title="Sanjivni MCP",
    description="AI-powered healthcare platform with MCP architecture",
    version="1.0.0",
)

app.add_middleware(
    SessionMiddleware,
    secret_key=SESSION_SECRET_KEY,
    same_site="lax",
    https_only=os.getenv("SESSION_HTTPS_ONLY", "false").lower() == "true",
)



app.include_router(chat_router)
app.include_router(auth_router)

from fastapi import Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

templates = Jinja2Templates(directory="templates")


@app.get("/register", response_class=HTMLResponse)
def register_page(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="register.html",
        context={},
    )

@app.get("/")
def root():
    return {
        "application": "Sanjivni MCP",
        "status": "running",
    }


@app.get("/health")
def health_check():
    return {
        "application": "Sanjivni MCP",
        "status": "healthy",
    }


@app.get("/health/database")
def database_health_check():
    try:
        result = check_database_connection()

        if result and result.get("status") == 1:
            return {
                "database": "connected",
                "status": "healthy",
            }

        return {
            "database": "error",
            "status": "unhealthy",
        }

    except Exception:
        logger.exception("Database health check failed.")

        return {
            "database": "connection_failed",
            "status": "unhealthy",
        }
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True) 