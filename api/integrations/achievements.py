"""
Achievement and Viral Moments System
Handles achievements, streaks, points, and social sharing
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta
import json

from ...database import get_db
from ...models import User, Achievement, UserAchievement, Booking, Game
from ...schemas import AchievementResponse, ViralMomentRequest

router = APIRouter(prefix="/achievements", tags=["achievements"])

# Achievement definitions
ACHIEVEMENTS = {
    "first_booking": {
        "name": "First Steps",
        "description": "Booked your first training session",
        "points": 50,
        "icon": "🏆",
        "viral_text": "I just booked my first run via GIA! 🚀"
    },
    "seven_day_streak": {
        "name": "Consistency King",
        "description": "7-day training streak",
        "points": 100,
        "icon": "🔥",
        "reward": "Free Training Session",
        "viral_text": "My 7-day streak unlocked a free session! 🔥"
    },
    "quick_court_find": {
        "name": "Court Master",
        "description": "Found a court in under 30 seconds",
        "points": 75,
        "icon": "⚡",
        "viral_text": "GIA found me a court in 30 seconds! ⚡"
    },
    "perfect_game": {
        "name": "Perfect Performance",
        "description": "Achieved a perfect game score",
        "points": 150,
        "icon": "🎯",
        "viral_text": "Just had a perfect game! 🎯"
    },
    "social_sharer": {
        "name": "Social Butterfly",
        "description": "Shared 5 achievements",
        "points": 25,
        "icon": "📱",
        "viral_text": "Leveling up my game with GoodRunss! 📱"
    }
}

@router.get("/user/{user_id}")
async def get_user_achievements(user_id: int, db: Session = Depends(get_db)):
    """Get all achievements for a user"""
    user_achievements = db.query(UserAchievement).filter(
        UserAchievement.user_id == user_id
    ).all()
    
    achievements = []
    for ua in user_achievements:
        achievement_data = ACHIEVEMENTS.get(ua.achievement_key)
        if achievement_data:
            achievements.append({
                "id": ua.id,
                "key": ua.achievement_key,
                "name": achievement_data["name"],
                "description": achievement_data["description"],
                "points": achievement_data["points"],
                "icon": achievement_data["icon"],
                "unlocked_at": ua.unlocked_at,
                "shared": ua.shared
            })
    
    return {"achievements": achievements}

@router.post("/check/{user_id}")
async def check_achievements(user_id: int, db: Session = Depends(get_db)):
    """Check and unlock new achievements for a user"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    new_achievements = []
    
    # Check first booking achievement
    bookings_count = db.query(Booking).filter(Booking.user_id == user_id).count()
    if bookings_count >= 1:
        achievement_key = "first_booking"
        existing = db.query(UserAchievement).filter(
            UserAchievement.user_id == user_id,
            UserAchievement.achievement_key == achievement_key
        ).first()
        
        if not existing:
            user_achievement = UserAchievement(
                user_id=user_id,
                achievement_key=achievement_key,
                unlocked_at=datetime.utcnow()
            )
            db.add(user_achievement)
            new_achievements.append(achievement_key)
    
    # Check 7-day streak
    seven_days_ago = datetime.utcnow() - timedelta(days=7)
    recent_bookings = db.query(Booking).filter(
        Booking.user_id == user_id,
        Booking.created_at >= seven_days_ago
    ).count()
    
    if recent_bookings >= 7:
        achievement_key = "seven_day_streak"
        existing = db.query(UserAchievement).filter(
            UserAchievement.user_id == user_id,
            UserAchievement.achievement_key == achievement_key
        ).first()
        
        if not existing:
            user_achievement = UserAchievement(
                user_id=user_id,
                achievement_key=achievement_key,
                unlocked_at=datetime.utcnow()
            )
            db.add(user_achievement)
            new_achievements.append(achievement_key)
    
    # Check perfect game
    perfect_games = db.query(Game).filter(
        Game.user_id == user_id,
        Game.score == 100
    ).count()
    
    if perfect_games >= 1:
        achievement_key = "perfect_game"
        existing = db.query(UserAchievement).filter(
            UserAchievement.user_id == user_id,
            UserAchievement.achievement_key == achievement_key
        ).first()
        
        if not existing:
            user_achievement = UserAchievement(
                user_id=user_id,
                achievement_key=achievement_key,
                unlocked_at=datetime.utcnow()
            )
            db.add(user_achievement)
            new_achievements.append(achievement_key)
    
    db.commit()
    
    # Return newly unlocked achievements with viral text
    unlocked_achievements = []
    for key in new_achievements:
        achievement_data = ACHIEVEMENTS[key]
        unlocked_achievements.append({
            "key": key,
            "name": achievement_data["name"],
            "description": achievement_data["description"],
            "points": achievement_data["points"],
            "icon": achievement_data["icon"],
            "viral_text": achievement_data["viral_text"],
            "reward": achievement_data.get("reward")
        })
    
    return {
        "new_achievements": unlocked_achievements,
        "count": len(unlocked_achievements)
    }

@router.post("/share/{user_id}/{achievement_key}")
async def share_achievement(
    user_id: int, 
    achievement_key: str, 
    platform: str,
    db: Session = Depends(get_db)
):
    """Mark an achievement as shared on social media"""
    user_achievement = db.query(UserAchievement).filter(
        UserAchievement.user_id == user_id,
        UserAchievement.achievement_key == achievement_key
    ).first()
    
    if not user_achievement:
        raise HTTPException(status_code=404, detail="Achievement not found")
    
    user_achievement.shared = True
    user_achievement.shared_platform = platform
    user_achievement.shared_at = datetime.utcnow()
    
    db.commit()
    
    # Award sharing points
    achievement_data = ACHIEVEMENTS.get(achievement_key)
    if achievement_data:
        return {
            "success": True,
            "viral_text": achievement_data["viral_text"],
            "points_awarded": 5  # Bonus points for sharing
        }
    
    return {"success": True}

@router.get("/leaderboard")
async def get_achievement_leaderboard(db: Session = Depends(get_db)):
    """Get top users by achievement points"""
    # This would calculate total points per user
    # For now, return mock data
    return {
        "leaderboard": [
            {
                "user_id": 1,
                "username": "BallPlayer123",
                "total_points": 450,
                "achievements_count": 8,
                "rank": 1
            },
            {
                "user_id": 2,
                "username": "CourtMaster",
                "total_points": 380,
                "achievements_count": 6,
                "rank": 2
            }
        ]
    }