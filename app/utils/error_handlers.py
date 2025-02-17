from typing import Optional, Dict
from fastapi import HTTPException, Response

async def handle_xero_error(response: Response) -> Optional[Dict]:
    """
    Maneja errores comunes de la API de Xero.
    
    Args:
        response (Response): Respuesta de la API de Xero
        
    Returns:
        Optional[Dict]: None si no hay error, o lanza HTTPException
    
    Raises:
        HTTPException: Con el código y mensaje de error apropiado
    """
    if response.status_code == 401:
        raise HTTPException(
            status_code=401, 
            detail="Token expired"
        )
    elif response.status_code == 429:
        raise HTTPException(
            status_code=429, 
            detail="Rate limit exceeded"
        )
    elif response.status_code >= 400:
        raise HTTPException(
            status_code=response.status_code,
            detail=f"Xero API error: {response.text}"
        )
    return None