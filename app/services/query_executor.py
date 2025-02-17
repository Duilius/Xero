from sqlalchemy import text
from app.db.database import SessionLocal

def execute_query(query: str):
    """
    Ejecuta consultas SQL y retorna los resultados
    """
    db = SessionLocal()
    try:
        print(f"Executing query: {query}")  # Log la query
        
        # Ejecutar query
        result = db.execute(text(query))
        
        # Obtener nombres de columnas
        columns = result.keys()
        print(f"Columns: {columns}")  # Log las columnas
        
        # Convertir resultados
        rows = [dict(zip(columns, row)) for row in result.fetchall()]
        print(f"Results: {rows}")  # Log los resultados
        
        return {
            "success": True,
            "data": rows,
            "row_count": len(rows)
        }
        
    except Exception as e:
        print(f"Error executing query: {str(e)}")  # Log detallado del error
        raise e
        
    finally:
        db.close()