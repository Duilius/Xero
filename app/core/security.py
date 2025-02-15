from datetime import datetime, timedelta, timezone
from typing import Optional
#import jwt
from jwt import PyJWT

#from jose import jwt as pyjose
from fastapi import HTTPException, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from app.core.config import settings

class SecurityManager:
    jwt_manager = PyJWT()  # Hazlo una variable de clase en lugar de instancia
    security = HTTPBearer()
    secret_key = settings.SECRET_KEY
    algorithm = "HS256"

    
    @classmethod
    def create_access_token(cls, user_id: int, tenant_ids: list[str]) -> str:
        """Create JWT access token."""
        payload = {
            'exp': datetime.now(timezone.utc) + timedelta(days=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
            'iat': datetime.now(timezone.utc),
            'sub': str(user_id),
            'tenant_ids': tenant_ids
        }
        return cls.jwt_manager.encode(payload, cls.secret_key, algorithm=cls.algorithm)

    @classmethod
    def decode_token(self, token: str):
        jwt_decoder = PyJWT()
        try:
            print("Starting token decode...")
            payload = jwt_decoder.decode(token, self.secret_key, algorithms=["HS256"])
            print("Decoded payload:", payload)
            return payload
        except Exception as e:
            print(f"Token decode error: {str(e)}")
            raise
    
    @classmethod
    async def get_current_user(cls, credentials: HTTPAuthorizationCredentials = Security(security)) -> dict:
        """Get current user from JWT token."""
        return cls.decode_token(credentials.credentials)

security_manager = SecurityManager()