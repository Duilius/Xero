from sqlalchemy import create_engine, text
from app.core.config import settings

def check_database():
    # Crear conexión
    engine = create_engine(settings.SQLALCHEMY_DATABASE_URI)
    
    # Queries de verificación
    queries = [
        "SELECT COUNT(*) as count FROM chat_clients",
        "SELECT COUNT(*) as count FROM chat_issued_invoices",
        "SELECT DISTINCT contact_name FROM chat_clients LIMIT 10"
    ]
    
    try:
        with engine.connect() as connection:
            print("\n=== Verificación de Datos ===")
            
            for query in queries:
                print(f"\nEjecutando: {query}")
                result = connection.execute(text(query))
                rows = result.fetchall()
                
                print("Resultados:")
                for row in rows:
                    print(row)
                    
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    check_database()