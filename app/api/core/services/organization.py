# app/core/services/organization.py
class OrganizationService:
    async def create(self, db: Session, org: schemas.OrganizationCreate, user_id: int,
                    browser_timestamp: str, client_timezone: str):
        # Crear organización principal
        db_org = models.Organization(
            name=org.name,
            user_id=user_id
        )
        db.add(db_org)
        db.flush()

        # Crear detalles
        browser_time = datetime.fromisoformat(browser_timestamp)
        server_time = datetime.now(timezone.utc)
        
        details = models.OrganizationDetail(
            organization_id=db_org.id,
            industry=org.industry,
            country=org.country,
            browser_timestamp=browser_time,
            server_timestamp=server_time,
            timezone_offset=org.timezone_offset
        )
        db.add(details)
        
        # Si hay sucursales, crearlas
        if org.branches:
            for branch in org.branches:
                db_branch = models.OrganizationBranch(
                    organization_id=db_org.id,
                    name=branch.name,
                    country=branch.country,
                    is_headquarters=branch.is_headquarters
                )
                db.add(db_branch)
        
        await db.commit()
        return db_org

    async def analyze_and_recommend(self, db: Session, org_id: int, current_user: models.User):
        org = await self.get_by_id(db, org_id)
        if not org:
            raise HTTPException(status_code=404, detail="Organization not found")
            
        # Obtener módulos actuales de Xero
        current_modules = await services.xero.get_active_modules(db, org_id)
        
        # Analizar según industria y tamaño
        recommendations = await services.ai.analyze_organization(
            industry=org.details.industry,
            size=org.details.employee_count,
            current_modules=current_modules
        )
        
        # Actualizar recomendaciones
        org.details.recommended_modules = recommendations
        await db.commit()
        
        return {
            "current_modules": current_modules,
            "recommendations": recommendations,
            "analysis_timestamp": datetime.now(timezone.utc)
        }