from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
#from app.models import Pagos, Inventario

router = APIRouter()

@router.post("/preguntas")
async def responder_pregunta(pregunta_id: int, parametros: dict, db: Session = Depends(get_db)):
    """
    Endpoint para manejar preguntas predefinidas.
    - pregunta_id: ID de la pregunta predefinida.
    - parametros: Diccionario con parámetros adicionales necesarios.
    """
    try:
        if pregunta_id == 1:  # ¿Cuántos pagos hemos realizado a una empresa específica?
            empresa = parametros.get("empresa")
            if not empresa:
                raise HTTPException(status_code=400, detail="Falta el parámetro 'empresa'")
            
            total_pagos = db.query(Pagos).filter(Pagos.empresa == empresa).count()
            return {"pregunta": "Total de pagos realizados", "respuesta": total_pagos}
        
        elif pregunta_id == 2:  # ¿Cuál es el saldo pendiente de una empresa?
            empresa = parametros.get("empresa")
            if not empresa:
                raise HTTPException(status_code=400, detail="Falta el parámetro 'empresa'")
            
            saldo_pendiente = db.query(Pagos).filter(
                Pagos.empresa == empresa,
                Pagos.estado == "pendiente"
            ).sum(Pagos.monto)
            return {"pregunta": "Saldo pendiente", "respuesta": saldo_pendiente}
        
        elif pregunta_id == 3:  # ¿Cuántos bienes tenemos registrados en el inventario?
            total_bienes = db.query(Inventario).count()
            return {"pregunta": "Total de bienes registrados", "respuesta": total_bienes}
        
        else:
            raise HTTPException(status_code=404, detail="Pregunta no encontrada")
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ocurrió un error: {e}")
