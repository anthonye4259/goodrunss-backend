"""
Snapchat Integration with Snap Kit
Handles login, sharing, and Bitmoji integration
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any
import requests
import os
import base64
import hashlib
import hmac
from datetime import datetime, timedelta

# Database imports will be handled dynamically to avoid import errors
try:
    from ...database import get_db
    from ...models import User, Achievement
except ImportError:
    # Fallback for when database isn't fully set up
    get_db = None
    User = None
    Achievement = None

router = APIRouter(prefix="/snapchat", tags=["snapchat"])

# Snapchat API configuration
SNAPCHAT_APP_ID = os.getenv("SNAPCHAT_APP_ID")
SNAPCHAT_CLIENT_SECRET = os.getenv("SNAPCHAT_CLIENT_SECRET")
SNAPCHAT_REDIRECT_URI = os.getenv("SNAPCHAT_REDIRECT_URI", "http://localhost:3000/auth/snapchat/callback")

@router.get("/auth-url")
async def get_snapchat_auth_url():
    """Generate Snapchat OAuth URL for login"""
    if not SNAPCHAT_APP_ID:
        raise HTTPException(status_code=500, detail="Snapchat App ID not configured")
    
    # Snap Kit OAuth URL
    auth_url = f"https://accounts.snapchat.com/login/oauth2/authorize"
    params = {
        "client_id": SNAPCHAT_APP_ID,
        "redirect_uri": SNAPCHAT_REDIRECT_URI,
        "response_type": "code",
        "scope": "user.display_name,user.bitmoji.avatar,user.external_id"
    }
    
    query_string = "&".join([f"{k}={v}" for k, v in params.items()])
    full_url = f"{auth_url}?{query_string}"
    
    return {
        "auth_url": full_url,
        "client_id": SNAPCHAT_APP_ID,
        "redirect_uri": SNAPCHAT_REDIRECT_URI
    }

@router.post("/callback")
async def handle_snapchat_callback(
    code: str,
    state: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Handle Snapchat OAuth callback"""
    if not SNAPCHAT_CLIENT_SECRET:
        raise HTTPException(status_code=500, detail="Snapchat Client Secret not configured")
    
    try:
        # Exchange code for access token
        token_url = "https://accounts.snapchat.com/login/oauth2/access_token"
        token_data = {
            "client_id": SNAPCHAT_APP_ID,
            "client_secret": SNAPCHAT_CLIENT_SECRET,
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": SNAPCHAT_REDIRECT_URI
        }
        
        response = requests.post(token_url, data=token_data)
        response.raise_for_status()
        token_info = response.json()
        
        access_token = token_info.get("access_token")
        if not access_token:
            raise HTTPException(status_code=400, detail="No access token received")
        
        # Get user info from Snapchat
        user_url = "https://kit.snapchat.com/v1/me"
        headers = {"Authorization": f"Bearer {access_token}"}
        user_response = requests.get(user_url, headers=headers)
        user_response.raise_for_status()
        user_info = user_response.json()
        
        # Store or update user in database
        snapchat_id = user_info.get("data", {}).get("me", {}).get("external_id")
        if snapchat_id:
            user = db.query(User).filter(User.snapchat_id == snapchat_id).first()
            if not user:
                user = User(
                    snapchat_id=snapchat_id,
                    username=user_info.get("data", {}).get("me", {}).get("display_name", "Snapchat User"),
                    email=None,  # Snapchat doesn't provide email
                    snapchat_access_token=access_token
                )
                db.add(user)
            else:
                user.snapchat_access_token = access_token
                user.username = user_info.get("data", {}).get("me", {}).get("display_name", user.username)
            
            db.commit()
            
            return {
                "success": True,
                "user_id": user.id,
                "username": user.username,
                "snapchat_id": snapchat_id,
                "bitmoji_avatar": user_info.get("data", {}).get("me", {}).get("bitmoji", {}).get("avatar")
            }
        else:
            raise HTTPException(status_code=400, detail="No Snapchat user ID received")
            
    except requests.RequestException as e:
        raise HTTPException(status_code=400, detail=f"Snapchat API error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")

@router.post("/share-achievement")
async def share_achievement_to_snapchat(
    user_id: int,
    achievement_id: str,
    message: str,
    db: Session = Depends(get_db)
):
    """Share achievement to Snapchat Stories"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.snapchat_access_token:
        raise HTTPException(status_code=404, detail="User not found or not connected to Snapchat")
    
    try:
        # Create shareable content
        share_content = {
            "media": {
                "type": "image",
                "url": f"https://your-domain.com/achievements/{achievement_id}.png"  # Achievement image
            },
            "caption": message,
            "attachment": {
                "url": f"https://your-domain.com/achievements/{achievement_id}",
                "title": "View Achievement on GoodRunss"
            }
        }
        
        # Post to Snapchat Stories
        share_url = "https://kit.snapchat.com/v1/stories"
        headers = {
            "Authorization": f"Bearer {user.snapchat_access_token}",
            "Content-Type": "application/json"
        }
        
        response = requests.post(share_url, json=share_content, headers=headers)
        response.raise_for_status()
        
        return {
            "success": True,
            "message": "Achievement shared to Snapchat successfully",
            "snap_id": response.json().get("id")
        }
        
    except requests.RequestException as e:
        raise HTTPException(status_code=400, detail=f"Snapchat sharing error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")

@router.get("/user-profile/{user_id}")
async def get_snapchat_user_profile(
    user_id: int,
    db: Session = Depends(get_db)
):
    """Get user's Snapchat profile information"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.snapchat_id:
        raise HTTPException(status_code=404, detail="User not found or not connected to Snapchat")
    
    try:
        if user.snapchat_access_token:
            # Get fresh data from Snapchat
            user_url = "https://kit.snapchat.com/v1/me"
            headers = {"Authorization": f"Bearer {user.snapchat_access_token}"}
            response = requests.get(user_url, headers=headers)
            
            if response.status_code == 200:
                user_info = response.json()
                return {
                    "snapchat_id": user.snapchat_id,
                    "username": user_info.get("data", {}).get("me", {}).get("display_name"),
                    "bitmoji_avatar": user_info.get("data", {}).get("me", {}).get("bitmoji", {}).get("avatar"),
                    "connected": True
                }
        
        # Return cached data if token is invalid
        return {
            "snapchat_id": user.snapchat_id,
            "username": user.username,
            "bitmoji_avatar": None,
            "connected": False
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching profile: {str(e)}")

@router.post("/disconnect")
async def disconnect_snapchat(
    user_id: int,
    db: Session = Depends(get_db)
):
    """Disconnect user's Snapchat account"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Clear Snapchat data
    user.snapchat_id = None
    user.snapchat_access_token = None
    db.commit()
    
    return {
        "success": True,
        "message": "Snapchat account disconnected successfully"
    }

@router.get("/bitmoji/{user_id}")
async def get_user_bitmoji(
    user_id: int,
    db: Session = Depends(get_db)
):
    """Get user's Bitmoji avatar URL"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.snapchat_access_token:
        raise HTTPException(status_code=404, detail="User not found or not connected to Snapchat")
    
    try:
        user_url = "https://kit.snapchat.com/v1/me"
        headers = {"Authorization": f"Bearer {user.snapchat_access_token}"}
        response = requests.get(user_url, headers=headers)
        
        if response.status_code == 200:
            user_info = response.json()
            bitmoji = user_info.get("data", {}).get("me", {}).get("bitmoji", {})
            return {
                "bitmoji_avatar": bitmoji.get("avatar"),
                "bitmoji_selfie": bitmoji.get("selfie")
            }
        else:
            raise HTTPException(status_code=400, detail="Unable to fetch Bitmoji data")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching Bitmoji: {str(e)}")

@router.post("/creative-kit/share")
async def share_via_creative_kit(
    user_id: int,
    content_type: str,
    content_url: str,
    caption: str,
    db: Session = Depends(get_db)
):
    """Share content via Snapchat Creative Kit"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.snapchat_access_token:
        raise HTTPException(status_code=404, detail="User not found or not connected to Snapchat")
    
    # Creative Kit sharing (this would typically be handled on the frontend)
    # This endpoint provides the necessary data for frontend integration
    return {
        "success": True,
        "share_data": {
            "content_type": content_type,
            "content_url": content_url,
            "caption": caption,
            "app_id": SNAPCHAT_APP_ID,
            "user_token": user.snapchat_access_token
        },
        "message": "Use this data with Snapchat Creative Kit SDK on frontend"
    }
