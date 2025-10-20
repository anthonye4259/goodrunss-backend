"""
HealthKit Integration - Receive and process Apple Watch data
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime
import os

router = APIRouter(prefix="/healthkit", tags=["healthkit"])

# In-memory storage (replace with database in production)
health_data_store: Dict[int, Dict[str, Any]] = {}

class HealthMetrics(BaseModel):
    heart_rate: Optional[int] = None
    steps: Optional[int] = None
    active_calories: Optional[int] = None
    vo2_max: Optional[float] = None
    sleep_hours: Optional[float] = None

class WorkoutData(BaseModel):
    type: str
    start_date: str
    end_date: str
    duration_minutes: int
    calories: int
    distance_miles: Optional[float] = None

class HealthKitSyncRequest(BaseModel):
    user_id: int
    device_type: str
    timestamp: str
    heart_rate: Optional[int] = None
    steps: Optional[int] = None
    active_calories: Optional[int] = None
    vo2_max: Optional[float] = None
    sleep_hours: Optional[float] = None
    workouts: Optional[List[WorkoutData]] = []

@router.post("/sync/{user_id}")
async def sync_healthkit_data(user_id: int, data: HealthKitSyncRequest):
    """Receive and store HealthKit data from iOS app"""
    
    # Store the data
    health_data_store[user_id] = {
        "user_id": user_id,
        "device_type": data.device_type,
        "last_sync": data.timestamp,
        "metrics": {
            "heart_rate": data.heart_rate,
            "steps": data.steps,
            "active_calories": data.active_calories,
            "vo2_max": data.vo2_max,
            "sleep_hours": data.sleep_hours
        },
        "workouts": [workout.dict() for workout in (data.workouts or [])],
        "synced_at": datetime.now().isoformat()
    }
    
    print(f"✅ Received HealthKit data from user {user_id}:")
    print(f"   💓 Heart Rate: {data.heart_rate} BPM")
    print(f"   🚶 Steps: {data.steps}")
    print(f"   🔥 Calories: {data.active_calories}")
    print(f"   💨 VO2 Max: {data.vo2_max}")
    print(f"   😴 Sleep: {data.sleep_hours} hours")
    print(f"   🏃 Workouts: {len(data.workouts or [])}")
    
    # Generate AI recommendations
    recommendations = generate_ai_recommendations(data)
    
    return {
        "message": "HealthKit data synced successfully",
        "user_id": user_id,
        "data_points_received": sum([
            1 if data.heart_rate else 0,
            1 if data.steps else 0,
            1 if data.active_calories else 0,
            1 if data.vo2_max else 0,
            1 if data.sleep_hours else 0,
            len(data.workouts or [])
        ]),
        "recommendations": recommendations,
        "next_sync": "In 1 hour"
    }

@router.get("/data/{user_id}")
async def get_healthkit_data(user_id: int):
    """Get stored HealthKit data for a user"""
    
    if user_id not in health_data_store:
        raise HTTPException(status_code=404, detail="No health data found for this user")
    
    return health_data_store[user_id]

@router.get("/recommendations/{user_id}")
async def get_health_recommendations(user_id: int):
    """Get AI-powered training recommendations based on health data"""
    
    if user_id not in health_data_store:
        return {
            "message": "No health data available yet. Sync your Apple Watch first!",
            "recommendations": [
                "⌚ Connect your Apple Watch to get started",
                "🏃 Go for a run to collect workout data",
                "😴 Wear your watch while sleeping for sleep insights"
            ]
        }
    
    data = health_data_store[user_id]
    metrics = data.get("metrics", {})
    
    # Generate recommendations based on data
    recommendations = []
    
    # Heart rate recommendations
    if metrics.get("heart_rate"):
        hr = metrics["heart_rate"]
        if hr < 60:
            recommendations.append("💓 Your resting heart rate is excellent! You're in great cardiovascular shape.")
        elif hr < 100:
            recommendations.append("💓 Your heart rate is in a healthy range. Keep up the good work!")
        else:
            recommendations.append("💓 Your heart rate is elevated. Consider some relaxation techniques.")
    
    # Steps recommendations
    if metrics.get("steps"):
        steps = metrics["steps"]
        if steps >= 10000:
            recommendations.append(f"🚶 Amazing! You've hit {steps:,} steps today. You're crushing your goals!")
        elif steps >= 7000:
            recommendations.append(f"🚶 Great job! {steps:,} steps and counting. Almost at 10K!")
        else:
            recommendations.append(f"🚶 You're at {steps:,} steps. Try to hit 10,000 for optimal health!")
    
    # Sleep recommendations
    if metrics.get("sleep_hours"):
        sleep = metrics["sleep_hours"]
        if sleep >= 8:
            recommendations.append(f"😴 Excellent sleep! {sleep:.1f} hours is perfect for recovery.")
        elif sleep >= 7:
            recommendations.append(f"😴 Good sleep at {sleep:.1f} hours. Aim for 8+ for peak performance.")
        else:
            recommendations.append(f"😴 Only {sleep:.1f} hours of sleep. Try to get more rest tonight!")
    
    # VO2 Max recommendations
    if metrics.get("vo2_max"):
        vo2 = metrics["vo2_max"]
        if vo2 >= 50:
            recommendations.append(f"💨 Outstanding VO2 Max of {vo2:.1f}! You're in elite cardio shape.")
        elif vo2 >= 40:
            recommendations.append(f"💨 Good VO2 Max at {vo2:.1f}. You're above average!")
        else:
            recommendations.append(f"💨 VO2 Max is {vo2:.1f}. Focus on cardio to improve.")
    
    # Workout recommendations
    workouts = data.get("workouts", [])
    if len(workouts) > 0:
        recommendations.append(f"🏃 You've completed {len(workouts)} workout(s) recently. Consistency is key!")
    
    # Training intensity recommendations
    training_plan = generate_training_plan(metrics)
    
    return {
        "user_id": user_id,
        "last_sync": data.get("last_sync"),
        "recommendations": recommendations,
        "training_plan": training_plan,
        "health_score": calculate_health_score(metrics),
        "next_steps": [
            "🎯 Book a training session to improve your skills",
            "🏀 Find a nearby court for practice",
            "💪 Maintain your current workout schedule"
        ]
    }

@router.get("/stats/{user_id}")
async def get_health_stats(user_id: int):
    """Get comprehensive health statistics and trends"""
    
    if user_id not in health_data_store:
        raise HTTPException(status_code=404, detail="No health data found")
    
    data = health_data_store[user_id]
    metrics = data.get("metrics", {})
    
    return {
        "user_id": user_id,
        "current_metrics": metrics,
        "health_score": calculate_health_score(metrics),
        "weekly_summary": {
            "workouts_completed": len(data.get("workouts", [])),
            "average_steps": metrics.get("steps", 0),
            "average_sleep": metrics.get("sleep_hours", 0),
            "total_calories": metrics.get("active_calories", 0)
        },
        "achievements": generate_achievements(metrics),
        "insights": generate_insights(metrics)
    }

# Helper functions

def generate_ai_recommendations(data: HealthKitSyncRequest) -> List[str]:
    """Generate AI-powered recommendations based on health data"""
    recommendations = []
    
    if data.heart_rate and data.heart_rate < 60:
        recommendations.append("💓 Excellent resting heart rate! Your cardiovascular health is strong.")
    
    if data.steps and data.steps >= 10000:
        recommendations.append(f"🚶 Outstanding! {data.steps:,} steps today. You're hitting your goals!")
    
    if data.vo2_max and data.vo2_max >= 45:
        recommendations.append(f"💨 Your VO2 Max of {data.vo2_max:.1f} is excellent. Keep it up!")
    
    if data.sleep_hours and data.sleep_hours >= 7.5:
        recommendations.append(f"😴 Great sleep quality at {data.sleep_hours:.1f} hours!")
    
    if not recommendations:
        recommendations.append("🎯 Keep wearing your Apple Watch to get personalized insights!")
    
    return recommendations

def generate_training_plan(metrics: Dict) -> Dict:
    """Generate training plan based on current metrics"""
    
    # Determine recovery status
    sleep = metrics.get("sleep_hours", 0)
    hr = metrics.get("heart_rate", 70)
    
    if sleep >= 8 and hr < 60:
        intensity = "High"
        message = "Your body is well-recovered. Great day for intense training!"
    elif sleep >= 7 and hr < 75:
        intensity = "Moderate"
        message = "Good recovery. Stick to your normal training intensity."
    else:
        intensity = "Light"
        message = "Consider active recovery today. Your body needs rest."
    
    return {
        "recommended_intensity": intensity,
        "message": message,
        "suggested_activities": get_suggested_activities(intensity),
        "optimal_training_time": "4:00 PM - 7:00 PM",
        "duration": "45-60 minutes"
    }

def get_suggested_activities(intensity: str) -> List[str]:
    """Get activity suggestions based on intensity level"""
    if intensity == "High":
        return [
            "🏀 Intense basketball scrimmage",
            "🏃 HIIT training session",
            "💪 Strength & power workout"
        ]
    elif intensity == "Moderate":
        return [
            "🏀 Moderate basketball practice",
            "🏃 Steady-state cardio",
            "🎯 Skill development drills"
        ]
    else:
        return [
            "🏀 Light shooting practice",
            "🧘 Yoga & stretching",
            "🚶 Active recovery walk"
        ]

def calculate_health_score(metrics: Dict) -> int:
    """Calculate overall health score (0-100)"""
    score = 50  # Base score
    
    # Heart rate contribution
    if metrics.get("heart_rate"):
        hr = metrics["heart_rate"]
        if hr < 60:
            score += 15
        elif hr < 75:
            score += 10
        elif hr < 100:
            score += 5
    
    # Steps contribution
    if metrics.get("steps"):
        steps = metrics["steps"]
        if steps >= 10000:
            score += 15
        elif steps >= 7000:
            score += 10
        elif steps >= 5000:
            score += 5
    
    # Sleep contribution
    if metrics.get("sleep_hours"):
        sleep = metrics["sleep_hours"]
        if sleep >= 8:
            score += 10
        elif sleep >= 7:
            score += 7
        elif sleep >= 6:
            score += 3
    
    # VO2 Max contribution
    if metrics.get("vo2_max"):
        vo2 = metrics["vo2_max"]
        if vo2 >= 50:
            score += 10
        elif vo2 >= 40:
            score += 7
        elif vo2 >= 30:
            score += 3
    
    return min(score, 100)  # Cap at 100

def generate_achievements(metrics: Dict) -> List[str]:
    """Generate achievement badges based on metrics"""
    achievements = []
    
    if metrics.get("steps", 0) >= 10000:
        achievements.append("🏆 10K Steps Master")
    
    if metrics.get("sleep_hours", 0) >= 8:
        achievements.append("😴 Sleep Champion")
    
    if metrics.get("vo2_max", 0) >= 50:
        achievements.append("💨 Cardio Elite")
    
    if metrics.get("heart_rate", 100) < 60:
        achievements.append("💓 Athlete Heart")
    
    return achievements

def generate_insights(metrics: Dict) -> List[str]:
    """Generate data-driven insights"""
    insights = []
    
    steps = metrics.get("steps", 0)
    if steps > 0:
        miles = steps * 0.0005  # Rough conversion
        insights.append(f"📊 You've walked approximately {miles:.1f} miles today")
    
    calories = metrics.get("active_calories", 0)
    if calories > 0:
        basketball_minutes = calories / 8  # ~8 cal/min for basketball
        insights.append(f"🏀 That's equivalent to {basketball_minutes:.0f} minutes of basketball")
    
    sleep = metrics.get("sleep_hours", 0)
    if sleep > 0:
        sleep_quality = "excellent" if sleep >= 8 else "good" if sleep >= 7 else "fair"
        insights.append(f"😴 Your {sleep:.1f} hours of sleep is {sleep_quality}")
    
    return insights

@router.get("/status/{user_id}")
async def get_healthkit_status(user_id: int):
    """Check if user has synced HealthKit data"""
    
    has_data = user_id in health_data_store
    
    if has_data:
        data = health_data_store[user_id]
        return {
            "connected": True,
            "last_sync": data.get("last_sync"),
            "device": data.get("device_type"),
            "data_points": len([v for v in data.get("metrics", {}).values() if v is not None])
        }
    else:
        return {
            "connected": False,
            "message": "No HealthKit data synced yet. Open the iOS app to connect your Apple Watch."
        }

