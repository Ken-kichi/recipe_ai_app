from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session
import os
import stripe

from src.get_conn import get_db
from src.db_models import StripePlan, Subscription, User
from datetime import datetime

router = APIRouter()

stripe.api_key = os.getenv("STRIPE_API_KEY")


@router.get("/plans")
def list_plans(db: Session = Depends(get_db)):
    plans = StripePlan.get_all_plans(db=db)
    return plans


@router.post("/create-checkout-session")
def create_checkout_session(stripe_plan_id: str, user_email: str, db: Session = Depends(get_db)):
    """
    Create a Stripe Checkout Session for a given plan and user email.
    The `StripePlan.stripe_plan_id` is expected to be a Stripe Price ID or Price/Product identifier.
    """
    if not stripe.api_key:
        raise HTTPException(
            status_code=500, detail="Stripe API key not configured")

    try:
        stripe.Price.retrieve(stripe_plan_id)
    except stripe.error.InvalidRequestError:
        raise HTTPException(status_code=404, detail="Price not found")

    try:
        success_url = os.getenv(
            "STRIPE_SUCCESS_URL") or "https://example.com/success"
        cancel_url = os.getenv(
            "STRIPE_CANCEL_URL") or "https://example.com/cancel"

        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            mode="subscription",
            line_items=[{"price": stripe_plan_id, "quantity": 1}],
            customer_email=user_email,
            success_url=success_url,
            cancel_url=cancel_url,
            metadata={"plan_id": stripe_plan_id},
        )

        return {"checkout_session_id": session.id, "checkout_url": session.url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/webhook")
async def stripe_webhook(request: Request, db: Session = Depends(get_db)):
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")
    webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET")

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, webhook_secret)
    except stripe.error.SignatureVerificationError as e:
        raise HTTPException(status_code=400, detail=f"Invalid signature: {e}")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid payload: {e}")

    evt_type = event["type"]
    data = event["data"]["object"]

    try:
        # === Checkout完了 ===
        if evt_type == "checkout.session.completed":
            customer_email = data.get("customer_email")
            plan_id = data.get("metadata", {}).get("plan_id")

            if not (customer_email and plan_id):
                raise HTTPException(
                    status_code=400, detail="Missing plan_id or email")

            user = User.get_user_by_email(db=db, email=customer_email)
            if not user:
                raise HTTPException(
                    status_code=404, detail=f"User not found: {customer_email}")

            # すでにsubscriptionが存在するかチェック
            existing_sub = Subscription.get_subscription_by_stripe_subscription_id(
                db=db, stripe_subscription_id=data.get("subscription"))

            if existing_sub:
                return {"status": "duplicate_event"}

            new_sub = Subscription(
                user_id=user.id,
                stripe_plan_id=plan_id,
                stripe_customer_id=data.get("customer"),
                stripe_subscription_id=data.get("subscription"),
                status="active",
                start_date=datetime.utcnow(),
            )
            db.add(new_sub)
            db.commit()

        # === Subscription更新 ===
        elif evt_type in (
            "customer.subscription.created",
            "customer.subscription.updated",
            "customer.subscription.deleted",
        ):
            stripe_sub_id = data.get("id")
            sub = Subscription.get_subscription_by_stripe_subscription_id(
                db=db, stripe_subscription_id=stripe_sub_id)

            if sub:
                sub.status = data.get("status")
                if sub.status in ("canceled", "unpaid", "past_due"):
                    sub.end_date = datetime.utcnow()
                db.commit()

        # === Invoice支払いイベント ===
        elif evt_type in ("invoice.payment_failed", "invoice.payment_succeeded"):
            stripe_sub_id = data.get("subscription")
            sub = Subscription.get_subscription_by_stripe_subscription_id(
                db=db, stripe_subscription_id=stripe_sub_id)
            if sub:
                sub.status = (
                    "active"
                    if evt_type == "invoice.payment_succeeded"
                    else "past_due"
                )
                db.commit()

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500, detail=f"Webhook processing failed: {e}")

    return {"status": "ok"}
