from typing import Optional, List
import secrets
from pydantic_settings import BaseSettings
import os
from dotenv import load_dotenv

# Cargar variables de entorno desde .env
load_dotenv()

class Settings(BaseSettings):
    PROJECT_NAME: str = "Xero Data Extractor"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/xero"
    
    # Environment
    ENVIRONMENT: str = os.getenv('ENVIRONMENT', 'development')
    
    # Database - configuración para Railway
    DB_TYPE: str = os.getenv('DB_TYPE', 'mysql+pymysql')
    DATABASE_URL: Optional[str] = os.getenv('DATABASE_URL')
    DB_USER: str = os.getenv('DB_USER', 'root')
    DB_PASSWORD: str = os.getenv('DB_PASSWORD', '')
    DB_HOST: str = os.getenv('DB_HOST', 'localhost')
    DB_PORT: str = os.getenv('DB_PORT', '3306')
    DB_NAME: str = os.getenv('DB_NAME', 'railway')
    
    # Security
    SECRET_KEY: str = secrets.token_urlsafe(32)
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8  # 8 days
    
    # Xero OAuth
    XERO_CLIENT_ID: str = os.getenv('XERO_CLIENT_ID', '')
    XERO_CLIENT_SECRET: str = os.getenv('XERO_CLIENT_SECRET', '')
    XERO_REDIRECT_URI: str = os.getenv('XERO_REDIRECT_URI', '')  # Añadido esta línea

    #Secret Key - OpenAI API
    inventario_demo_key:str = os.getenv('inventario_demo_key', '')

    ADMIN_EMAILS: List[str] = [
        "duilio@dataextractor.cloud"
        # Aquí puedes agregar más emails de administradores
    ]
    
    @property
    def SQLALCHEMY_DATABASE_URI(self) -> str:
        """Genera la URL de conexión a la base de datos."""
        if self.DATABASE_URL:
            return self.DATABASE_URL.replace('mysql://', f'{self.DB_TYPE}://')
        return f"{self.DB_TYPE}://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    class Config:
        case_sensitive = True
        env_file = ".env"

settings = Settings()

# Debug para ver qué valores se están usando
#print("==== Settings Values ====")
#print(f"ENVIRONMENT: {settings.ENVIRONMENT}")
#print(f"DB_TYPE: {settings.DB_TYPE}")
#print(f"DB_USER: {settings.DB_USER}")
#print(f"DB_HOST: {settings.DB_HOST}")
#print(f"DB_PORT: {settings.DB_PORT}")
#print(f"DB_NAME: {settings.DB_NAME}")
#print(f"SQLALCHEMY_DATABASE_URI: {settings.SQLALCHEMY_DATABASE_URI}")
#print("XERO_REDIRECT_URI: {settings.XERO_REDIRECT_URI}")
#print("========================")