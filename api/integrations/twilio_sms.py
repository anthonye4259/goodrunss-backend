"""
Twilio SMS Integration
Handles SMS notifications, 2FA, and messaging
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional, Dict
from datetime import datetime, timedelta
import random
import string
import os
from twilio.rest import Client
from twilio.base.exceptions import TwilioException

from ...database import get_db
from ...models import User, SMSLog, TwoFactorCode

router = APIRouter(prefix="/sms", tags=["sms"])

# Initialize Twilio client
account_sid = os.getenv("TWILIO_ACCOUNT_SID")
auth_token = os.getenv("TWILIO_AUTH_TOKEN")
twilio_phone = os.getenv("TWILIO_PHONE_NUMBER")

if account_sid and auth_token:
    client = Client(account_sid, auth_token)
else:
    client = None

@router.post("/send/{user_id}")
async def send_sms(
    user_id: int,
    phone_number: str,
    message: str,
    db: Session = Depends(get_db)
):
    """Send SMS message"""
    if not client:
        raise HTTPException(status_code=500, detail="Twilio not configured")
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    try:
        # Send SMS
        message_obj = client.messages.create(
            body=message,
            from_=twilio_phone,
            to=phone_number
        )
        
        # Log SMS
        sms_log = SMSLog(
            user_id=user_id,
            phone_number=phone_number,
            message=message,
            twilio_sid=message_obj.sid,
            status=message_obj.status,
            sent_at=datetime.utcnow()
        )
        db.add(sms_log)
        db.commit()
        
        return {
            "success": True,
            "message_sid": message_obj.sid,
            "status": message_obj.status,
            "to": phone_number
        }
        
    except TwilioException as e:
        raise HTTPException(status_code=400, detail=f"Twilio error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to send SMS: {str(e)}")

@router.post("/send-2fa/{user_id}")
async def send_2fa_code(
    user_id: int,
    phone_number: str,
    db: Session = Depends(get_db)
):
    """Send 2FA verification code"""
    if not client:
        raise HTTPException(status_code=500, detail="Twilio not configured")
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Generate 6-digit code
    code = ''.join(random.choices(string.digits, k=6))
    
    # Set expiration (5 minutes)
    expires_at = datetime.utcnow() + timedelta(minutes=5)
    
    # Save code to database
    two_factor_code = TwoFactorCode(
        user_id=user_id,
        phone_number=phone_number,
        code=code,
        expires_at=expires_at,
        created_at=datetime.utcnow()
    )
    db.add(two_factor_code)
    db.commit()
    
    # Send SMS
    message = f"Your GoodRunss verification code is: {code}. This code expires in 5 minutes."
    
    try:
        message_obj = client.messages.create(
            body=message,
            from_=twilio_phone,
            to=phone_number
        )
        
        return {
            "success": True,
            "message": "2FA code sent successfully",
            "expires_at": expires_at
        }
        
    except TwilioException as e:
        raise HTTPException(status_code=400, detail=f"Failed to send 2FA code: {str(e)}")

@router.post("/verify-2fa/{user_id}")
async def verify_2fa_code(
    user_id: int,
    phone_number: str,
    code: str,
    db: Session = Depends(get_db)
):
    """Verify 2FA code"""
    two_factor_code = db.query(TwoFactorCode).filter(
        TwoFactorCode.user_id == user_id,
        TwoFactorCode.phone_number == phone_number,
        TwoFactorCode.code == code,
        TwoFactorCode.expires_at > datetime.utcnow(),
        TwoFactorCode.used == False
    ).first()
    
    if not two_factor_code:
        raise HTTPException(status_code=400, detail="Invalid or expired code")
    
    # Mark code as used
    two_factor_code.used = True
    two_factor_code.verified_at = datetime.utcnow()
    db.commit()
    
    return {
        "success": True,
        "message": "2FA verification successful",
        "verified_at": two_factor_code.verified_at
    }