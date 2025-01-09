from typing import Optional, List
import secrets
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "Xero Data Extractor"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/xero"
    
    # Environment
    ENVIRONMENT: str = "development"
    
    # Database - configuración para Railway
    DB_TYPE: str = "mysql+pymysql"
    DATABASE_URL: Optional[str] = None
    DB_USER: str
    DB_PASSWORD: str
    DB_HOST: str
    DB_PORT: str
    DB_NAME: str
    
    # Security
    SECRET_KEY: str = secrets.token_urlsafe(32)
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8  # 8 days
    
    # Xero OAuth
    XERO_CLIENT_ID: str
    XERO_CLIENT_SECRET: str
    XERO_REDIRECT_URI: str = "http://localhost:8000/auth/callback"  # Default para development
    
    # CORS - con valores por defecto explícitos
    BACKEND_CORS_ORIGINS: List[str] = ["http://localhost:8000", "http://localhost"]

    @property
    def SQLALCHEMY_DATABASE_URI(self) -> str:
        """Genera la URL de conexión a la base de datos."""
        return f"{self.DB_TYPE}://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    class Config:
        case_sensitive = True
        env_file = ".env"

    def setup_environment(self):
        if self.ENVIRONMENT != "development":
            self.XERO_REDIRECT_URI = "https://xero.dataextractor.cloud/auth/callback"
            self.BACKEND_CORS_ORIGINS = ["https://xero.dataextractor.cloud"]

settings = Settings()
settings.setup_environment()