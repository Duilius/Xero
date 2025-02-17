# api/xero.py
import httpx
from fastapi import APIRouter, Depends, HTTPException
import xero_python
from xero_python.api_client import ApiClient
from xero_python.api_client.configuration import Configuration
from xero_python.api_client.oauth2 import OAuth2Token

router = APIRouter()

# En app/services/xero_service.py o donde tengas tus servicios Xero
class XeroService:
   async def get_organization_details(self, access_token: str, tenant_id: str):
       """Obtiene detalles de la organización desde la API de Xero"""
       url = "https://api.xero.com/api.xro/2.0/Organisation"
       headers = {
           "Authorization": f"Bearer {access_token}",
           "Xero-tenant-id": tenant_id,
           "Accept": "application/json"
       }
       
       async with httpx.AsyncClient() as client:
           response = await client.get(url, headers=headers)
           response.raise_for_status()
           data = response.json()
           return data["Organisations"][0]  # Retorna la primera organización

xero_service = XeroService()