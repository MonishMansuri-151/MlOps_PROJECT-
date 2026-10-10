# import os
# import sys
# import uvicorn
# from chatbot.router.injury import router as injury_router
# from contextlib import asynccontextmanager
# from chatbot.router.admin_analytics import router as admin_analytics_router
# from fastapi import APIRouter, HTTPException
# from fastapi import FastAPI, Form, Request
# from fastapi.responses import HTMLResponse
# from fastapi.staticfiles import StaticFiles
# from fastapi.templating import Jinja2Templates
# from starlette.middleware.sessions import SessionMiddleware

# from src.exception import CustomException
# from src.logger import get_logger
# logger = get_logger(__name__)

# from src.pipeline.predict_pipeline import CustomData, PredictPipeline

# from nlp_pretrained.ner_tagger import (
#     get_pos_tags,
#     extract_entities
# )

# from nlp_pretrained.embedding import (
#     most_similar_words
# )

# from nlp_pretrained.sentiment_analyzer import (
#     analyze_sentiment
# )

# # Chatbot routers
# from chatbot.router.chat import router as chatbot_router
# from chatbot.auth.router import router as auth_router

# # Chat history cleanup
# from chatbot.database.queries import delete_expired_chat_sessions
# from chatbot.router.medical import router as medical_router

# @asynccontextmanager
# async def lifespan(app: FastAPI):
#     try:
#         deleted = delete_expired_chat_sessions(20)

#         logger.info(
#             f"Chat history cleanup completed. "
#             f"Deleted sessions: {deleted}"
#         )

#     except Exception as e:
#         logger.error(
#             f"Chat history cleanup failed: {e}"
#         )

#     yield


# app = FastAPI(
#     title="Covid Prediction Clinic",
#     lifespan=lifespan
# )


# app.add_middleware(
#     SessionMiddleware,
#     secret_key="change-this-secret-key"
# )


# # Chatbot router
# app.include_router(chatbot_router)
# # Authentication router
# app.include_router(auth_router)
# # medical router 
# app.include_router(medical_router)
# # injury router added
# app.include_router(injury_router)
# # add admin analytics file router 
# app.include_router(admin_analytics_router)

# # Existing static files
# app.mount(
#     "/static",
#     StaticFiles(directory="static"),
#     name="static"
# )


# # Chatbot frontend static files
# app.mount(
#     "/chatbot/static",
#     StaticFiles(directory="chatbot/frontend"),
#     name="chatbot_static"
# )

# ##Set the template folder 
# templates = Jinja2Templates(directory="templates") 

# @app.get("/", response_class=HTMLResponse) 
# async def home(request:Request):
#     logger.info("Home page accessed...") 
#     return templates.TemplateResponse(request, "index.html") 

# @app.get("/predict", response_class=HTMLResponse)
# async def predict_form(request: Request):
#     logger.info("Predict form page accessed.....") 
#     return templates.TemplateResponse(request, "predict.html", {"result":None}) 

# @app.post("/predict", response_class=HTMLResponse)
# async def predict_result(
#     request: Request,
#     age:int = Form(...),
#     gender: str = Form(...),
#     fever: float = Form(...),
#     cough: str = Form(...),
#     city: str = Form(...) 
# ) :
#     try:
#         logger.info(f"Prediction request received :: age{age}, gender{gender}, fever{fever}, cough{cough},city{city}")
#         custom_data = CustomData(age=age,gender=gender,fever=fever,cough=cough,city=city)
#         data_df = custom_data.get_data_as_dataframe() 
#         predict_pipeline = PredictPipeline() 
#         result , probability = predict_pipeline.predict(data_df) 
#         return templates.TemplateResponse(
#             request,
#             "predict.html",
#             {
#                 "result": result,
#                 "probability":probability,
#                 "form_data": {
#                     "age":age,
#                     "gender":gender,
#                     "fever":fever,
#                     "cough":cough,
#                     "city":city
#                 }
#             }
#         )
#     except Exception as e:
#         raise CustomException(e,sys) 

# @app.get("/health")
# async def health_check():
#     logger.info("Monitering alert....")
#     return {"status":"ok"}

# ## nlp (netural language processing ..................................)



# ### NLP Pretrained 

# @app.get("/pretrained-nlp" , response_class=HTMLResponse) 
# async def pretrained_nlp_form(request: Request):
#     return templates.TemplateResponse(request, 
#                                       "pretrained_nlp.html",
#                                       {
#                                           "result": None,

#                                           "form_data": {
#                                               "query": ""
#                                           },
#                                           "error": None 
#                                       })

# @app.post("/pretrained-nlp" , response_class=HTMLResponse) 
# async def pretrained_nlp_analysis(
#     request: Request,
#     query: str= Form(...)
# ):
#     try:
#         ## text clean 
#         query = query.strip() 
#         if not query:
#             return templates.TemplateResponse(
#                 request,
#                 "pretrained_nlp.html",
#                 {
#                     "result": None,
#                     "form_data": {
#                         "query": ""
#                     },
#                     "error": "Please enter some text..." 
#                 }
#             )

#         ## Pos tagging 
#         pos_tags = get_pos_tags(query) 

#         ## NER 
#         entities = extract_entities(query) 

#         ## Sentiment Analysis 
#         sentiment = analyze_sentiment(query) 

#         ## Word Embeddings 
#         similar_words = [] 
#         words = query.split() 
#         first_word = words[0].lower() 
#         if words:
#             try:
#                 similar_words = most_similar_words(first_word , topn=5) 
#             except Exception as e :
#                 logger.warning(f"Glove similarity failed for: " , {first_word} ,"and the error is:", {e}) 
#                 similar_words = [] 
#         ## final result 
#         result = {
#             "query": query,
#             "pos_tags": pos_tags,
#             "entities": entities,
#             "similar_words": similar_words,
#             "sentiment": sentiment
#         }
#         ##render result 
#         return templates.TemplateResponse(
#             request,
#             "pretrained_nlp.html",
#             {
#                 "result": result,
#                 "form_data": {
#                     "query": query
#                 },
#                 "error": None
#             }
#         )



#     except Exception as e :
#         logger.info("Error occured in pretrained nlp analysis")
#         return templates.TemplateResponse(
#             request,
#             "pretrained_nlp.html",
#             {
#                 "result": None,
#                 "form_data": {
#                     "query": query
#                 },
#                 "error": str(e)
#             }
#         )
     


# if __name__ == "__main__":
#     uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True) 

# import os
# import sys
# import uvicorn

# from contextlib import asynccontextmanager

# from fastapi import FastAPI, Form, Request
# from fastapi.responses import HTMLResponse
# from fastapi.staticfiles import StaticFiles
# from fastapi.templating import Jinja2Templates
# from starlette.middleware.sessions import SessionMiddleware

# from chatbot.router.injury import router as injury_router
# from chatbot.router.admin_analytics import router as admin_analytics_router
# from chatbot.auth.router import router as auth_router
# from chatbot.database.queries import delete_expired_chat_sessions
# from chatbot.router.medical import router as medical_router

# from src.exception import CustomException
# from src.logger import get_logger
# from src.pipeline.predict_pipeline import CustomData, PredictPipeline

# from nlp_pretrained.ner_tagger import (
#     get_pos_tags,
#     extract_entities,
# )
# from nlp_pretrained.embedding import most_similar_words
# from nlp_pretrained.sentiment_analyzer import analyze_sentiment

# logger = get_logger(__name__)

# # Keep templates and static files in the original project.
# templates = Jinja2Templates(directory="templates")


# @asynccontextmanager
# async def lifespan(app: FastAPI):
#     """Clean expired chat sessions when the application starts."""
#     try:
#         deleted = delete_expired_chat_sessions(20)
#         logger.info(
#             "Chat history cleanup completed. Deleted sessions: %s",
#             deleted,
#         )
#     except Exception:
#         logger.exception("Chat history cleanup failed.")

#     yield


# app = FastAPI(
#     title="Sanjivni Healthcare Website",
#     lifespan=lifespan,
# )

# # Use an environment variable instead of a hardcoded session secret.
# session_secret = os.getenv("SESSION_SECRET_KEY")
# if not session_secret:
#     raise RuntimeError(
#         "SESSION_SECRET_KEY is missing. Configure it in your .env file."
#     )

# app.add_middleware(
#     SessionMiddleware,
#     secret_key=session_secret,
#     same_site="lax",
#     https_only=os.getenv("SESSION_HTTPS_ONLY", "false").lower() == "true",
# )

# # Keep the original authentication and non-chatbot features.
# app.include_router(auth_router)
# app.include_router(medical_router)
# app.include_router(injury_router)
# app.include_router(admin_analytics_router)

# # Serve the original website's static files, including chatbot.css/js.
# app.mount(
#     "/static",
#     StaticFiles(directory="static"),
#     name="static",
# )

# # Use the original homepage and include the new chatbot widget in index.html.
# @app.get("/", response_class=HTMLResponse)
# async def home(request: Request):
#     logger.info("Home page accessed.")
#     return templates.TemplateResponse(
#         request=request,
#         name="index.html",
#         context={},
#     )


# @app.get("/predict", response_class=HTMLResponse)
# async def predict_form(request: Request):
#     logger.info("Prediction form accessed.")
#     return templates.TemplateResponse(
#         request=request,
#         name="predict.html",
#         context={"result": None},
#     )


# @app.post("/predict", response_class=HTMLResponse)
# async def predict_result(
#     request: Request,
#     age: int = Form(...),
#     gender: str = Form(...),
#     fever: float = Form(...),
#     cough: str = Form(...),
#     city: str = Form(...),
# ):
#     try:
#         logger.info("Prediction request received.")

#         custom_data = CustomData(
#             age=age,
#             gender=gender,
#             fever=fever,
#             cough=cough,
#             city=city,
#         )

#         data_df = custom_data.get_data_as_dataframe()
#         predict_pipeline = PredictPipeline()
#         result, probability = predict_pipeline.predict(data_df)

#         return templates.TemplateResponse(
#             request=request,
#             name="predict.html",
#             context={
#                 "result": result,
#                 "probability": probability,
#                 "form_data": {
#                     "age": age,
#                     "gender": gender,
#                     "fever": fever,
#                     "cough": cough,
#                     "city": city,
#                 },
#             },
#         )

#     except Exception as exc:
#         raise CustomException(exc, sys) from exc


# @app.get("/health")
# async def health_check():
#     return {"status": "ok"}


# @app.get("/pretrained-nlp", response_class=HTMLResponse)
# async def pretrained_nlp_form(request: Request):
#     return templates.TemplateResponse(
#         request=request,
#         name="pretrained_nlp.html",
#         context={
#             "result": None,
#             "form_data": {"query": ""},
#             "error": None,
#         },
#     )


# @app.post("/pretrained-nlp", response_class=HTMLResponse)
# async def pretrained_nlp_analysis(
#     request: Request,
#     query: str = Form(...),
# ):
#     query = query.strip()

#     if not query:
#         return templates.TemplateResponse(
#             request=request,
#             name="pretrained_nlp.html",
#             context={
#                 "result": None,
#                 "form_data": {"query": ""},
#                 "error": "Please enter some text.",
#             },
#         )

#     try:
#         pos_tags = get_pos_tags(query)
#         entities = extract_entities(query)
#         sentiment = analyze_sentiment(query)

#         similar_words = []
#         words = query.split()

#         if words:
#             try:
#                 similar_words = most_similar_words(
#                     words[0].lower(),
#                     topn=5,
#                 )
#             except Exception:
#                 logger.exception("Word similarity lookup failed.")

#         result = {
#             "query": query,
#             "pos_tags": pos_tags,
#             "entities": entities,
#             "similar_words": similar_words,
#             "sentiment": sentiment,
#         }

#         return templates.TemplateResponse(
#             request=request,
#             name="pretrained_nlp.html",
#             context={
#                 "result": result,
#                 "form_data": {"query": query},
#                 "error": None,
#             },
#         )

#     except Exception:
#         logger.exception("Pretrained NLP analysis failed.")
#         return templates.TemplateResponse(
#             request=request,
#             name="pretrained_nlp.html",
#             context={
#                 "result": None,
#                 "form_data": {"query": query},
#                 "error": "Unable to analyze the text right now.",
#             },
#         )


# if __name__ == "__main__":
#     uvicorn.run(
#         "main:app",
#         host="0.0.0.0",
#         port=8000,
#         reload=True,
#     )




import os
import sys
import uvicorn
from pathlib import Path

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

# Make MCP modules importable.
# This must happen before importing the MCP routers.
if str(MCP_DIR) not in sys.path:
    sys.path.insert(0, str(MCP_DIR))

# Load MCP .env if python-dotenv is installed.
try:
    from dotenv import load_dotenv
    load_dotenv(MCP_DIR / ".env", override=False)
except ImportError:
    pass

from api.chat import router as mcp_chat_router
from api.auth import router as mcp_auth_router


# --------------------------------------------------
# APP SETUP
# --------------------------------------------------

logger = get_logger(__name__)
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

app = FastAPI(title="Sanjivni Healthcare Website")

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
