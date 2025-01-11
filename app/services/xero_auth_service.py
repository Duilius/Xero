from datetime import datetime, timezone
from typing import Dict, List, Optional
import httpx
import json
from datetime import datetime, timedelta, timezone
#import jwt as pyjwt
from jose import jwt
from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.core.config import settings
from app.models.user import User, UserRole, UserStatus
from app.models.organization import Organization, OrganizationUser, OrganizationStatus, SubscriptionType
from app.models.xero_token import XeroToken
#from app.services.xero_oauth import xero_oauth_service
from app.services.xero_oauth_service import xero_oauth_service

from app.core.security import security_manager


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

            # Preparar datos de sesión mejorados
            session_data = {
                "user_info": {
                    "id": user.id,
                    "name": f"{user.first_name} {user.last_name}",
                    "email": user.email
                },
                "organizations": {
                    "connections": [
                        {
                            "tenant_id": conn["tenantId"],
                            "name": conn["tenantName"],
                            "status": "connected",
                            "last_sync": datetime.now(timezone.utc).isoformat()
                        } 
                        for conn in tenant_connections
                    ],
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            }

            # Create session token con datos mejorados
            session_token = self._create_session_token(
                user.id, 
                tenant_ids,
                session_data  # Pasar los datos adicionales
            )

            return {
                "token": session_token,  # Cambiado de "access_token" a "token"
                "user": {
                    "id": user.id,
                    "email": user.email,
                    "name": f"{user.first_name} {user.last_name}"
                },
                "organizations": session_data["organizations"]  # Incluir organizaciones en la respuesta
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
            
            user_info = response.json()
        
            # DEBUG: Imprimir la estructura de la respuesta
            print("Xero User Info Response:", json.dumps(user_info, indent=2))
                
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

        try:
            user = db.query(User).filter(User.email == email).first()
            current_time = datetime.now(timezone.utc)
            
            if user:
                # Update existing user
                user.first_name = user_info.get("given_name", user.first_name)
                user.last_name = user_info.get("family_name", user.last_name)
                user.xero_roles = user_info
                user.email_verified = True
                user.email_verified_at = current_time
                user.last_login_at = current_time
                user.updated_at = current_time
            else:
                # Create new user
                import secrets
                temp_password = secrets.token_hex(16)
                from passlib.hash import bcrypt
                password_hash = bcrypt.hash(temp_password)
                
                # Determinar rol y asegurarnos de que sea mayúsculas
                assigned_role = self._determine_role_from_xero(user_info)
                print(f"Tipo de rol asignado: {type(assigned_role)}")  # Debug
                print(f"Valor de rol asignado: {assigned_role.value}")  # Debug
                
                user = User(
                    email=email,
                    password_hash=password_hash,
                    first_name=user_info.get("given_name", ""),
                    last_name=user_info.get("family_name", ""),
                    role=assigned_role.value,  # Usamos .value explícitamente
                    status=UserStatus.ACTIVE.value,  # También usamos .value aquí
                    xero_roles=user_info,
                    email_verified=True,
                    email_verified_at=current_time,
                    last_login_at=current_time,
                    created_at=current_time,
                    updated_at=current_time
                )
                db.add(user)

            db.commit()
            db.refresh(user)
            return user
            
        except Exception as e:
            print(f"Error en _create_or_update_user: {str(e)}")
            print(f"Tipo de error: {type(e)}")
            import traceback
            print(traceback.format_exc())
            raise

    def _determine_role_from_xero(self, user_info: Dict) -> UserRole:
        """Determine user role based on Xero information."""
        email = user_info.get("email", "").lower()
        print(f"Determinando rol para email: {email}")  # Debug log
        
        # Verificar si es admin
        if email in settings.ADMIN_EMAILS:
            print(f"Email {email} encontrado en ADMIN_EMAILS")  # Debug log
            return UserRole.ADMIN
        
        # Por defecto, asignar rol de contador
        print(f"Asignando rol ACCOUNTANT por defecto")  # Debug log
        return UserRole.ACCOUNTANT

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
        # Generar un slug único
        slug = tenant_id
        
        # Buscar organización existente
        organization = db.query(Organization).filter(Organization.slug == slug).first()
        
        if not organization:
            # Usar datetime actual en vez de now()
            current_time = datetime.now(timezone.utc)
            
            organization = Organization(
                name=tenant_name,
                slug=slug,
                status=OrganizationStatus.ACTIVE,
                subscription_type=SubscriptionType.TRIAL,
                created_at=current_time,
                updated_at=current_time
            )
            db.add(organization)
            db.commit()
            db.refresh(organization)
        
        return organization

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
            current_time = datetime.now(timezone.utc)
            org_user = OrganizationUser(
                organization_id=organization_id,
                user_id=user_id,
                created_at=current_time,
                updated_at=current_time
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
        current_time = datetime.now(timezone.utc)
        token_expires_at = current_time + timedelta(seconds=token_data.get('expires_in', 1800))
        
        # Buscar el tenant_name en los datos de conexión o usar un valor por defecto
        tenant = db.query(XeroToken).filter(
            XeroToken.organization_id == organization_id,
            XeroToken.tenant_id == tenant_id
        ).first()
        
        if tenant:
            # Actualizar token existente
            tenant.access_token = token_data.get('access_token')
            tenant.refresh_token = token_data.get('refresh_token')
            tenant.token_expires_at = token_expires_at
            tenant.updated_at = current_time
        else:
            # Crear nuevo token
            token = XeroToken(
                organization_id=organization_id,
                tenant_id=tenant_id,
                tenant_name=token_data.get('tenant_name', 'Default Tenant'),  # Valor por defecto
                access_token=token_data.get('access_token'),
                refresh_token=token_data.get('refresh_token'),
                token_expires_at=token_expires_at,
                created_at=current_time,
                updated_at=current_time
            )
            db.add(token)
        
        db.commit()

    def _create_session_token(
        self, 
        user_id: int, 
        tenant_ids: List[str], 
        session_data: Dict
    ) -> str:
        """Create a session token with enhanced data."""
        payload = {
            "user_id": user_id,
            "tenant_ids": tenant_ids,
            "session_data": session_data,
            "exp": datetime.now(timezone.utc) + timedelta(
                minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
            )
        }
        
        return jwt.encode(
            payload,
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
        
    async def process_auth_data(
        self,
        db: Session,
        user_info: Dict,
        token_data: Dict,
        tenants: List[Dict]
    ) -> Dict:
        """Procesa los datos de autenticación de Xero."""
        try:
            # 1. Crear o actualizar usuario
            user = self._create_or_update_user(db, user_info)
            
            # 2. Procesar cada tenant/organización
            tenant_ids = []
            for tenant in tenants:
                org = self._create_or_update_organization(db, tenant)
                self._ensure_organization_user(db, org.id, user.id)
                self._save_tokens(
                    db=db,
                    organization_id=org.id,
                    tenant_id=tenant["tenantId"],
                    token_data=token_data
                )
                tenant_ids.append(tenant["tenantId"])
            
            # 3. Crear token de sesión
            session_token = security_manager.create_access_token(
                user_id=user.id,
                tenant_ids=tenant_ids
            )
            
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
                detail=f"Error processing auth data: {str(e)}"
            )
        

xero_auth_service = XeroAuthService()