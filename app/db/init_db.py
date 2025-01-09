from sqlalchemy import create_engine
from sqlalchemy_utils import database_exists, create_database
from app.core.config import settings
from app.models.base import Base
from app.models import user, organization, xero  # Importamos todos los modelos

def init_db() -> None:
    engine = create_engine(settings.SQLALCHEMY_DATABASE_URI)
    
    # Crear base de datos si no existe
    if not database_exists(engine.url):
        create_database(engine.url)
    
    # Crear todas las tablas
    Base.metadata.create_all(bind=engine)

if __name__ == "__main__":
    print("Creating initial database...")
    init_db()
    print("Database tables created successfully!")