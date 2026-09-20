# the main purpose of this file to performing the data transformation 
# data divide the with thier target column and to apply the feture engineering 
# combine the np.c arrry to to export the pkl using utils.py save_object file 
# return path pkl and train_arr and test_arr 



import os 
import sys 
import pandas as pd 
from dataclasses import dataclass 
import numpy as np 
from sklearn.compose import ColumnTransformer 
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline 
from sklearn.preprocessing import OneHotEncoder , OrdinalEncoder
from src.exception import CustomException 
from src.logger import get_logger 
from src.utils import save_object 

logger = get_logger(__name__)


class DataTransformConfig:
    preprocessor_object_path_file = os.path.join('artifacts', 'preprocessor.pkl')
    
class DataTransformation:
    def __init__(self):
        self.Data_transform_config = DataTransformConfig()
        
    def get_data_transfrom_object (self):
        try:
            numerical_col = ['fever','age']
            ordinal_col =['cough']
            oneHot_col = ['city','gender']
            # for create the numerical pipeline 
            num_pipeline = Pipeline(steps=[(
              "imputer",  SimpleImputer(strategy=('mean'))
            )])
            # apply the one hot encoding  
            oneHot_pipeline = Pipeline(steps=[(
                'OneHotEncoder', OneHotEncoder(handle_unknown="ignore",sparse_output=False)
                
            )])
            # apply the ordinal encoding 
            ordinal_pipeline = Pipeline(steps=[(
                'ordinalEncoder',OrdinalEncoder(categories=[['Mild','Strong']])
            )])
            
            preprocessor = ColumnTransformer(
                transformers= [
                    ('num_pipeline', num_pipeline, numerical_col),
                    ('oneHot_pipeline',oneHot_pipeline,oneHot_col),
                    ('ordinal_pipeline',ordinal_pipeline,ordinal_col)
                ]
            )
            logger.info('preprocessor object create successfully ....')
            return preprocessor 
        except Exception as e :
            raise CustomException (e, sys)
    
    
    def initiate_data_transformation(self,train_path: str , test_path : str):
        try :
            train_df = pd.read_csv(train_path)
            test_df = pd.read_csv(test_path)
            logger.info('finaly train  and test data are loaded .....')
            target_column = 'has_covid'
            x_input_feature_train_df = train_df.drop(columns=[target_column])
            y_input_feature_train_df = train_df[target_column].map({'Yes': 1, 'No': 0})
            
            x_input_feature_test_df = test_df.drop(columns=[target_column])
            y_input_feature_test_df = test_df[target_column].map({'Yes': 1, 'No': 0})
            
            preprocessing_obj = self.get_data_transfrom_object()
            logger.info('applying the preprocessor on train and test data ......')
            
            input_feature_train_Arr = preprocessing_obj.fit_transform(x_input_feature_train_df)
            input_feature_test_Arr = preprocessing_obj.transform(x_input_feature_test_df)
            
            train_arr = np.c_[input_feature_train_Arr,np.array(y_input_feature_train_df)]
            test_arr = np.c_[input_feature_test_Arr,np.array(y_input_feature_test_df)]
            
            save_object(
                file_path= self.Data_transform_config.preprocessor_object_path_file,
                obj= preprocessing_obj
            )
            logger.info('save the object in preprocessor.pkl')
            return (
                train_arr,
                test_arr,
                self.Data_transform_config.preprocessor_object_path_file
            )
            
        except Exception as e :
            raise CustomException(e,sys)
        
        
if __name__ == '__main__':
    obj = DataTransformation()
    obj.initiate_data_transformation('artifacts/train.csv','artifacts/test.csv')
         
