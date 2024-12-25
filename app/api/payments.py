# app/api/payments.py
@router.post("/create-subscription")
async def create_subscription(
    request: schemas.SubscriptionCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    payment_service = PaymentService(settings)
    subscription = await payment_service.create_subscription(
        customer_email=current_user.email,
        price_id=request.price_id,
        payment_method_id=request.payment_method_id,
        country_code=request.country_code
    )
    
    # Guardar en base de datos
    db_subscription = models.Subscription(
        user_id=current_user.id,
        stripe_subscription_id=subscription.id,
        stripe_customer_id=subscription.customer,
        plan_id=request.price_id,
        status=subscription.status,
        current_period_start=datetime.fromtimestamp(
            subscription.current_period_start
        ),
        current_period_end=datetime.fromtimestamp(
            subscription.current_period_end
        ),
        payment_method=request.payment_method_id
    )
    db.add(db_subscription)
    await db.commit()
    
    return subscription