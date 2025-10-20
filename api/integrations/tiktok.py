"""
TikTok Integration with TikTok for Developers API
Handles login, sharing, and content creation
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any, List
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

router = APIRouter(prefix="/tiktok", tags=["tiktok"])

# TikTok API configuration
TIKTOK_CLIENT_KEY = os.getenv("TIKTOK_CLIENT_KEY")
TIKTOK_CLIENT_SECRET = os.getenv("TIKTOK_CLIENT_SECRET")
TIKTOK_REDIRECT_URI = os.getenv("TIKTOK_REDIRECT_URI", "http://localhost:3000/auth/tiktok/callback")

# TikTok API endpoints
TIKTOK_AUTH_URL = "https://www.tiktok.com/v2/auth/authorize/"
TIKTOK_TOKEN_URL = "https://open.tiktokapis.com/v2/oauth/token/"
TIKTOK_API_BASE = "https://open.tiktokapis.com/v2"

@router.get("/auth-url")
async def get_tiktok_auth_url():
    """Generate TikTok OAuth URL for login"""
    if not TIKTOK_CLIENT_KEY:
        raise HTTPException(status_code=500, detail="TikTok Client Key not configured")
    
    # TikTok OAuth URL
    auth_url = TIKTOK_AUTH_URL
    params = {
        "client_key": TIKTOK_CLIENT_KEY,
        "scope": "user.info.basic,video.publish",
        "response_type": "code",
        "redirect_uri": TIKTOK_REDIRECT_URI,
        "state": "goodrunss_auth_state"
    }
    
    query_string = "&".join([f"{k}={v}" for k, v in params.items()])
    full_url = f"{auth_url}?{query_string}"
    
    return {
        "auth_url": full_url,
        "client_key": TIKTOK_CLIENT_KEY,
        "redirect_uri": TIKTOK_REDIRECT_URI
    }

@router.post("/callback")
async def handle_tiktok_callback(
    code: str,
    state: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Handle TikTok OAuth callback"""
    if not TIKTOK_CLIENT_SECRET:
        raise HTTPException(status_code=500, detail="TikTok Client Secret not configured")
    
    try:
        # Exchange code for access token
        token_data = {
            "client_key": TIKTOK_CLIENT_KEY,
            "client_secret": TIKTOK_CLIENT_SECRET,
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": TIKTOK_REDIRECT_URI
        }
        
        response = requests.post(TIKTOK_TOKEN_URL, data=token_data)
        response.raise_for_status()
        token_info = response.json()
        
        access_token = token_info.get("access_token")
        if not access_token:
            raise HTTPException(status_code=400, detail="No access token received")
        
        # Get user info from TikTok
        user_url = f"{TIKTOK_API_BASE}/user/info/"
        headers = {"Authorization": f"Bearer {access_token}"}
        user_response = requests.get(user_url, headers=headers)
        user_response.raise_for_status()
        user_info = user_response.json()
        
        # Store or update user in database
        tiktok_id = user_info.get("data", {}).get("user", {}).get("open_id")
        if tiktok_id:
            user = db.query(User).filter(User.tiktok_id == tiktok_id).first()
            if not user:
                user = User(
                    tiktok_id=tiktok_id,
                    username=user_info.get("data", {}).get("user", {}).get("display_name", "TikTok User"),
                    email=None,  # TikTok doesn't provide email
                    tiktok_access_token=access_token
                )
                db.add(user)
            else:
                user.tiktok_access_token = access_token
                user.username = user_info.get("data", {}).get("user", {}).get("display_name", user.username)
            
            db.commit()
            
            return {
                "success": True,
                "user_id": user.id,
                "username": user.username,
                "tiktok_id": tiktok_id,
                "avatar_url": user_info.get("data", {}).get("user", {}).get("avatar_url")
            }
        else:
            raise HTTPException(status_code=400, detail="No TikTok user ID received")
            
    except requests.RequestException as e:
        raise HTTPException(status_code=400, detail=f"TikTok API error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")

@router.post("/share-achievement")
async def share_achievement_to_tiktok(
    user_id: int,
    achievement_id: str,
    message: str,
    video_url: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Share achievement to TikTok"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.tiktok_access_token:
        raise HTTPException(status_code=404, detail="User not found or not connected to TikTok")
    
    try:
        # Create TikTok post data
        post_data = {
            "post_info": {
                "title": f"GoodRunss Achievement: {message}",
                "description": f"I just unlocked '{message}' on GoodRunss! 🏆 #GoodRunss #Achievement #Fitness",
                "privacy_level": "SELF_ONLY",  # Start private, user can make public
                "disable_duet": False,
                "disable_comment": False,
                "disable_stitch": False,
                "video_cover_timestamp_ms": 1000
            }
        }
        
        # If video URL provided, upload video
        if video_url:
            post_data["post_info"]["video_url"] = video_url
        
        # Post to TikTok
        post_url = f"{TIKTOK_API_BASE}/post/publish/video/init/"
        headers = {
            "Authorization": f"Bearer {user.tiktok_access_token}",
            "Content-Type": "application/json"
        }
        
        response = requests.post(post_url, json=post_data, headers=headers)
        response.raise_for_status()
        
        return {
            "success": True,
            "message": "Achievement shared to TikTok successfully",
            "post_id": response.json().get("data", {}).get("publish_id")
        }
        
    except requests.RequestException as e:
        raise HTTPException(status_code=400, detail=f"TikTok posting error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")

@router.get("/user-profile/{user_id}")
async def get_tiktok_user_profile(
    user_id: int,
    db: Session = Depends(get_db)
):
    """Get user's TikTok profile information"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.tiktok_id:
        raise HTTPException(status_code=404, detail="User not found or not connected to TikTok")
    
    try:
        if user.tiktok_access_token:
            # Get fresh data from TikTok
            user_url = f"{TIKTOK_API_BASE}/user/info/"
            headers = {"Authorization": f"Bearer {user.tiktok_access_token}"}
            response = requests.get(user_url, headers=headers)
            
            if response.status_code == 200:
                user_info = response.json()
                user_data = user_info.get("data", {}).get("user", {})
                return {
                    "tiktok_id": user.tiktok_id,
                    "username": user_data.get("display_name"),
                    "follower_count": user_data.get("follower_count"),
                    "following_count": user_data.get("following_count"),
                    "avatar_url": user_data.get("avatar_url"),
                    "verified": user_data.get("is_verified"),
                    "connected": True
                }
        
        # Return cached data if token is invalid
        return {
            "tiktok_id": user.tiktok_id,
            "username": user.username,
            "connected": False
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching profile: {str(e)}")

@router.post("/disconnect")
async def disconnect_tiktok(
    user_id: int,
    db: Session = Depends(get_db)
):
    """Disconnect user's TikTok account"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Clear TikTok data
    user.tiktok_id = None
    user.tiktok_access_token = None
    db.commit()
    
    return {
        "success": True,
        "message": "TikTok account disconnected successfully"
    }

@router.get("/videos/{user_id}")
async def get_user_videos(
    user_id: int,
    max_count: int = 20,
    db: Session = Depends(get_db)
):
    """Get user's TikTok videos"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.tiktok_access_token:
        raise HTTPException(status_code=404, detail="User not found or not connected to TikTok")
    
    try:
        videos_url = f"{TIKTOK_API_BASE}/video/list/"
        headers = {"Authorization": f"Bearer {user.tiktok_access_token}"}
        params = {"max_count": max_count}
        
        response = requests.get(videos_url, headers=headers, params=params)
        response.raise_for_status()
        
        videos_data = response.json()
        return {
            "success": True,
            "videos": videos_data.get("data", {}).get("videos", []),
            "has_more": videos_data.get("data", {}).get("has_more", False)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching videos: {str(e)}")

@router.post("/create-viral-moment")
async def create_viral_moment(
    user_id: int,
    moment_type: str,  # "achievement", "streak", "workout", "milestone"
    title: str,
    description: str,
    hashtags: List[str],
    db: Session = Depends(get_db)
):
    """Create a viral moment for TikTok sharing"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.tiktok_access_token:
        raise HTTPException(status_code=404, detail="User not found or not connected to TikTok")
    
    # Generate viral content based on moment type
    viral_content = {
        "achievement": {
            "title": f"🏆 {title}",
            "description": f"{description}\n\n#GoodRunss #{moment_type.title()} #Fitness #Achievement #Motivation",
            "hashtags": ["GoodRunss", "Achievement", "Fitness", "Motivation"] + hashtags
        },
        "streak": {
            "title": f"🔥 {title}",
            "description": f"{description}\n\n#GoodRunss #Streak #Consistency #Fitness #Motivation",
            "hashtags": ["GoodRunss", "Streak", "Consistency", "Fitness"] + hashtags
        },
        "workout": {
            "title": f"💪 {title}",
            "description": f"{description}\n\n#GoodRunss #Workout #Fitness #Training #Motivation",
            "hashtags": ["GoodRunss", "Workout", "Fitness", "Training"] + hashtags
        },
        "milestone": {
            "title": f"🎯 {title}",
            "description": f"{description}\n\n#GoodRunss #Milestone #Progress #Fitness #Achievement",
            "hashtags": ["GoodRunss", "Milestone", "Progress", "Fitness"] + hashtags
        }
    }
    
    content = viral_content.get(moment_type, viral_content["achievement"])
    
    try:
        # Create TikTok post for viral moment
        post_data = {
            "post_info": {
                "title": content["title"],
                "description": content["description"],
                "privacy_level": "SELF_ONLY",
                "disable_duet": False,
                "disable_comment": False,
                "disable_stitch": False
            }
        }
        
        post_url = f"{TIKTOK_API_BASE}/post/publish/video/init/"
        headers = {
            "Authorization": f"Bearer {user.tiktok_access_token}",
            "Content-Type": "application/json"
        }
        
        response = requests.post(post_url, json=post_data, headers=headers)
        response.raise_for_status()
        
        return {
            "success": True,
            "message": "Viral moment created on TikTok",
            "content": content,
            "post_id": response.json().get("data", {}).get("publish_id")
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating viral moment: {str(e)}")

@router.get("/analytics/{user_id}")
async def get_tiktok_analytics(
    user_id: int,
    db: Session = Depends(get_db)
):
    """Get TikTok analytics for user"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.tiktok_access_token:
        raise HTTPException(status_code=404, detail="User not found or not connected to TikTok")
    
    try:
        # Get analytics data
        analytics_url = f"{TIKTOK_API_BASE}/video/query/"
        headers = {"Authorization": f"Bearer {user.tiktok_access_token}"}
        
        response = requests.get(analytics_url, headers=headers)
        response.raise_for_status()
        
        analytics_data = response.json()
        return {
            "success": True,
            "analytics": analytics_data.get("data", {}),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching analytics: {str(e)}")

@router.get("/trending-hashtags")
async def get_trending_hashtags():
    """Get trending fitness hashtags for TikTok"""
    trending_hashtags = [
        "#GoodRunss", "#Fitness", "#Workout", "#Motivation", "#Achievement",
        "#Basketball", "#Training", "#Sports", "#Healthy", "#Active",
        "#Progress", "#Goals", "#Success", "#Inspiration", "#Community",
        "#Teamwork", "#Challenge", "#Winner", "#Champion", "#Elite"
    ]
    
    return {
        "success": True,
        "trending_hashtags": trending_hashtags,
        "fitness_hashtags": trending_hashtags[:10],
        "motivation_hashtags": trending_hashtags[10:20]
    }
