"""
Simplified Gmail Integration - No Database Dependencies
"""

from fastapi import APIRouter, HTTPException
import os

router = APIRouter(prefix="/gmail", tags=["gmail"])

# Gmail API scopes
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly', 
          'https://www.googleapis.com/auth/gmail.send',
          'https://www.googleapis.com/auth/gmail.modify']

@router.post("/connect/{user_id}")
async def connect_gmail(user_id: int, authorization_code: str = None):
    """Connect Gmail account using OAuth2"""
    client_id = os.getenv('GOOGLE_CLIENT_ID')
    if not client_id:
        raise HTTPException(status_code=500, detail="Google Client ID not configured")
    
    auth_url = f"https://accounts.google.com/o/oauth2/auth?client_id={client_id}&redirect_uri=http://localhost:8001/auth/google/callback&scope={' '.join(SCOPES)}&response_type=code"
    
    return {
        "message": "Gmail connection initiated",
        "auth_url": auth_url,
        "user_id": user_id,
        "status": "pending_authorization",
        "client_id": client_id[:20] + "..."
    }

@router.get("/auth-url")
async def get_gmail_auth_url():
    """Get Gmail OAuth authorization URL"""
    client_id = os.getenv('GOOGLE_CLIENT_ID')
    if not client_id:
        raise HTTPException(status_code=500, detail="Google Client ID not configured")
    
    auth_url = f"https://accounts.google.com/o/oauth2/auth?client_id={client_id}&redirect_uri=http://localhost:8001/auth/google/callback&scope={' '.join(SCOPES)}&response_type=code"
    
    return {
        "auth_url": auth_url,
        "client_id": client_id,
        "redirect_uri": "http://localhost:8001/auth/google/callback"
    }
