# Text ---> Machine understand Numbers ---> (TF-IDF, GLOVE, GENSIM, FASTTEXT), Advance(huggingface transformer(All-minilm-l6-v2), googlegenerativeembeddings, openaiembeddings) 

import sys 
import gensim.downloader as api 
from src.exception import CustomException 
from src.logger import get_logger 
logger = get_logger(__name__) 

_model = None 
MODEL_NAME = "glove-wiki-gigaword-50" 

def _get_model():
    global _model 
    if _model is None:
        logger.info(f"Loading pretrained Model for Embeddings: {MODEL_NAME}") 
        _model= api.load(MODEL_NAME) 
        logger.info(f"Embeddings Loaded , Vocabulary size: {len(_model.index_to_key)}") 
    return _model 

def most_similar_words(word:str , topn: int=5):
    try:
        model = _get_model() 
        word = word.lower() 
        if word not in model:
            logger.info(f" '{word}' was not found in voucabulary.")
            return []
        results = model.most_similar(word, topn=topn) 
        logger.info(f"Most Similar to '{word}' : '{results}'")
        return results 
    except Exception as e:
        raise CustomException(e,sys)  

def word_similarity(word1:str , word2: str):
    try:
        model = _get_model() 
        score = float(model.similarity(word1.lower() , word2.lower())) 
        logger.info(f"Similarity('{word1}', '{word2}') = {score:.3f}") 
        return score 
    except Exception as e :
        raise CustomException(e,sys) 



















# import sys
# from src.logger import get_logger 
# from src.exception import CustomException 
# import gensim.downloader as api
# logger = get_logger(__name__)

# _model = None 
# MODEL_NAME = "glove-wiki-gigaword-50"
# # this is pretrianed model gensim liabrary 

# def get_model():
#     global _model 
#     logger.info(f"loading the pretrained Embeding .... {MODEL_NAME}")
#     _model = api.load(MODEL_NAME)
#     logger.info(f"loading Embeding  vocablary size ...{len(_model.index_to_key)}")
#     return _model

# def most_similar_word(word: str, topn : int=5) :
#     try:
#         model = get_model()
#         word = word.lower()
#         if word not in model :
#             logger.info (f"word not found in model {word}")
#             return []
#         result = model.most_similar(word,topn = topn) 
#         return result 
#     except Exception as e :
#         raise CustomException(e,sys)
    

# def similer_word(word1:str,word2:str):
#     try:
#         model = get_model()
#         score = float(model.similarity(word1.lower(),word2.lower()))
#         logger.info(f"word1{word1} and word2 {word2} score {score}")
#         return score   
        
#     except Exception as e :
#         raise CustomException(e,sys)
    
    
 





