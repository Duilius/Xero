# services/xero_balance_service.py
import asyncio
import httpx
from typing import Dict, Optional, List
from datetime import datetime
from sqlalchemy.orm import Session
from app.services.xero_auth_service import XeroAuthService
from fastapi import FastAPI, APIRouter, Depends, HTTPException, Header
from app.db.session import get_db
import json
from app.models.xero_token import XeroToken
from app.models.xero_mapping import AccountMapping
import requests
import os
from app.db.database import SessionLocal

router = APIRouter()
app = FastAPI()

# Configuración de Xero
XERO_API_BASE = "https://api.xero.com/api.xro/2.0"
XERO_ACCESS_TOKEN = os.getenv("XERO_ACCESS_TOKEN")  # Debes manejar OAuth
HEADERS = {
    "Authorization": f"Bearer {XERO_ACCESS_TOKEN}",
    "Accept": "application/json",
}

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/xero/balance-sheet/{organization_id}")
def get_filtered_balance_sheet(organization_id: int, db: Session = Depends(get_db)):
    """
    Obtiene el balance filtrado para una organización.
    """
    # 1️⃣ Obtener los `account_id` desde nuestra BD
    account_mappings = db.query(AccountMapping.account_code, AccountMapping.account_id) \
                         .filter(AccountMapping.organization_id == organization_id).all()
    account_lookup = {m.account_id: m.account_code for m in account_mappings}

    if not account_lookup:
        raise HTTPException(status_code=404, detail="No se encontraron cuentas para esta organización.")

    # 2️⃣ Llamar a la API de Xero (Balance Sheet)
    response = requests.get(f"{XERO_API_BASE}/Reports/BalanceSheet", headers=HEADERS)
    
    if response.status_code != 200:
        raise HTTPException(status_code=500, detail=f"Error en Xero: {response.text}")

    balance_data = response.json()

    # 3️⃣ Filtrar solo las cuentas que tenemos en la BD
    filtered_rows = []
    for row in balance_data.get("Reports", [{}])[0].get("Rows", []):
        if row.get("RowType") == "Row":
            for cell in row.get("Cells", []):
                for attr in cell.get("Attributes", []):
                    if attr["Id"] == "account" and attr["Value"] in account_lookup:
                        filtered_rows.append(row)
                        break  # Evitamos procesar más celdas de la misma fila

    return {"organization_id": organization_id, "filtered_balance": filtered_rows}

@app.get("/xero/account-details/{account_id}")
def get_account_details(account_id: str):
    """
    Obtiene los detalles de una cuenta específica desde Xero.
    """
    response = requests.get(f"{XERO_API_BASE}/Accounts/{account_id}", headers=HEADERS)

    if response.status_code != 200:
        raise HTTPException(status_code=500, detail=f"Error en Xero: {response.text}")

    return response.json()


@router.post("/xero/balance-sheet")
async def get_balance_sheet(
    payload: dict,
    xero_tenant_id: str = Header(..., alias="Xero-tenant-id"),
    xero_auth_service: XeroAuthService = Depends(),
    db: Session = Depends(get_db)
):
    """
    Endpoint para obtener los saldos de múltiples cuentas en múltiples empresas desde Xero.

    Parámetros en `payload`:
    - `date` (str): La fecha del balance.
    - `account_pairs` (list): Lista de diccionarios con `tenant_id` y `account_code`.

    Ejemplo de `payload`:
    {
        "date": "2024-12-31",
        "account_pairs": [
            {"tenant_id": "abc123", "account_code": "100"},
            {"tenant_id": "xyz789", "account_code": "200"}
        ]
    }
    """
    try:
        date = payload.get("date")
        account_pairs = payload.get("account_pairs", [])

        print(f"😍Processing request for tenant: {xero_tenant_id}, date: {date}, accounts: {account_pairs}")

        # Obtener token
        token_entry = db.query(XeroToken).filter_by(tenant_id=xero_tenant_id).first()
        if not token_entry:
            print(f"😋No token found for tenant: {xero_tenant_id}")
            raise HTTPException(status_code=404, detail="Token not found")

        # Refrescar token si es necesario
        token = await xero_auth_service.refresh_token_if_needed(token_entry, db)

        async with httpx.AsyncClient() as client:
            headers = {
                "Authorization": f"Bearer {token_entry.access_token}",
                "Xero-tenant-id": xero_tenant_id,
                "Accept": "application/json"
            }

            response = await client.get(
                "https://api.xero.com/api.xro/2.0/Reports/BalanceSheet",
                headers=headers,
                params={"date": date}
            )

            print(f"😛Response Status: {response.status_code}")

            if response.status_code == 200:
                data = response.json()
                
                # 🔍 LOG: Imprimir estructura del JSON recibido
                print(f"😝Xero Response Structure: {json.dumps(data, indent=2)[:2000]}...")  # Limitamos a 2000 caracteres
                
                return data
            else:
                error_detail = f"Error from Xero API: {response.text}"
                print(error_detail)
                raise HTTPException(status_code=response.status_code, detail=error_detail)

    except Exception as e:
        error_msg = f"ERROR in get_balance_sheet: {str(e)}"
        print(error_msg)
        raise HTTPException(status_code=500, detail=error_msg)



def extract_balance(data, account_code):
    """Busca el saldo de la cuenta en el reporte de BalanceSheet de Xero."""
    try:
        report = data.get("Reports", [{}])[0]
        for section in report.get("Rows", []):
            if "Rows" in section:
                for row in section["Rows"]:
                    if row.get("Cells") and row["Cells"][0]["Value"].startswith(account_code):
                        balance_str = row["Cells"][1]["Value"]
                        return float(balance_str.replace(",", "").replace("$", ""))
    except Exception:
        pass
    return None

""" LO SIGUIENTE ES POSIBLE QUE NO SE USE Y/O NO LO NECESITE
"""

def extract_balance_from_report(data: dict, account_code: str) -> float:
    """Extraer el saldo de una cuenta específica del reporte de Balance Sheet"""
    try:
        for section in data.get("Reports", [{}])[0].get("Rows", []):
            for row in section.get("Rows", []):
                if row.get("Cells", [{}])[0].get("Value", "").startswith(account_code):
                    balance_str = row.get("Cells", [{}])[1].get("Value", "0")
                    return float(balance_str.replace(",", "").replace("$", ""))

    except Exception as e:
        print(f"Error extrayendo balance para {account_code}: {e}")
    
    return 0.0

async def fetch_account_balance(url: str, headers: Dict, account_code: str, date: str) -> float:
    """Consulta Xero para obtener el saldo de una cuenta en una fecha específica."""
    params = {"date": date}
    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=headers, params=params)
        if response.status_code != 200:
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Error from Xero API: {response.text}"
            )
        
        data = response.json()
        
        # Buscar la cuenta y su saldo
        for section in data.get("Reports", [{}])[0].get("Rows", []):
            for row in section.get("Rows", []):
                if row.get("Cells", [{}])[0].get("Value", "").startswith(account_code):
                    balance_str = row.get("Cells", [{}])[1].get("Value", "0")
                    # Remover formato de moneda y convertir a número
                    try:
                        return float(balance_str.replace(",", ""))
                    except ValueError:
                        return None  # Indica que no hay datos
        
        return None  # Indica que no se encontró la cuenta








#****** USADO ANTERIORMENTE ****************** USADO ANTERIORMENTE****** USADO ANTERIORMENTE****** USADO ANTERIORMENTE
class XeroBalanceService:
    async def get_account_balance(
        self,
        tenant_id: str,
        access_token: str,
        account_id: str
    ) -> Dict:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"https://api.xero.com/api.xro/2.0/Reports/BalanceSheet",
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Xero-tenant-id": tenant_id,
                    "Accept": "application/json"
                },
                params={
                    "accountID": account_id,
                    "date": datetime.now().strftime("%Y-%m-%d")
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                return self._extract_balance(data, account_id)
            return None
    
    def _extract_balance(self, data: Dict, account_id: str) -> Optional[float]:
        # Implementar lógica de extracción según estructura de respuesta Xero
        pass

    async def get_account_balances_by_period(
        self,
        tenant_id: str,
        access_token: str,
        account_id: str,
        from_date: str,
        to_date: str
    ):
        # Obtener saldos por período
        pass

    async def get_comparative_balances(
        self,
        org_ids: List[int],
        account_id: str,
        period: str
    ):
        # Matriz comparativa con variaciones
        pass