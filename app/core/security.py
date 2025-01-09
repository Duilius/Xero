from datetime import datetime, timedelta
from typing import Optional
import jwt
from fastapi import HTTPException, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from app.core.config import settings

class SecurityManager:
    security = HTTPBearer()
    secret_key = settings.SECRET_KEY
    algorithm = "HS256"
    
    @classmethod
    def create_access_token(cls, user_id: int, tenant_ids: list[str]) -> str:
        """Create JWT access token."""
        payload = {
            'exp': datetime.utcnow() + timedelta(days=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
            'iat': datetime.utcnow(),
            'sub': str(user_id),
            'tenant_ids': tenant_ids
        }
        return jwt.encode(payload, cls.secret_key, algorithm=cls.algorithm)

    @classmethod
    def decode_token(cls, token: str) -> dict:
        """Decode JWT token."""
        try:
            payload = jwt.decode(token, cls.secret_key, algorithms=[cls.algorithm])
            if datetime.fromtimestamp(payload['exp']) < datetime.utcnow():
                raise HTTPException(status_code=401, detail="Token has expired")
            return payload
        except jwt.InvalidTokenError:
            raise HTTPException(status_code=401, detail="Invalid token")

    @classmethod
    async def get_current_user(cls, credentials: HTTPAuthorizationCredentials = Security(security)) -> dict:
        """Get current user from JWT token."""
        return cls.decode_token(credentials.credentials)

security_manager = SecurityManager()