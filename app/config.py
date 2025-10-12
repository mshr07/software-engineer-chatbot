from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # OpenAI API Configuration
    openai_api_key: str
    
    # Database Configuration
    database_url: str
    
    # Authentication Configuration
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # Redis Configuration
    redis_url: str = "redis://localhost:6379"
    
    # Application Configuration
    app_name: str = "Software Engineer Chatbot"
    debug: bool = False
    
    class Config:
        env_file = ".env"

settings = Settings()