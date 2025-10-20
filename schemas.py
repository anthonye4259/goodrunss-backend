"""
Pydantic schemas for API requests and responses
"""

from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime

# Email schemas
class EmailRequest(BaseModel):
    to: str
    subject: str
    body: str
    html_body: Optional[str] = None

class EmailResponse(BaseModel):
    message_id: str
    status: str
    sent_at: datetime

# Calendar schemas
class CalendarEventRequest(BaseModel):
    title: str
    description: Optional[str] = None
    start_time: datetime
    end_time: datetime
    location: Optional[str] = None

class CalendarEventResponse(BaseModel):
    event_id: str
    status: str
    created_at: datetime

# Payment schemas
class PaymentRequest(BaseModel):
    amount: float
    currency: str = "usd"
    description: str

class PaymentResponse(BaseModel):
    payment_intent_id: str
    status: str
    amount: float

# SMS schemas
class SMSRequest(BaseModel):
    to: str
    message: str

class SMSResponse(BaseModel):
    message_id: str
    status: str
    sent_at: datetime

