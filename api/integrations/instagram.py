"""
Instagram Integration
Handles Instagram posting, stories, and social sharing
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional, Dict
from datetime import datetime
import requests
import json

from ...database import get_db
from ...models import User, SocialIntegration

router = APIRouter(prefix="/instagram", tags=["instagram"])

@router.post("/connect/{user_id}")
async def connect_instagram(user_id: int, access_token: str, db: Session = Depends(get_db)):
    """Connect Instagram account"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    try:
        # Verify Instagram access token
        verify_url = f"https://graph.instagram.com/me?fields=id,username&access_token={access_token}"
        response = requests.get(verify_url)
        
        if response.status_code != 200:
            raise HTTPException(status_code=400, detail="Invalid Instagram access token")
        
        user_data = response.json()
        
        # Save integration
        social_integration = SocialIntegration(
            user_id=user_id,
            provider="instagram",
            access_token=access_token,
            provider_user_id=user_data.get("id"),
            provider_username=user_data.get("username"),
            connected_at=datetime.utcnow(),
            status="connected"
        )
        db.add(social_integration)
        db.commit()
        
        return {
            "success": True,
            "message": "Instagram connected successfully",
            "username": user_data.get("username"),
            "connected_at": social_integration.connected_at
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Instagram connection failed: {str(e)}")

@router.post("/post-achievement/{user_id}")
async def post_achievement_to_instagram(
    user_id: int,
    achievement_name: str,
    achievement_description: str,
    achievement_image_url: str,
    db: Session = Depends(get_db)
):
    """Post achievement to Instagram"""
    social_integration = db.query(SocialIntegration).filter(
        SocialIntegration.user_id == user_id,
        SocialIntegration.provider == "instagram"
    ).first()
    
    if not social_integration:
        raise HTTPException(status_code=404, detail="Instagram not connected")
    
    caption = f"""
🏆 {achievement_name}

{achievement_description}

Just leveled up my game with GoodRunss! 🚀

#GoodRunss #Basketball #Training #Achievement #LevelUp
    """.strip()
    
    try:
        # Create media container
        container_url = f"https://graph.instagram.com/{social_integration.provider_user_id}/media"
        
        container_data = {
            "image_url": achievement_image_url,
            "caption": caption,
            "access_token": social_integration.access_token
        }
        
        container_response = requests.post(container_url, data=container_data)
        
        if container_response.status_code != 200:
            raise HTTPException(status_code=400, detail="Failed to create media container")
        
        container_id = container_response.json().get("id")
        
        # Publish the media
        publish_url = f"https://graph.instagram.com/{social_integration.provider_user_id}/media_publish"
        
        publish_data = {
            "creation_id": container_id,
            "access_token": social_integration.access_token
        }
        
        publish_response = requests.post(publish_url, data=publish_data)
        
        if publish_response.status_code != 200:
            raise HTTPException(status_code=400, detail="Failed to publish post")
        
        post_id = publish_response.json().get("id")
        
        return {
            "success": True,
            "post_id": post_id,
            "container_id": container_id,
            "caption": caption
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to post to Instagram: {str(e)}")