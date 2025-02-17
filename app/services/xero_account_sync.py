# services/xero_account_sync.py
from sqlalchemy.sql import func
from typing import Dict, List
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from app.models.account_structures import XeroAccountStructure
from app.codigos_internos_xero import get_xero_account_structure
from app.models.xero_mapping import AccountMapping, AccountChange
from datetime import datetime, timezone
import httpx
from fastapi import HTTPException
import json

class XeroAccountService:
    def __init__(self):
        # Timeout más estricto y limits para controlar conexiones
        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(10.0, connect=5.0),
            limits=httpx.Limits(max_keepalive_connections=5, max_connections=10)
        )
        print(">>>> 👉 XeroAccountService initialized with strict timeouts <<<<<< ")

    async def get_xero_account_structure(self, tenant_id: str, access_token: str):
        try:
            # Usar with para asegurar que la conexión se cierre
            async with httpx.AsyncClient(timeout=httpx.Timeout(10.0)) as client:
                response = await client.get(
                    "https://api.xero.com/api.xro/2.0/Accounts",
                    headers={
                        "Authorization": f"Bearer {access_token}",
                        "Xero-tenant-id": tenant_id,
                        "Accept": "application/json"
                    }
                )
                print(f">>> 👉Response status for tenant {tenant_id}: {response.status_code}")
                return response.json() if response.status_code == 200 else None

        except httpx.TimeoutException:
            print(f">>> 👉Timeout reached for tenant {tenant_id}")
            return None
        except Exception as e:
            print(f">>> 👉 Error: {str(e)}")
            return None

    async def sync_account_structure(self, db: Session, org_id: int, tenant_id: str, access_token: str):
        print(f">>> 👉Starting sync for tenant {tenant_id}")
        try:
            accounts = await self.get_xero_account_structure(tenant_id, access_token)
            if not accounts or 'Accounts' not in accounts:
                print(">>> 👉No accounts data received")
                return

            sync_time = datetime.utcnow()
            for account in accounts['Accounts']:
                try:
                    mapping = await self.update_mapping(db, org_id, account, sync_time)
                    if not mapping:
                        continue
                except Exception as e:
                    print(f">>> 👉Error processing account: {str(e)}")
                    continue

            db.commit()
            print(f">>> 👉Sync completed for tenant {tenant_id}")

        except Exception as e:
            print(f">>> 👉Sync failed: {str(e)}")
            db.rollback()

    async def update_mapping(self, db: Session, org_id: int, account: dict, sync_time: datetime) -> AccountMapping:
        """Actualiza o crea un mapeo de cuenta"""
        existing = db.query(AccountMapping).filter(
            AccountMapping.organization_id == org_id,
            AccountMapping.account_id == account['AccountID']
        ).first()

        if existing:
            # Si el código ha cambiado, registrar el cambio
            if existing.account_code != account['Code']:
                self.log_change(db, existing, 'CODE_CHANGE', existing.account_code, account['Code'])
            
            # Actualizar registro existente
            existing.account_code = account['Code']
            existing.account_name = account['Name']
            existing.account_type = account['Type']
            existing.updated_at = sync_time
        else:
            # Crear nuevo registro
            existing = AccountMapping(
                organization_id=org_id,
                account_id=account['AccountID'],
                account_code=account['Code'],
                account_name=account['Name'],
                account_type=account['Type'],
                created_at=sync_time,
                updated_at=sync_time
            )
            db.add(existing)

        try:
            db.commit()
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=f"Error updating account mapping: {str(e)}")

        return existing

    def log_special_chars(account_data):
        for key, value in account_data.items():
            if isinstance(value, str) and any(ord(c) > 127 for c in value):
                print(f">>> 👉Campo {key}: Raw={value}, Unicode={value.encode('unicode_escape')}")     


    async def update_structure(self, db: Session, org_id: int, account: dict) -> XeroAccountStructure:
        """
        Actualiza o crea una estructura de cuenta de Xero evitando duplicados.
        """
        try:
            # Buscar registro existente usando una combinación única de campos
            existing = db.query(XeroAccountStructure).filter(
                and_(
                    XeroAccountStructure.organization_id == org_id,
                    XeroAccountStructure.account_id == account['AccountID']
                )
            ).first()

            current_time = datetime.now(timezone.utc)

            if existing:
                # Actualizar el registro existente
                updates = {
                    'code': account['Code'],
                    'name': account['Name'],
                    'type': account['Type'],
                    'report_type': 'BS' if account['Type'] in ['ASSET', 'LIABILITY', 'EQUITY'] else 'PL',
                    'last_sync': current_time
                }
                
                # Verificar si hay cambios reales antes de actualizar
                if any(getattr(existing, k) != v for k, v in updates.items() if k != 'last_sync'):
                    for k, v in updates.items():
                        setattr(existing, k, v)
                    print(f"Updated account structure: {account['Code']} for org {org_id}")
                else:
                    print(f"No changes needed for account: {account['Code']} for org {org_id}")
                    
            else:
                # Crear nuevo registro solo si no existe
                existing = XeroAccountStructure(
                    organization_id=org_id,
                    account_id=account['AccountID'],
                    code=account['Code'],
                    name=account['Name'],
                    type=account['Type'],
                    report_type='BS' if account['Type'] in ['ASSET', 'LIABILITY', 'EQUITY'] else 'PL',
                    last_sync=current_time
                )
                db.add(existing)
                print(f"Created new account structure: {account['Code']} for org {org_id}")

            # Commit los cambios
            db.commit()
            return existing

        except SQLAlchemyError as e:
            db.rollback()
            print(f"Error in update_structure: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Database error while updating account structure: {str(e)}"
            )
        except Exception as e:
            db.rollback()
            print(f"Unexpected error in update_structure: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Unexpected error while updating account structure: {str(e)}"
            )

    def log_change(self, db: Session, mapping: AccountMapping, change_type: str, old_value: str, new_value: str):
        """Registra un cambio en la cuenta"""
        change = AccountChange(
            mapping_id=mapping.id,
            change_type=change_type,
            old_code=old_value,
            new_code=new_value,
            changed_at=datetime.utcnow()
        )
        db.add(change)
        # El commit se realizará en update_mapping