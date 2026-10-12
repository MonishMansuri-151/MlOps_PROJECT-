


import os
import sys
import uvicorn
from contextlib import asynccontextmanager
from pathlib import Path

# Root folder must come FIRST on sys.path. Both this folder and
# chatbot_version_2 have a package named "src"; root's "src" must win.
# (Needed for the uvicorn reload process too.)
_ROOT_DIR = str(Path(__file__).resolve().parent)
if _ROOT_DIR in sys.path:
    sys.path.remove(_ROOT_DIR)
sys.path.insert(0, _ROOT_DIR)

from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware

from src.exception import CustomException
from src.logger import get_logger
from src.pipeline.predict_pipeline import CustomData, PredictPipeline

from nlp_pretrained.ner_tagger import (
    get_pos_tags,
    extract_entities,
)
from nlp_pretrained.embedding import most_similar_words
from nlp_pretrained.sentiment_analyzer import analyze_sentiment


# --------------------------------------------------
# MCP CHATBOT IMPORTS
# --------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent
MCP_DIR = BASE_DIR / "chatbot_version_2"

if not MCP_DIR.is_dir():
    raise RuntimeError(f"MCP folder not found: {MCP_DIR}")

# Make MCP modules importable (api, auth, llm, mcp_app, ...).
# Appended at the END so it can never hide root packages such as "src".
# This must happen before importing the MCP routers.
if str(MCP_DIR) not in sys.path:
    sys.path.append(str(MCP_DIR))

# Load MCP .env if python-dotenv is installed.
try:
    from dotenv import load_dotenv
    load_dotenv(MCP_DIR / ".env", override=False)
except ImportError:
    pass

from api.chat import router as mcp_chat_router
from api.auth import router as mcp_auth_router
from mcp_app.register_tools import register_all_tools


# --------------------------------------------------
# APP SETUP
# --------------------------------------------------

logger = get_logger(__name__)
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

@asynccontextmanager
async def lifespan(_app: FastAPI):
    """Fill the MCP tool registry once. Without this the chatbot has no tools."""
    count = register_all_tools()
    logger.info("Registered %s MCP tools.", count)
    yield


app = FastAPI(title="Sanjivni Healthcare Website", lifespan=lifespan)

SESSION_SECRET_KEY = os.getenv("SESSION_SECRET_KEY")
if not SESSION_SECRET_KEY:
    raise RuntimeError(
        "SESSION_SECRET_KEY is missing. Configure it in chatbot_version_2/.env "
        "or in your environment."
    )

app.add_middleware(
    SessionMiddleware,
    secret_key=SESSION_SECRET_KEY,
    same_site="lax",
    https_only=os.getenv("SESSION_HTTPS_ONLY", "false").lower() == "true",
)

# Register MCP routes directly on the website app.
app.include_router(mcp_chat_router)
app.include_router(mcp_auth_router)



# Existing website static files.
app.mount(
    "/static",
    StaticFiles(directory=str(BASE_DIR / "static")),
    name="static",
)


# --------------------------------------------------
# HOME PAGE
# --------------------------------------------------

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    logger.info("Home page accessed.")
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={},
    )


# --------------------------------------------------
# PREDICTION
# --------------------------------------------------

@app.get("/predict", response_class=HTMLResponse)
async def predict_form(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="predict.html",
        context={"result": None},
    )


@app.post("/predict", response_class=HTMLResponse)
async def predict_result(
    request: Request,
    age: int = Form(...),
    gender: str = Form(...),
    fever: float = Form(...),
    cough: str = Form(...),
    city: str = Form(...),
):
    try:
        custom_data = CustomData(
            age=age,
            gender=gender,
            fever=fever,
            cough=cough,
            city=city,
        )

        data_df = custom_data.get_data_as_dataframe()
        predict_pipeline = PredictPipeline()
        result, probability = predict_pipeline.predict(data_df)

        return templates.TemplateResponse(
            request=request,
            name="predict.html",
            context={
                "result": result,
                "probability": probability,
                "form_data": {
                    "age": age,
                    "gender": gender,
                    "fever": fever,
                    "cough": cough,
                    "city": city,
                },
            },
        )

    except Exception as exc:
        logger.exception("Prediction failed.")
        raise CustomException(exc, sys) from exc


# --------------------------------------------------
# HEALTH CHECK
# --------------------------------------------------

@app.get("/health")
async def health_check():
    return {"status": "ok"}


# --------------------------------------------------
# PRETRAINED NLP
# --------------------------------------------------

@app.get("/pretrained-nlp", response_class=HTMLResponse)
async def pretrained_nlp_form(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="pretrained_nlp.html",
        context={
            "result": None,
            "form_data": {"query": ""},
            "error": None,
        },
    )


@app.post("/pretrained-nlp", response_class=HTMLResponse)
async def pretrained_nlp_analysis(
    request: Request,
    query: str = Form(...),
):
    query = query.strip()

    if not query:
        return templates.TemplateResponse(
            request=request,
            name="pretrained_nlp.html",
            context={
                "result": None,
                "form_data": {"query": ""},
                "error": "Please enter some text.",
            },
        )

    try:
        pos_tags = get_pos_tags(query)
        entities = extract_entities(query)
        sentiment = analyze_sentiment(query)

        similar_words = []
        words = query.split()

        if words:
            try:
                similar_words = most_similar_words(
                    words[0].lower(),
                    topn=5,
                )
            except Exception:
                logger.exception("Word similarity lookup failed.")

        result = {
            "query": query,
            "pos_tags": pos_tags,
            "entities": entities,
            "similar_words": similar_words,
            "sentiment": sentiment,
        }

        return templates.TemplateResponse(
            request=request,
            name="pretrained_nlp.html",
            context={
                "result": result,
                "form_data": {"query": query},
                "error": None,
            },
        )

    except Exception:
        logger.exception("Pretrained NLP analysis failed.")

        return templates.TemplateResponse(
            request=request,
            name="pretrained_nlp.html",
            context={
                "result": None,
                "form_data": {"query": query},
                "error": "Unable to analyze the text right now.",
            },
        )


# --------------------------------------------------
# RUN WEBSITE + MCP ON ONE SERVER
# --------------------------------------------------

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
    )
