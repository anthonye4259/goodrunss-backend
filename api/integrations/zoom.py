"""
Zoom Integration
Handles virtual meeting creation and management
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional, Dict
from datetime import datetime, timedelta
import requests
import json
import os

from ...database import get_db
from ...models import User, ZoomIntegration, VirtualSession

router = APIRouter(prefix="/zoom", tags=["zoom"])

# Zoom API configuration
ZOOM_API_KEY = os.getenv("ZOOM_API_KEY")

@router.post("/connect/{user_id}")
async def connect_zoom(user_id: int, access_token: str, db: Session = Depends(get_db)):
    """Connect Zoom account"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    try:
        # Verify Zoom access token
        verify_url = "https://api.zoom.us/v2/users/me"
        headers = {"Authorization": f"Bearer {access_token}"}
        
        response = requests.get(verify_url, headers=headers)
        
        if response.status_code != 200:
            raise HTTPException(status_code=400, detail="Invalid Zoom access token")
        
        user_data = response.json()
        
        # Save integration
        zoom_integration = ZoomIntegration(
            user_id=user_id,
            access_token=access_token,
            zoom_user_id=user_data.get("id"),
            email=user_data.get("email"),
            connected_at=datetime.utcnow(),
            status="connected"
        )
        db.add(zoom_integration)
        db.commit()
        
        return {
            "success": True,
            "message": "Zoom connected successfully",
            "email": user_data.get("email"),
            "connected_at": zoom_integration.connected_at
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Zoom connection failed: {str(e)}")

@router.post("/create-virtual-session/{user_id}")
async def create_virtual_training_session(
    user_id: int,
    trainer_name: str,
    session_type: str,
    start_time: datetime,
    duration_minutes: int,
    price: float,
    db: Session = Depends(get_db)
):
    """Create a virtual training session with Zoom"""
    zoom_integration = db.query(ZoomIntegration).filter(
        ZoomIntegration.user_id == user_id
    ).first()
    
    if not zoom_integration:
        raise HTTPException(status_code=404, detail="Zoom not connected")
    
    try:
        # Create meeting via Zoom API
        create_url = f"https://api.zoom.us/v2/users/{zoom_integration.zoom_user_id}/meetings"
        
        headers = {
            "Authorization": f"Bearer {zoom_integration.access_token}",
            "Content-Type": "application/json"
        }
        
        meeting_data = {
            "topic": f"Virtual Training Session - {trainer_name}",
            "type": 2,  # Scheduled meeting
            "start_time": start_time.isoformat(),
            "duration": duration_minutes,
            "timezone": "America/New_York",
            "settings": {
                "host_video": True,
                "participant_video": True,
                "join_before_host": False,
                "mute_upon_entry": True,
                "waiting_room": True
            }
        }
        
        response = requests.post(create_url, headers=headers, json=meeting_data)
        
        if response.status_code != 201:
            raise HTTPException(status_code=400, detail="Failed to create Zoom meeting")
        
        meeting_info = response.json()
        
        # Save virtual session
        virtual_session = VirtualSession(
            user_id=user_id,
            trainer_name=trainer_name,
            session_type=session_type,
            start_time=start_time,
            duration_minutes=duration_minutes,
            zoom_meeting_id=meeting_info["id"],
            zoom_join_url=meeting_info["join_url"],
            zoom_start_url=meeting_info["start_url"],
            price=price,
            status="scheduled",
            created_at=datetime.utcnow()
        )
        db.add(virtual_session)
        db.commit()
        
        return {
            "success": True,
            "virtual_session_id": virtual_session.id,
            "zoom_meeting": {
                "meeting_id": meeting_info["id"],
                "join_url": meeting_info["join_url"],
                "start_url": meeting_info["start_url"]
            },
            "session_details": {
                "trainer_name": trainer_name,
                "session_type": session_type,
                "start_time": start_time,
                "duration_minutes": duration_minutes,
                "price": price
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create virtual session: {str(e)}")

@router.get("/virtual-sessions/{user_id}")
async def get_virtual_sessions(user_id: int, db: Session = Depends(get_db)):
    """Get user's virtual training sessions"""
    virtual_sessions = db.query(VirtualSession).filter(
        VirtualSession.user_id == user_id
    ).order_by(VirtualSession.start_time.desc()).all()
    
    sessions = []
    for session in virtual_sessions:
        sessions.append({
            "id": session.id,
            "trainer_name": session.trainer_name,
            "session_type": session.session_type,
            "start_time": session.start_time,
            "duration_minutes": session.duration_minutes,
            "price": session.price,
            "status": session.status,
            "zoom_join_url": session.zoom_join_url,
            "created_at": session.created_at
        })
    
    return {
        "virtual_sessions": sessions,
        "count": len(sessions)
    }