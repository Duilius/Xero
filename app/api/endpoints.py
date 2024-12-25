# app/api/endpoints.py
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timezone
from ..core import services
from ..core.services.translations import translations
from ..db import models, schemas

router = APIRouter()

# Endpoint original actualizado con soporte de idioma
@router.post("/organizations/", response_model=schemas.Organization)
async def create_organization(
    org: schemas.OrganizationCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    browser_timestamp = request.headers.get("X-Client-Timestamp")
    client_tz = request.headers.get("X-Client-Timezone")
    language = request.state.language if hasattr(request.state, 'language') else 'en'
    
    result = await services.organization.create(
        db=db,
        org=org,
        user_id=current_user.id,
        browser_timestamp=browser_timestamp,
        client_timezone=client_tz
    )

    return {
        "data": result,
        "message": translations[language]["organizations"]["created"]
    }

@router.get("/organizations/", response_model=List[schemas.OrganizationDetail])
async def get_organizations(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
    country: Optional[str] = None,
    industry: Optional[str] = None,
    request: Request = None
):
    language = request.state.language if request and hasattr(request.state, 'language') else 'en'
    
    orgs = await services.organization.get_all(
        db=db,
        user_id=current_user.id,
        filters={"country": country, "industry": industry}
    )
    
    return {
        "data": orgs,
        "title": translations[language]["organizations"]["title"]
    }

@router.post("/organizations/{org_id}/contacts/")
async def add_organization_contact(
    org_id: int,
    contact: schemas.ContactCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
    request: Request = None
):
    language = request.state.language if request and hasattr(request.state, 'language') else 'en'
    
    result = await services.organization.add_contact(
        db=db,
        org_id=org_id,
        contact=contact,
        current_user=current_user
    )
    
    return {
        "data": result,
        "message": translations[language]["contacts"]["added"]
    }

@router.get("/organizations/{org_id}/permissions/")
async def get_organization_permissions(
    org_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    return await services.xero.get_permissions(
        db=db,
        org_id=org_id,
        current_user=current_user
    )

@router.post("/organizations/{org_id}/analyze/")
async def analyze_organization(
    org_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
    request: Request = None
):
    """Analiza módulos usados y genera recomendaciones"""
    language = request.state.language if request and hasattr(request.state, 'language') else 'en'
    
    result = await services.organization.analyze_and_recommend(
        db=db,
        org_id=org_id,
        current_user=current_user
    )
    
    return {
        "data": result,
        "message": translations[language]["analysis"]["completed"]
    }

# Nuevos endpoints
@router.get("/organizations/{org_id}/metrics")
async def get_organization_metrics(
    org_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Obtiene métricas y KPIs de la organización"""
    language = request.state.language if hasattr(request.state, 'language') else 'en'
    
    metrics = await services.organization.get_metrics(
        db=db,
        org_id=org_id,
        current_user=current_user
    )

    return {
        "data": metrics,
        "labels": translations[language]["metrics"]
    }

@router.get("/user/preferences")
async def get_user_preferences(
    request: Request,
    current_user: models.User = Depends(get_current_user)
):
    """Obtiene preferencias del usuario incluyendo idioma"""
    return {
        "language": request.state.language if hasattr(request.state, 'language') else 'en',
        "theme": getattr(current_user, 'theme_preference', 'dark'),
        "timezone": getattr(current_user, 'timezone', 'UTC')
    }

@router.put("/user/preferences")
async def update_user_preferences(
    preferences: schemas.UserPreferences,
    request: Request,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Actualiza preferencias del usuario"""
    language = request.state.language if hasattr(request.state, 'language') else 'en'
    
    updated = await services.user.update_preferences(
        db=db,
        user_id=current_user.id,
        preferences=preferences
    )

    return {
        "data": updated,
        "message": translations[language]["preferences"]["updated"]
    }