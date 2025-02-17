# app/services/xero_api.py
from app.services.xero_oauth_service import XeroOAuthService
import httpx

class XeroAPI:
   def __init__(self):
       self.auth_service = XeroOAuthService()
   
   async def get_balance(self, org_id: str, account_id: str) -> float:
       token = await self.auth_service.get_valid_token(org_id)
       async with httpx.AsyncClient() as client:
           response = await client.get(
               "https://api.xero.com/api.xro/2.0/Reports/BalanceSheet",
               headers={
                   "Authorization": f"Bearer {token}",
                   "Xero-tenant-id": org_id
               }
           )
           if response.status_code == 200:
               # Extraer balance del reporte
               data = response.json()
               return self._extract_balance(data, account_id)
           return 0.0

xero_api = XeroAPI()  # Instancia singleton