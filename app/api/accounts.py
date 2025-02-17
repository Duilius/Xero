import httpx
from app.models.account_structures import get_account_balance
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.db.session import get_db
import json
from redis import Redis
from app.services.xero_api import xero_api,XeroOAuthService
#from app.services.xero_account_sync import XeroAccountStructure
from app.models.account_structures import XeroAccountStructure
from app.services.xero_auth_service import XeroAuthService
from app.codigos_internos_xero import get_xero_auth_service, XeroToken
from app.models.organization import Organization
from app.core.cache import redis  # Importar instancia Redis configurada
from app.services.xero_account_sync import XeroAccountService as AccountService

from app.models.xero_mapping import AccountMapping, AccountChange
#from app.services.xero_auth_service import XeroAuthService, get_xero_auth_service
from app.models.xero_token import XeroToken

router = APIRouter()

# api/accounts.py

@router.get("/api/accounts/list")
async def list_accounts(
   db: Session = Depends(get_db)
):
   accounts = db.query(XeroAccountStructure).all()
   return [
       {
           "id": acc.account_id,
           "code": acc.code,
           "name": acc.name,
           "type": acc.type,
           "report_type": acc.report_type
       }
       for acc in accounts
   ]

@router.get("/api/accounts/balance/{from_org_id}/{to_org_id}")
async def get_cross_balance(
   from_org_id: int,
   to_org_id: int,
   account_id: str = Query(...),
   db: Session = Depends(get_db),
   xero_auth_service: XeroAuthService = Depends(get_xero_auth_service)
):
   cache_key = f"balance:{from_org_id}:{to_org_id}:{account_id}"
   
   # Check cache
   cached = await redis.get(cache_key)
   if cached:
       return json.loads(cached)
   
   # Get fresh data from Xero
   token = db.query(XeroToken).filter(XeroToken.organization_id == from_org_id).first()
   balance = await xero_auth_service.get_account_balance(
       token.tenant_id,
       token.access_token,
       account_id
   )
   
   # Cache result
   await redis.set(cache_key, json.dumps(balance), ex=7200)
   
   return balance

@router.get("/api/organizations/list")
async def list_organizations(
   db: Session = Depends(get_db)
):
   orgs = db.query(Organization).filter(Organization.status == 'ACTIVE').all()
   return [
       {
           "id": org.id,
           "name": org.name
       }
       for org in orgs
   ]

#************************  ANTIGUO, LO USABA EN EL MODAL DE AJUSTES *****************************
# api/accounts.py
@router.get("/accounts/balance/{org_id}/{account_id}")
async def get_balance(
    org_id: int,
    account_id: str,
    db: Session = Depends(get_db)
):
    balance = await get_account_balance(org_id, account_id)
    return {"balance": balance}


# ************************ SINCRONIZAR EL MAPEO DE CUENTAS ****************************************
# accounts.py - Corregir endpoint
@router.get("/sync/{tenant_id}")
async def sync_accounts(tenant_id: str, xero_auth_service: XeroAuthService = Depends(),db: Session = Depends(get_db)):
    try:
        service = AccountService()  # Usar con alias para verificar
        print(">>> 👉 account.py >>> TENANT ID ==========> ",tenant_id)

        # Obtener y verificar token para este tenant
        token_entry = db.query(XeroToken).filter_by(tenant_id=tenant_id).first()
        if not token_entry:
           raise HTTPException(status_code=404, detail="Token not found")
       
        # Refrescar token si es necesario
        token = await xero_auth_service.refresh_token_if_needed(token_entry, db)

        print(">>> 👉 account.py >>> RESULTADO DEL FILTRO ====> ", token.organization_id)
        account_service = service
        await account_service.sync_account_structure(db=db, org_id = token.organization_id, tenant_id = token.tenant_id, access_token= token.access_token)
        
        return {"status": "success"}
    except Exception as e:
        print(f"Sync error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# En xero_account_sync.py verificar que sync_account_structure está definido y correctamente indentado


# **********************  Agregar get_xero_account_structure al servicio  **********************************

# Agregar get_xero_account_structure al servicio
class XeroAccountService:
    async def get_xero_account_structure(self, tenant_id: str, access_token: str):
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://api.xero.com/api.xro/2.0/Accounts",
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Xero-tenant-id": tenant_id
                }
            )
            return response.json() if response.status_code == 200 else None
        

