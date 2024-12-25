# app/api/automation.py
@router.post("/automation/reconciliation/schedule")
async def schedule_reconciliation(
    request: schemas.ReconciliationSchedule,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    automation_service = AutomationService()
    schedule = await automation_service.schedule_reconciliation(
        db=db,
        org_id=request.organization_id,
        related_orgs=request.related_organizations,
        frequency=request.frequency
    )
    return schedule

@router.get("/automation/reconciliation/matches")
async def get_reconciliation_matches(
    org_id: int,
    start_date: datetime,
    end_date: datetime,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    automation_service = AutomationService()
    matches = await automation_service.find_matches_for_period(
        db=db,
        org_id=org_id,
        start_date=start_date,
        end_date=end_date
    )
    return matches