



# from pydantic_settings import BaseSettings
# from typing import Optional


# class Settings(BaseSettings):
#     # API Keys
#     OPENAI_API_KEY: Optional[str] = None
#     ELEVENLABS_API_KEY: Optional[str] = None
    
#     # Web Scraping APIs
#     PAGESPEED_API_KEY: Optional[str] = None
#     GOOGLE_API_KEY: Optional[str] = None
#     GOOGLE_SEARCH_ENGINE_ID: Optional[str] = None
    
#     # AWS Configuration
#     AWS_ACCESS_KEY_ID: Optional[str] = None
#     AWS_SECRET_ACCESS_KEY: Optional[str] = None
#     AWS_REGION: str = "ap-south-1"
#     S3_BUCKET_NAME: str = "sales-training-audio"
    
#     # MongoDB
#     MONGODB_URL: str = "mongodb://localhost:27017"
#     MONGODB_DB_NAME: str = "sales_training_db"
    
#     # Application
#     APP_ENV: str = "development"
#     DEBUG: bool = True
    
#     class Config:
#         env_file = ".env"
#         case_sensitive = True


# settings = Settings()



from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # API Keys
    OPENAI_API_KEY: Optional[str] = None
    ELEVENLABS_API_KEY: Optional[str] = None
    
    # Web Scraping APIs
    PAGESPEED_API_KEY: Optional[str] = None
    GOOGLE_API_KEY: Optional[str] = None
    GOOGLE_SEARCH_ENGINE_ID: Optional[str] = None
    
    # AWS Configuration
    AWS_ACCESS_KEY_ID: Optional[str] = None
    AWS_SECRET_ACCESS_KEY: Optional[str] = None
    AWS_REGION: str = "ap-south-1"
    S3_BUCKET_NAME: str = "sales-training-audio"
    
    # MongoDB
    MONGODB_URL: str = "mongodb://localhost:27017"
    MONGODB_DB_NAME: str = "sales_training_db"
    
    # Application
    APP_ENV: str = "development"
    DEBUG: bool = True
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()