from datetime import datetime, timedelta
from fastapi import HTTPException
from sqlalchemy.orm import Session
import httpx
from app.core.config import settings
from app.models.xero_token import XeroToken
from datetime import datetime, timedelta, timezone
import jwt
from typing import Dict, List, Optional
from jwt.exceptions import ExpiredSignatureError, InvalidTokenError

# En app/core/services/xero_auth_service.py
class XeroAuthService:

    def __init__(self):
        self.jwt = jwt
        self.secret_key = settings.SECRET_KEY

    def decode_session_token(self, token: str) -> Dict:
       try:
           payload = self.jwt.decode(
               token,
               self.secret_key,
               algorithms=["HS256"]
           )
           return payload
       except ExpiredSignatureError:
           raise HTTPException(
               status_code=401,
               detail="Token has expired"
           )
       except InvalidTokenError:
           raise HTTPException(
               status_code=401,
               detail="Invalid token"
           )

    def encode_session_token(self, data: Dict) -> str:
        """Encode data into a JWT token."""
        try:
            token = self.jwt.encode(
                data,
                self.secret_key,
                algorithm="HS256"
            )
            return token
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error encoding token: {str(e)}"
            )

    async def refresh_token_if_needed(self, token: XeroToken, db: Session) -> XeroToken:
        """
        Verifica y actualiza el token si está expirado o próximo a expirar
        """
        
        print("Starting refresh_token_if_needed...")  # Debug
        now = datetime.now(timezone.utc)  # En lugar de utcnow()

        if not token:
            print("Token is None")  # Debug
            raise HTTPException(401, "No token found")
        

        print(f"Token expires_at: {token.token_expires_at}")  # Debug
        # Actualizar si expira en menos de 5 minutos
        if not token.token_expires_at or (token.token_expires_at - now).total_seconds() < 300:
            print("Token needs refresh")  # Debug
            try:
                new_token = await self.refresh_token(token.refresh_token)
                
                # Actualizar en DB
                token.access_token = new_token["access_token"]
                token.refresh_token = new_token["refresh_token"]
                token.token_expires_at = datetime.now(timezone.utc) + timedelta(seconds=new_token["expires_in"])
                token.updated_at = datetime.now(timezone.utc)
                
                db.commit()
                
            except Exception as e:
                print(f"Error refreshing token: {e}")
                # Redirigir a login si falla la actualización
                raise HTTPException(
                    status_code=401,
                    detail="Session expired. Please login again."
                )
        
        return token

    async def refresh_token(self, refresh_token: str) -> dict:
        """
        Obtiene un nuevo token usando el refresh_token
        """
        data = {
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
            "client_id": settings.XERO_CLIENT_ID,
            "client_secret": settings.XERO_CLIENT_SECRET
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://identity.xero.com/connect/token",
                data=data
            )
            response.raise_for_status()
            return response.json()

xero_auth_service = XeroAuthService()