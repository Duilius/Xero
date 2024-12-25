# app/core/services/payment_service.py
from datetime import datetime, timezone
from typing import List, Optional
import stripe
from fastapi import HTTPException

class PaymentService:
    def __init__(self, settings):
        self.stripe = stripe
        self.stripe.api_key = settings.STRIPE_SECRET_KEY
        self.webhook_secret = settings.STRIPE_WEBHOOK_SECRET

    async def create_subscription(
        self,
        customer_email: str,
        price_id: str,
        payment_method_id: Optional[str] = None,
        country_code: str = 'US'
    ):
        try:
            # Crear o recuperar cliente
            customer = await self._get_or_create_customer(customer_email)

            # Determinar método de pago según país
            payment_methods = self._get_available_payment_methods(country_code)

            # Crear suscripción
            subscription = await self.stripe.Subscription.create(
                customer=customer.id,
                items=[{'price': price_id}],
                payment_method=payment_method_id,
                payment_settings={
                    'payment_method_types': payment_methods
                },
                expand=['latest_invoice.payment_intent']
            )

            return subscription

        except stripe.error.StripeError as e:
            raise HTTPException(status_code=400, detail=str(e))

    def _get_available_payment_methods(self, country_code: str) -> List[str]:
        """Determina métodos de pago disponibles por país"""
        methods = ['card']  # Siempre disponible
        
        country_methods = {
            'AU': ['au_becs_debit'],
            'GB': ['bacs_debit'],
            'SG': ['grabpay', 'paynow'],
            'MY': ['grabpay', 'fpx']
        }
        
        return methods + country_methods.get(country_code, [])