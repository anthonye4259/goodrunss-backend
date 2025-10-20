"""
Stripe Payment Integration
Handles platform commissions, trainer payouts, and instant payments
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
import stripe
import os
from datetime import datetime

from ...database import get_db
from ...models import User, Transaction, Booking
from ...schemas import PaymentRequest, PayoutRequest, TransactionResponse

# Initialize Stripe
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
router = APIRouter(prefix="/payments", tags=["payments"])

# Platform commission rate (5%)
PLATFORM_COMMISSION_RATE = 0.05

@router.post("/process-booking-payment")
async def process_booking_payment(
    booking_id: int,
    payment_method_id: str,
    db: Session = Depends(get_db)
):
    """Process payment for a booking with platform commission"""
    try:
        # Get booking details
        booking = db.query(Booking).filter(Booking.id == booking_id).first()
        if not booking:
            raise HTTPException(status_code=404, detail="Booking not found")
        
        # Calculate amounts
        total_amount = booking.total_price
        platform_fee = int(total_amount * PLATFORM_COMMISSION_RATE * 100)  # Convert to cents
        trainer_amount = int(total_amount * 100) - platform_fee
        
        # Create Stripe payment intent
        intent = stripe.PaymentIntent.create(
            amount=int(total_amount * 100),  # Convert to cents
            currency='usd',
            payment_method=payment_method_id,
            confirmation_method='manual',
            confirm=True,
            application_fee_amount=platform_fee,
            transfer_data={
                'destination': booking.trainer.stripe_connect_id
            }
        )
        
        # Record transaction
        transaction = Transaction(
            user_id=booking.user_id,
            amount=total_amount,
            platform_fee=platform_fee / 100,
            trainer_amount=trainer_amount / 100,
            stripe_payment_intent_id=intent.id,
            booking_id=booking_id,
            status="completed"
        )
        db.add(transaction)
        db.commit()
        
        return {
            "success": True,
            "transaction_id": transaction.id,
            "stripe_payment_intent_id": intent.id,
            "amount_charged": total_amount,
            "platform_fee": platform_fee / 100,
            "trainer_amount": trainer_amount / 100
        }
        
    except stripe.error.StripeError as e:
        raise HTTPException(status_code=400, detail=f"Payment failed: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")

@router.post("/instant-payout")
async def request_instant_payout(
    trainer_id: int,
    amount: float,
    db: Session = Depends(get_db)
):
    """Request instant payout for trainer"""
    trainer = db.query(User).filter(User.id == trainer_id).first()
    if not trainer:
        raise HTTPException(status_code=404, detail="Trainer not found")
    
    account = stripe.Account.retrieve(trainer.stripe_connect_id)
    
    if account.charges_enabled and account.payouts_enabled:
        try:
            # Create instant payout
            payout = stripe.Payout.create(
                amount=int(amount * 100),
                currency='usd',
                destination=account.default_destination
            )
            
            return {
                "success": True,
                "payout_id": payout.id,
                "amount": amount,
                "arrival_date": payout.arrival_date
            }
        except stripe.error.StripeError as e:
            raise HTTPException(status_code=400, detail=f"Payout failed: {str(e)}")
    else:
        raise HTTPException(status_code=400, detail="Account not properly set up for payouts")

@router.get("/available-balance/{trainer_id}")
async def get_available_balance(trainer_id: int, db: Session = Depends(get_db)):
    """Get trainer's available balance"""
    trainer = db.query(User).filter(User.id == trainer_id).first()
    if not trainer:
        raise HTTPException(status_code=404, detail="Trainer not found")
    
    # Calculate available balance from completed transactions
    completed_transactions = db.query(Transaction).filter(
        Transaction.booking_id.in_(
            db.query(Booking.id).filter(Booking.trainer_id == trainer_id)
        ),
        Transaction.status == "completed"
    ).all()
    
    available_balance = sum(t.trainer_amount for t in completed_transactions)
    
    return {
        "trainer_id": trainer_id,
        "available_balance": available_balance,
        "currency": "USD"
    }

@router.get("/payout-history/{trainer_id}")
async def get_payout_history(trainer_id: int, db: Session = Depends(get_db)):
    """Get trainer's payout history"""
    # This would integrate with Stripe API to get actual payout history
    # For now, return mock data
    return {
        "trainer_id": trainer_id,
        "payouts": [
            {
                "id": "po_1234567890",
                "amount": 150.00,
                "currency": "USD",
                "status": "paid",
                "arrival_date": "2024-01-15",
                "created": "2024-01-15T10:30:00Z"
            }
        ]
    }