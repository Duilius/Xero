# app/core/services/xero.py
class XeroService:
    async def get_permissions(self, db: Session, org_id: int, current_user: models.User):
        permissions = db.query(models.XeroPermission).filter(
            models.XeroPermission.organization_id == org_id
        ).all()
        
        return {
            "active_permissions": [p for p in permissions if p.is_active],
            "inactive_permissions": [p for p in permissions if not p.is_active],
            "last_updated": datetime.now(timezone.utc)
        }

    async def get_active_modules(self, db: Session, org_id: int):
        org = db.query(models.Organization).get(org_id)
        if not org or not org.xero_tenant_id:
            raise HTTPException(status_code=404, detail="Organization not found or not connected to Xero")
            
        # Obtener token activo
        token = await self.get_valid_token(db, org.user_id)
        if not token:
            raise HTTPException(status_code=401, detail="No valid Xero token found")
            
        # Consultar API de Xero
        xero_client = self.create_xero_client(token)
        return await xero_client.get_active_modules(org.xero_tenant_id)