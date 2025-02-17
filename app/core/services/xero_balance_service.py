from typing import Dict
import httpx
from datetime import datetime
from fastapi import HTTPException
from app.core.config import settings

class XeroBalanceService:
    def __init__(self):
        self.api_url = "https://api.xero.com/api.xro/2.0"

    async def get_balance_between_orgs(
        self,
        access_token: str,
        from_org_id: str,
        to_org_id: str,
        start_date: str,
        end_date: str
    ) -> float:
        try:
            datetime.strptime(start_date, '%Y-%m-%d')
            datetime.strptime(end_date, '%Y-%m-%d')

            url = f"{self.api_url}/Reports/BalanceSheet"
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Accept": "application/json",
                "Xero-tenant-id": from_org_id,
                "Content-Type": "application/json"
            }

            print(f"=====> Consultando balance desde {start_date} hasta {end_date}...")
            start_balance = await self._get_balance_for_date(url, headers, start_date, to_org_id)
            end_balance = await self._get_balance_for_date(url, headers, end_date, to_org_id)
            print(f"Balance inicial: {start_balance}, Balance final: {end_balance}")

            return end_balance - start_balance
        except Exception as e:
            print(f"Error getting balance: {str(e)}")
            raise HTTPException(status_code=500, detail="Error al obtener el balance")

    async def _get_balance_for_date(self, url, headers, date: str, to_org_id: str) -> float:
        params = {"date": date}
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers, params=params)
            response.raise_for_status()
            balance_sheet = response.json()

        print(f"Datos recibidos para balance en {date}: {balance_sheet}")
        total_balance = 0.0
        sections = ["Non-Current Liabilities", "Current Liabilities", "Non-Current Assets", "Current Assets"]

        for section_name in sections:
            section = next(
                (s for s in balance_sheet.get("Reports", [{}])[0].get("Rows", []) if s.get("Title") == section_name), {}
            )
            for row in section.get("Rows", []):
                try:
                    cells = row.get("Cells", [])
                    if len(cells) > 1:
                        value = cells[1].get("Value", "0").replace(",", "")
                        balance = float(value)
                        if section_name in ["Non-Current Liabilities", "Current Liabilities"]:
                            balance = -balance
                        total_balance += balance
                        print(f"{section_name}: {row.get('Title')} -> {balance}")
                except (ValueError, IndexError):
                    continue

        print(f"Balance total en {date}: {total_balance}")
        return total_balance

    async def get_transactions_between_orgs(
    self,
    access_token: str,
    from_org_id: str,
    to_org_id: str,
    start_date: str,
    end_date: str
    ) -> Dict:
        try:
            url = f"{self.api_url}/BankTransactions"
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Accept": "application/json",
                "Xero-tenant-id": from_org_id
            }
            params = {"where": f"Date >= DateTime({start_date}) && Date <= DateTime({end_date})"}

            print(f"=====> Consultando transacciones desde {start_date} hasta {end_date}...")
            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=headers, params=params)
                response.raise_for_status()
                transactions = response.json().get("BankTransactions", [])

            print(f"=====> Transacciones obtenidas: {transactions}")

            for tx in transactions:
                print(f"=====> Fecha: {tx.get('Date')}, Monto: {tx.get('Total')}, Moneda: {tx.get('CurrencyCode')}")

            filtered_transactions = [
                tx for tx in transactions if any(to_org_id in line.get("Contact", {}).get("ContactID", "") for line in tx.get("LineItems", []))
            ]

            print(f"=====> Transacciones filtradas entre {from_org_id} y {to_org_id}: {filtered_transactions}")
            return {"transactions": filtered_transactions}
        except Exception as e:
            print(f"Error getting transactions: {str(e)}")
            raise HTTPException(status_code=500, detail="Error al obtener transacciones")

xero_balance_service = XeroBalanceService()
