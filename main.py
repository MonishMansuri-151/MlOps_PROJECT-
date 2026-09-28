import os
import sys
import uvicorn
from chatbot.router.injury import router as injury_router
from contextlib import asynccontextmanager
from chatbot.router.admin_analytics import router as admin_analytics_router
from fastapi import APIRouter, HTTPException
from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware

from src.exception import CustomException
from src.logger import get_logger
logger = get_logger(__name__)

from src.pipeline.predict_pipeline import CustomData, PredictPipeline

from nlp_pretrained.ner_tagger import (
    get_pos_tags,
    extract_entities
)

from nlp_pretrained.embedding import (
    most_similar_words
)

from nlp_pretrained.sentiment_analyzer import (
    analyze_sentiment
)

# Chatbot routers
from chatbot.router.chat import router as chatbot_router
from chatbot.auth.router import router as auth_router

# Chat history cleanup
from chatbot.database.queries import delete_expired_chat_sessions
from chatbot.router.medical import router as medical_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        deleted = delete_expired_chat_sessions(20)

        logger.info(
            f"Chat history cleanup completed. "
            f"Deleted sessions: {deleted}"
        )

    except Exception as e:
        logger.error(
            f"Chat history cleanup failed: {e}"
        )

    yield


app = FastAPI(
    title="Covid Prediction Clinic",
    lifespan=lifespan
)


app.add_middleware(
    SessionMiddleware,
    secret_key="change-this-secret-key"
)


# Chatbot router
app.include_router(chatbot_router)
# Authentication router
app.include_router(auth_router)
# medical router 
app.include_router(medical_router)
# injury router added
app.include_router(injury_router)
# add admin analytics file router 
app.include_router(admin_analytics_router)

# Existing static files
app.mount(
    "/static",
    StaticFiles(directory="static"),
    name="static"
)


# Chatbot frontend static files
app.mount(
    "/chatbot/static",
    StaticFiles(directory="chatbot/frontend"),
    name="chatbot_static"
)

##Set the template folder 
templates = Jinja2Templates(directory="templates") 

@app.get("/", response_class=HTMLResponse) 
async def home(request:Request):
    logger.info("Home page accessed...") 
    return templates.TemplateResponse(request, "index.html") 

@app.get("/predict", response_class=HTMLResponse)
async def predict_form(request: Request):
    logger.info("Predict form page accessed.....") 
    return templates.TemplateResponse(request, "predict.html", {"result":None}) 

@app.post("/predict", response_class=HTMLResponse)
async def predict_result(
    request: Request,
    age:int = Form(...),
    gender: str = Form(...),
    fever: float = Form(...),
    cough: str = Form(...),
    city: str = Form(...) 
) :
    try:
        logger.info(f"Prediction request received :: age{age}, gender{gender}, fever{fever}, cough{cough},city{city}")
        custom_data = CustomData(age=age,gender=gender,fever=fever,cough=cough,city=city)
        data_df = custom_data.get_data_as_dataframe() 
        predict_pipeline = PredictPipeline() 
        result , probability = predict_pipeline.predict(data_df) 
        return templates.TemplateResponse(
            request,
            "predict.html",
            {
                "result": result,
                "probability":probability,
                "form_data": {
                    "age":age,
                    "gender":gender,
                    "fever":fever,
                    "cough":cough,
                    "city":city
                }
            }
        )
    except Exception as e:
        raise CustomException(e,sys) 

@app.get("/health")
async def health_check():
    logger.info("Monitering alert....")
    return {"status":"ok"}

## nlp (netural language processing ..................................)



### NLP Pretrained 

@app.get("/pretrained-nlp" , response_class=HTMLResponse) 
async def pretrained_nlp_form(request: Request):
    return templates.TemplateResponse(request, 
                                      "pretrained_nlp.html",
                                      {
                                          "result": None,

                                          "form_data": {
                                              "query": ""
                                          },
                                          "error": None 
                                      })

@app.post("/pretrained-nlp" , response_class=HTMLResponse) 
async def pretrained_nlp_analysis(
    request: Request,
    query: str= Form(...)
):
    try:
        ## text clean 
        query = query.strip() 
        if not query:
            return templates.TemplateResponse(
                request,
                "pretrained_nlp.html",
                {
                    "result": None,
                    "form_data": {
                        "query": ""
                    },
                    "error": "Please enter some text..." 
                }
            )

        ## Pos tagging 
        pos_tags = get_pos_tags(query) 

        ## NER 
        entities = extract_entities(query) 

        ## Sentiment Analysis 
        sentiment = analyze_sentiment(query) 

        ## Word Embeddings 
        similar_words = [] 
        words = query.split() 
        first_word = words[0].lower() 
        if words:
            try:
                similar_words = most_similar_words(first_word , topn=5) 
            except Exception as e :
                logger.warning(f"Glove similarity failed for: " , {first_word} ,"and the error is:", {e}) 
                similar_words = [] 
        ## final result 
        result = {
            "query": query,
            "pos_tags": pos_tags,
            "entities": entities,
            "similar_words": similar_words,
            "sentiment": sentiment
        }
        ##render result 
        return templates.TemplateResponse(
            request,
            "pretrained_nlp.html",
            {
                "result": result,
                "form_data": {
                    "query": query
                },
                "error": None
            }
        )



    except Exception as e :
        logger.info("Error occured in pretrained nlp analysis")
        return templates.TemplateResponse(
            request,
            "pretrained_nlp.html",
            {
                "result": None,
                "form_data": {
                    "query": query
                },
                "error": str(e)
            }
        )
     


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True) 