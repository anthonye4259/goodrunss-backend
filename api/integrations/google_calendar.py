"""
Google Calendar Integration
Handles calendar events, scheduling, and syncing
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional, Dict
from datetime import datetime, timedelta
import json
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Database imports will be handled dynamically to avoid import errors
try:
    from ...database import get_db
    from ...models import User, CalendarIntegration, Booking
    from ...schemas import CalendarEventRequest, CalendarEventResponse
except ImportError:
    # Fallback for when database isn't fully set up
    get_db = None
    User = None
    CalendarIntegration = None
    Booking = None
    CalendarEventRequest = None
    CalendarEventResponse = None

router = APIRouter(prefix="/calendar", tags=["calendar"])

# Google Calendar API scopes
SCOPES = ['https://www.googleapis.com/auth/calendar']

@router.post("/connect/{user_id}")
async def connect_google_calendar(user_id: int, authorization_code: str):
    """Connect Google Calendar using OAuth2"""
    # For now, return a mock response without database dependency
    return {
        "message": "Google Calendar connection initiated",
        "auth_url": f"https://accounts.google.com/o/oauth2/auth?client_id={os.getenv('GOOGLE_CLIENT_ID')}&redirect_uri=http://localhost:8001/auth/google/callback&scope={' '.join(SCOPES)}&response_type=code",
        "user_id": user_id,
        "status": "pending_authorization"
    }

@router.post("/create-event/{user_id}")
async def create_calendar_event(
    user_id: int,
    event_request: CalendarEventRequest,
    db: Session = Depends(get_db)
):
    """Create a calendar event"""
    calendar_integration = db.query(CalendarIntegration).filter(
        CalendarIntegration.user_id == user_id,
        CalendarIntegration.provider == "google_calendar"
    ).first()
    
    if not calendar_integration:
        raise HTTPException(status_code=404, detail="Google Calendar not connected")
    
    try:
        # Load credentials
        credentials = Credentials.from_authorized_user_info(
            json.loads(calendar_integration.credentials), SCOPES)
        
        # Build Calendar service
        service = build('calendar', 'v3', credentials=credentials)
        
        # Create event
        event = {
            'summary': event_request.title,
            'description': event_request.description,
            'start': {
                'dateTime': event_request.start_time.isoformat(),
                'timeZone': 'America/New_York',
            },
            'end': {
                'dateTime': event_request.end_time.isoformat(),
                'timeZone': 'America/New_York',
            },
            'attendees': [{'email': email} for email in event_request.attendees],
            'reminders': {
                'useDefault': False,
                'overrides': [
                    {'method': 'email', 'minutes': 24 * 60},
                    {'method': 'popup', 'minutes': 10},
                ],
            },
        }
        
        # Insert event
        created_event = service.events().insert(
            calendarId='primary', body=event).execute()
        
        return {
            "success": True,
            "event_id": created_event['id'],
            "event_link": created_event['htmlLink'],
            "title": event_request.title
        }
        
    except HttpError as e:
        raise HTTPException(status_code=400, detail=f"Calendar API error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create event: {str(e)}")

@router.post("/sync-booking/{user_id}/{booking_id}")
async def sync_booking_to_calendar(
    user_id: int,
    booking_id: int,
    db: Session = Depends(get_db)
):
    """Sync a booking to Google Calendar"""
    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    
    # Create event request
    event_request = CalendarEventRequest(
        title=f"Training Session - {booking.court.name}",
        description=f"""
Training session with {booking.trainer.name}

Court: {booking.court.name}
Location: {booking.court.location}
Price: ${booking.total_price}

Booked via GoodRunss
        """.strip(),
        start_time=datetime.combine(booking.date, booking.start_time),
        end_time=datetime.combine(booking.date, booking.end_time),
        attendees=[booking.user.email, booking.trainer.email]
    )
    
    return await create_calendar_event(user_id, event_request, db)

@router.get("/events/{user_id}")
async def get_calendar_events(
    user_id: int,
    days_ahead: int = 7,
    db: Session = Depends(get_db)
):
    """Get upcoming calendar events"""
    calendar_integration = db.query(CalendarIntegration).filter(
        CalendarIntegration.user_id == user_id,
        CalendarIntegration.provider == "google_calendar"
    ).first()
    
    if not calendar_integration:
        raise HTTPException(status_code=404, detail="Google Calendar not connected")
    
    try:
        # Load credentials
        credentials = Credentials.from_authorized_user_info(
            json.loads(calendar_integration.credentials), SCOPES)
        
        # Build Calendar service
        service = build('calendar', 'v3', credentials=credentials)
        
        # Get events
        now = datetime.utcnow().isoformat() + 'Z'
        time_max = (datetime.utcnow() + timedelta(days=days_ahead)).isoformat() + 'Z'
        
        events_result = service.events().list(
            calendarId='primary',
            timeMin=now,
            timeMax=time_max,
            maxResults=50,
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        
        events = events_result.get('items', [])
        
        event_list = []
        for event in events:
            start = event['start'].get('dateTime', event['start'].get('date'))
            end = event['end'].get('dateTime', event['end'].get('date'))
            
            event_list.append({
                "id": event['id'],
                "title": event.get('summary', 'No Title'),
                "description": event.get('description', ''),
                "start": start,
                "end": end,
                "location": event.get('location', ''),
                "attendees": [attendee.get('email') for attendee in event.get('attendees', [])]
            })
        
        return {
            "events": event_list,
            "count": len(event_list)
        }
        
    except HttpError as e:
        raise HTTPException(status_code=400, detail=f"Calendar API error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get events: {str(e)}")

@router.delete("/event/{user_id}/{event_id}")
async def delete_calendar_event(
    user_id: int,
    event_id: str,
    db: Session = Depends(get_db)
):
    """Delete a calendar event"""
    calendar_integration = db.query(CalendarIntegration).filter(
        CalendarIntegration.user_id == user_id,
        CalendarIntegration.provider == "google_calendar"
    ).first()
    
    if not calendar_integration:
        raise HTTPException(status_code=404, detail="Google Calendar not connected")
    
    try:
        # Load credentials
        credentials = Credentials.from_authorized_user_info(
            json.loads(calendar_integration.credentials), SCOPES)
        
        # Build Calendar service
        service = build('calendar', 'v3', credentials=credentials)
        
        # Delete event
        service.events().delete(
            calendarId='primary', eventId=event_id).execute()
        
        return {
            "success": True,
            "message": "Event deleted successfully"
        }
        
    except HttpError as e:
        raise HTTPException(status_code=400, detail=f"Calendar API error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete event: {str(e)}")
