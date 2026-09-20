import sys 
from src.components.data_ingestion import DataIngestion 
from src.components.data_transformation import DataTransformation 
from src.components.model_trainer import ModelTrainer 
from src.exception import CustomException 
from src.logger import get_logger 
logger = get_logger(__name__) 

def run_training_pipeline():
    try:
        logger.info("TRAINING PIPELINE STARTED....") 
        #Data Ingestion 
        data_ingestion = DataIngestion() 
        train_path, test_path = data_ingestion.initiate_data_ingestion() 

        #data transformation 
        data_transformation = DataTransformation() 
        train_arr, test_arr , _ = data_transformation.initiate_data_transformation(train_path, test_path)


        #Model training 
        model_trainer = ModelTrainer() 
        best_model_name, best_model_score = model_trainer.initiate_model_trainer(train_arr, test_arr) 

        logger.info(f"TRAINING PIPELINE COMPLETED | BEST MODEL: {best_model_name}, Accuracy: {best_model_score:.2f}") 
        print(f"Training Complete. Best Model: {best_model_name}(accuracy = {best_model_score:.2f})") 
    except Exception as e :
        raise CustomException(e,sys) 

if __name__ == "__main__":
    run_training_pipeline()






# import sys 
# from src.logger import get_logger 
# from src.exception import CustomException
# from src.components.data_ingestion import DataIngestion
# from src.components.data_transformation import DataTransformation
# from src.components.model_trainer import ModleTrainer
# logger = get_logger(__name__)

# def run_training_pipeline():
#     try:
#         logger.info("TRAINING PIPELINE STARTED .................")
#         # I will create the object of data ingestion file return the train and test path 
#         data_ingestion = DataIngestion()
#         train_path , test_path = data_ingestion.initiate_data_ingestion()
        
#         # second file data tranfromation file to return the train arr and test arr 
        
#         data_transformer = DataTransformation()
#         train_arr ,test_arr, _ = data_transformer.initiate_data_transformation(train_path,test_path)
#         # model trainer se model ko pkl me convert karna trian karke 
        
#         model_trainer = ModleTrainer()
#         best_model_score,best_model_name  = model_trainer.initiate_model_trainer(train_arr,test_arr)
#         logger.info (f'TRAINING PIPELINE COMPELETED  best model --> {best_model_name} accuracy -->{best_model_score}')
        
#         print(f" best model name ---> {best_model_name} and best model accura ---> {best_model_score}")
        
#     except Exception as e :
#         raise CustomException (e, sys)
    
    
# if __name__ == "__main__":
#     run_training_pipeline()