from typing import Dict, List, Optional
import httpx
from datetime import datetime, timedelta
import jwt
from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.core.config import settings
from app.models.user import User
from app.models.organization import Organization, OrganizationUser
from app.models.xero_token import XeroToken
from app.services.xero_oauth import xero_oauth_service

class XeroAuthService:
    def __init__(self):
        self.userinfo_url = "https://identity.xero.com/connect/userinfo"
        self.connections_url = "https://api.xero.com/connections"
        self.secret_key = settings.SECRET_KEY

    async def handle_oauth_callback(self, db: Session, code: str) -> Dict:
        """Handle the OAuth callback process comprehensively."""
        try:
            # Exchange code for tokens
            token_data = await xero_oauth_service.exchange_code_for_tokens(code)
            access_token = token_data["access_token"]

            # Get user info from Xero
            user_info = await self._get_user_info(access_token)
            
            # Create or update user
            user = await self._create_or_update_user(db, user_info)
            
            # Get Xero tenant connections
            tenant_connections = await self._get_tenant_connections(access_token)
            
            # Process each tenant connection
            tenant_ids = await self._process_tenant_connections(
                db, user.id, tenant_connections, token_data
            )

            # Create session token
            session_token = self._create_session_token(user.id, tenant_ids)

            return {
                "access_token": session_token,
                "user": {
                    "id": user.id,
                    "email": user.email,
                    "name": f"{user.first_name} {user.last_name}"
                }
            }

        except Exception as e:
            raise HTTPException(
                status_code=400,
                detail=f"OAuth callback failed: {str(e)}"
            )

    async def _get_user_info(self, access_token: str) -> Dict:
        """Get user information from Xero."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                self.userinfo_url,
                headers={"Authorization": f"Bearer {access_token}"}
            )
            
            if response.status_code != 200:
                raise HTTPException(
                    status_code=400,
                    detail="Failed to get user info from Xero"
                )
                
            return response.json()

    async def _get_tenant_connections(self, access_token: str) -> List[Dict]:
        """Get all tenant connections from Xero."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                self.connections_url,
                headers={"Authorization": f"Bearer {access_token}"}
            )
            
            if response.status_code != 200:
                raise HTTPException(
                    status_code=400,
                    detail="Failed to get tenant connections"
                )
                
            return response.json()

    async def _create_or_update_user(self, db: Session, user_info: Dict) -> User:
        """Create or update user from Xero information."""
        email = user_info.get("email")
        if not email:
            raise HTTPException(
                status_code=400,
                detail="No email provided by Xero"
            )

        user = db.query(User).filter(User.email == email).first()
        
        if user:
            # Update existing user
            user.first_name = user_info.get("given_name", user.first_name)
            user.last_name = user_info.get("family_name", user.last_name)
            user.email_verified = True
            user.email_verified_at = datetime.utcnow()
            user.last_login_at = datetime.utcnow()
        else:
            # Create new user
            user = User(
                email=email,
                first_name=user_info.get("given_name", ""),
                last_name=user_info.get("family_name", ""),
                role="user",
                status="active",
                email_verified=True,
                email_verified_at=datetime.utcnow(),
                last_login_at=datetime.utcnow()
            )
            db.add(user)

        db.commit()
        db.refresh(user)
        return user

    async def _process_tenant_connections(
        self,
        db: Session,
        user_id: int,
        tenant_connections: List[Dict],
        token_data: Dict
    ) -> List[str]:
        """Process and store tenant connections."""
        tenant_ids = []
        
        for connection in tenant_connections:
            tenant_id = connection["tenantId"]
            tenant_name = connection["tenantName"]
            
            # Create or update organization
            org = self._get_or_create_organization(db, tenant_id, tenant_name)
            
            # Create or update organization user relationship
            self._ensure_organization_user(db, org.id, user_id)
            
            # Save tokens
            self._save_tokens(
                db=db,
                organization_id=org.id,
                tenant_id=tenant_id,
                token_data=token_data
            )
            
            tenant_ids.append(tenant_id)
            
        return tenant_ids

    def _get_or_create_organization(
        self,
        db: Session,
        tenant_id: str,
        tenant_name: str
    ) -> Organization:
        """Get or create an organization."""
        org = db.query(Organization).filter(
            Organization.slug == tenant_id
        ).first()
        
        if not org:
            org = Organization(
                name=tenant_name,
                slug=tenant_id,
                status="active"
            )
            db.add(org)
            db.commit()
            db.refresh(org)
            
        return org

    def _ensure_organization_user(
        self,
        db: Session,
        organization_id: int,
        user_id: int
    ) -> None:
        """Ensure user is connected to organization."""
        org_user = db.query(OrganizationUser).filter(
            OrganizationUser.organization_id == organization_id,
            OrganizationUser.user_id == user_id
        ).first()
        
        if not org_user:
            org_user = OrganizationUser(
                organization_id=organization_id,
                user_id=user_id,
                role="member"
            )
            db.add(org_user)
            db.commit()

    def _save_tokens(
        self,
        db: Session,
        organization_id: int,
        tenant_id: str,
        token_data: Dict
    ) -> None:
        """Save or update tokens for a tenant."""
        token = db.query(XeroToken).filter(
            XeroToken.organization_id == organization_id,
            XeroToken.tenant_id == tenant_id
        ).first()
        
        if not token:
            token = XeroToken(
                organization_id=organization_id,
                tenant_id=tenant_id
            )
            db.add(token)
        
        token.access_token = token_data["access_token"]
        token.refresh_token = token_data["refresh_token"]
        token.token_expires_at = datetime.utcnow() + timedelta(seconds=token_data["expires_in"])
        
        db.commit()

    def _create_session_token(self, user_id: int, tenant_ids: List[str]) -> str:
        """Create a session token."""
        return jwt.encode(
            {
                "sub": str(user_id),
                "tenant_ids": tenant_ids,
                "exp": datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
            },
            self.secret_key,
            algorithm="HS256"
        )

    def decode_session_token(self, token: str) -> Dict:
        """Decode and validate a session token."""
        try:
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=["HS256"]
            )
            return payload
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=401,
                detail="Token has expired"
            )
        except jwt.InvalidTokenError:
            raise HTTPException(
                status_code=401,
                detail="Invalid token"
            )

xero_auth_service = XeroAuthService()