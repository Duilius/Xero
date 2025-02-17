from app.core.cache import redis  # Importar instancia Redis configurada
from app.services.xero_api import XeroAPI  # Importar servicio Xero configurado
import json

xero_api = XeroAPI()

async def get_account_balance(org_id: str, account_id: str):
   cache_key = f"balance:{org_id}:{account_id}"
   balance = await redis.get(cache_key)
   if balance:
       return json.loads(balance)
       
   balance = await xero_api.get_balance(org_id, account_id)
   await redis.set(cache_key, json.dumps(balance), ex=7200)
   return balance