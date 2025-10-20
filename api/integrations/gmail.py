"""
Gmail Integration
Handles email sending, reading, and management
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional, Dict
from datetime import datetime
import base64
import json
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Database imports will be handled dynamically to avoid import errors
try:
    from ...database import get_db
    from ...models import User, EmailIntegration
    from ...schemas import EmailRequest, EmailResponse
except ImportError:
    # Fallback for when database isn't fully set up
    get_db = None
    User = None
    EmailIntegration = None
    EmailRequest = None
    EmailResponse = None

router = APIRouter(prefix="/gmail", tags=["gmail"])

# Gmail API scopes
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly', 
          'https://www.googleapis.com/auth/gmail.send',
          'https://www.googleapis.com/auth/gmail.modify']

@router.post("/connect/{user_id}")
async def connect_gmail(user_id: int, authorization_code: str):
    """Connect Gmail account using OAuth2"""
    # For now, return a mock response without database dependency
    return {
        "message": "Gmail connection initiated",
        "auth_url": f"https://accounts.google.com/o/oauth2/auth?client_id={os.getenv('GOOGLE_CLIENT_ID')}&redirect_uri=http://localhost:8001/auth/google/callback&scope={' '.join(SCOPES)}&response_type=code",
        "user_id": user_id,
        "status": "pending_authorization"
    }

@router.post("/send/{user_id}")
async def send_email(
    user_id: int,
    to: str,
    subject: str,
    body: str,
    db: Session = Depends(get_db)
):
    """Send email via Gmail"""
    email_integration = db.query(EmailIntegration).filter(
        EmailIntegration.user_id == user_id,
        EmailIntegration.provider == "gmail"
    ).first()
    
    if not email_integration:
        raise HTTPException(status_code=404, detail="Gmail not connected")
    
    try:
        # Load credentials
        credentials = Credentials.from_authorized_user_info(
            json.loads(email_integration.credentials), SCOPES)
        
        # Build Gmail service
        service = build('gmail', 'v1', credentials=credentials)
        
        # Create message
        message = {
            'raw': base64.urlsafe_b64encode(
                f"To: {to}\r\nSubject: {subject}\r\n\r\n{body}".encode()
            ).decode()
        }
        
        # Send email
        sent_message = service.users().messages().send(
            userId='me', body=message).execute()
        
        return {
            "success": True,
            "message_id": sent_message['id'],
            "to": to,
            "subject": subject
        }
        
    except HttpError as e:
        raise HTTPException(status_code=400, detail=f"Gmail API error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to send email: {str(e)}")

@router.get("/emails/{user_id}")
async def get_emails(
    user_id: int,
    query: Optional[str] = None,
    max_results: int = 10,
    db: Session = Depends(get_db)
):
    """Get emails from Gmail"""
    email_integration = db.query(EmailIntegration).filter(
        EmailIntegration.user_id == user_id,
        EmailIntegration.provider == "gmail"
    ).first()
    
    if not email_integration:
        raise HTTPException(status_code=404, detail="Gmail not connected")
    
    try:
        # Load credentials
        credentials = Credentials.from_authorized_user_info(
            json.loads(email_integration.credentials), SCOPES)
        
        # Build Gmail service
        service = build('gmail', 'v1', credentials=credentials)
        
        # Get messages
        results = service.users().messages().list(
            userId='me',
            q=query or '',
            maxResults=max_results
        ).execute()
        
        messages = results.get('messages', [])
        
        # Get full message details
        email_list = []
        for message in messages:
            msg = service.users().messages().get(
                userId='me', id=message['id']).execute()
            
            # Extract headers
            headers = msg['payload'].get('headers', [])
            subject = next((h['value'] for h in headers if h['name'] == 'Subject'), '')
            sender = next((h['value'] for h in headers if h['name'] == 'From'), '')
            date = next((h['value'] for h in headers if h['name'] == 'Date'), '')
            
            email_list.append({
                "id": message['id'],
                "subject": subject,
                "sender": sender,
                "date": date,
                "snippet": msg['snippet']
            })
        
        return {
            "emails": email_list,
            "count": len(email_list)
        }
        
    except HttpError as e:
        raise HTTPException(status_code=400, detail=f"Gmail API error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get emails: {str(e)}")

@router.post("/send-booking-confirmation/{user_id}")
async def send_booking_confirmation(
    user_id: int,
    booking_id: int,
    db: Session = Depends(get_db)
):
    """Send booking confirmation email"""
    from ...models import Booking
    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    
    subject = f"Booking Confirmed - {booking.court.name}"
    body = f"""
Hi {booking.user.name},

Your training session has been confirmed!

Details:
- Court: {booking.court.name}
- Trainer: {booking.trainer.name}
- Date: {booking.date}
- Time: {booking.start_time} - {booking.end_time}
- Price: ${booking.total_price}

See you on the court!

Best,
The GoodRunss Team
    """
    
    return await send_email(
        user_id=user_id,
        to=booking.user.email,
        subject=subject,
        body=body,
        db=db
    )