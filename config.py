# config.py
from dotenv import load_dotenv
import os

# Cargar las variables desde el archivo .env
load_dotenv()

# Definir las variables como constantes
XERO_CLIENT_ID = os.getenv("XERO_CLIENT_ID")
XERO_CLIENT_SECRET = os.getenv("XERO_CLIENT_SECRET")
XERO_REDIRECT_URI = os.getenv("XERO_REDIRECT_URI")
XERO_ACCESS_TOKEN = os.getenv("XERO_ACCESS_TOKEN")
XERO_REFRESH_TOKEN = os.getenv("XERO_REFRESH_TOKEN")
XERO_TENAN_ID = os.getenv("XERO_TENAN_ID")




"""from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    DATABASE_URL: str
    XERO_CLIENT_ID: str
    XERO_CLIENT_SECRET: str
    SECRET_KEY: str
    CORS_ORIGINS: list[str] = ["*"]
    
    class Config:
        env_file = ".env"

@lru_cache()
def get_settings():
    return Settings()"""