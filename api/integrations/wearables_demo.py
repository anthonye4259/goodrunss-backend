"""
Wearables Integration - DEMO MODE
Test Apple Watch, Whoop, and Fitbit integration with simulated data
"""

from fastapi import APIRouter, HTTPException
from datetime import datetime, timedelta
import random

router = APIRouter(prefix="/wearables-demo", tags=["wearables_demo"])

@router.get("/apple-watch/demo/{user_id}")
async def get_demo_apple_watch_data(user_id: int):
    """Get simulated Apple Watch data for testing"""
    
    # Generate realistic demo data
    current_time = datetime.now()
    
    return {
        "user_id": user_id,
        "device": "Apple Watch Series 9",
        "last_sync": current_time.isoformat(),
        "data": {
            "heart_rate": {
                "current_bpm": random.randint(65, 85),
                "resting_bpm": random.randint(55, 70),
                "max_bpm": random.randint(150, 180),
                "avg_bpm": random.randint(70, 90),
                "measurement_time": current_time.isoformat()
            },
            "activity": {
                "steps": random.randint(5000, 12000),
                "distance_miles": round(random.uniform(2.5, 6.0), 2),
                "calories_burned": random.randint(300, 800),
                "active_minutes": random.randint(30, 90),
                "stand_hours": random.randint(8, 12),
                "exercise_minutes": random.randint(20, 60)
            },
            "workout_sessions": [
                {
                    "type": "Basketball",
                    "duration_minutes": 45,
                    "calories": 320,
                    "avg_heart_rate": 142,
                    "max_heart_rate": 175,
                    "start_time": (current_time - timedelta(hours=3)).isoformat(),
                    "end_time": (current_time - timedelta(hours=2, minutes=15)).isoformat()
                },
                {
                    "type": "Running",
                    "duration_minutes": 30,
                    "calories": 280,
                    "avg_heart_rate": 155,
                    "max_heart_rate": 182,
                    "distance_miles": 3.2,
                    "pace_per_mile": "9:22",
                    "start_time": (current_time - timedelta(days=1)).isoformat(),
                    "end_time": (current_time - timedelta(days=1) + timedelta(minutes=30)).isoformat()
                }
            ],
            "sleep": {
                "last_night_hours": round(random.uniform(6.5, 8.5), 1),
                "deep_sleep_hours": round(random.uniform(1.5, 2.5), 1),
                "rem_sleep_hours": round(random.uniform(1.0, 2.0), 1),
                "sleep_quality": random.choice(["Excellent", "Good", "Fair"]),
                "bed_time": "23:15",
                "wake_time": "07:00"
            },
            "vo2_max": round(random.uniform(42, 55), 1),
            "recovery_score": random.randint(70, 95)
        },
        "gia_recommendations": [
            "🏀 Your heart rate during basketball was in the optimal cardio zone. Great intensity!",
            f"💪 You've completed {random.randint(3, 5)} workouts this week. Keep up the consistency!",
            "😴 Your sleep quality is good. Aim for 8 hours for optimal recovery.",
            f"🎯 You're {random.randint(85, 95)}% toward your daily activity goal. Almost there!"
        ]
    }

@router.get("/whoop/demo/{user_id}")
async def get_demo_whoop_data(user_id: int):
    """Get simulated Whoop data for testing"""
    
    return {
        "user_id": user_id,
        "device": "Whoop 4.0",
        "last_sync": datetime.now().isoformat(),
        "data": {
            "recovery": {
                "score": random.randint(60, 95),
                "hrv": random.randint(50, 100),
                "resting_heart_rate": random.randint(48, 65),
                "status": random.choice(["Green", "Yellow", "Red"]),
                "recommendation": random.choice([
                    "Your body is well-recovered. Push hard today!",
                    "Moderate recovery. Stick to your training plan.",
                    "Low recovery. Consider active recovery today."
                ])
            },
            "strain": {
                "day_strain": round(random.uniform(12.0, 18.5), 1),
                "optimal_strain": round(random.uniform(14.0, 16.0), 1),
                "status": random.choice(["Optimal", "Undertraining", "Overreaching"])
            },
            "sleep": {
                "performance": random.randint(70, 98),
                "total_hours": round(random.uniform(7.0, 9.0), 1),
                "rem_hours": round(random.uniform(1.5, 2.5), 1),
                "slow_wave_hours": round(random.uniform(1.0, 2.0), 1),
                "disturbances": random.randint(2, 8),
                "respiratory_rate": round(random.uniform(13.5, 16.5), 1)
            },
            "workouts": [
                {
                    "sport": "Basketball",
                    "strain": 14.2,
                    "avg_heart_rate": 148,
                    "max_heart_rate": 178,
                    "calories": 425,
                    "duration_minutes": 55
                }
            ]
        },
        "gia_insights": [
            "🟢 Excellent recovery score! Your body is ready for high-intensity training.",
            "📊 Your strain is in the optimal zone for performance gains.",
            "😴 Sleep performance is strong. Keep this routine going!",
            "💡 Based on your HRV, consider a lower-intensity session tomorrow."
        ]
    }

@router.post("/sync/demo/{user_id}")
async def simulate_device_sync(user_id: int, device_type: str):
    """Simulate syncing data from a wearable device"""
    
    if device_type not in ["apple_watch", "whoop", "fitbit"]:
        raise HTTPException(status_code=400, detail="Invalid device type")
    
    return {
        "message": f"Successfully synced {device_type} data",
        "user_id": user_id,
        "device": device_type,
        "data_points_synced": random.randint(50, 200),
        "last_sync": datetime.now().isoformat(),
        "next_sync": (datetime.now() + timedelta(hours=1)).isoformat(),
        "status": "success"
    }

@router.get("/dashboard/demo/{user_id}")
async def get_demo_wearables_dashboard(user_id: int):
    """Get complete wearables dashboard with all metrics"""
    
    return {
        "user_id": user_id,
        "connected_devices": ["Apple Watch Series 9", "Whoop 4.0"],
        "last_updated": datetime.now().isoformat(),
        "summary": {
            "recovery_score": random.randint(70, 95),
            "daily_strain": round(random.uniform(12.0, 16.0), 1),
            "sleep_quality": random.randint(75, 95),
            "readiness": random.choice(["Ready", "Moderate", "Rest"]),
            "steps_today": random.randint(6000, 12000),
            "active_calories": random.randint(400, 800)
        },
        "weekly_trends": {
            "avg_recovery": random.randint(75, 88),
            "avg_strain": round(random.uniform(13.0, 15.0), 1),
            "avg_sleep_hours": round(random.uniform(7.2, 8.0), 1),
            "total_workouts": random.randint(4, 7),
            "total_active_minutes": random.randint(200, 400)
        },
        "gia_training_plan": {
            "today": {
                "recommended_intensity": random.choice(["High", "Moderate", "Low"]),
                "suggested_workouts": ["Basketball scrimmage", "Cardio session", "Strength training"],
                "optimal_duration": "45-60 minutes",
                "reason": "Based on your excellent recovery and moderate strain"
            },
            "this_week": {
                "high_intensity_days": 3,
                "moderate_days": 2,
                "recovery_days": 2,
                "focus": "Maintain consistency while building endurance"
            }
        },
        "health_insights": [
            "🎯 Your recovery has improved 12% this week - great job!",
            "💪 You're averaging 5 workouts per week. This is optimal for progress.",
            "😴 Sleep quality is consistent. Keep your bedtime routine.",
            "🏃 Consider adding one more cardio session to reach peak fitness.",
            "📈 HRV trending upward - your training is working!"
        ]
    }

@router.get("/recommendations/demo/{user_id}")
async def get_demo_ai_recommendations(user_id: int):
    """Get AI-powered training recommendations based on wearable data"""
    
    recovery = random.randint(60, 95)
    
    if recovery >= 80:
        intensity = "High"
        workouts = ["Intense basketball scrimmage", "HIIT training", "Strength & power workout"]
        message = "Your recovery is excellent! This is a great day to push hard."
    elif recovery >= 65:
        intensity = "Moderate"
        workouts = ["Moderate basketball practice", "Steady-state cardio", "Skill development"]
        message = "Good recovery. Stick to your normal training intensity."
    else:
        intensity = "Low"
        workouts = ["Light shooting practice", "Yoga/stretching", "Active recovery walk"]
        message = "Low recovery detected. Focus on active recovery today."
    
    return {
        "user_id": user_id,
        "generated_at": datetime.now().isoformat(),
        "recovery_score": recovery,
        "recommended_intensity": intensity,
        "message": message,
        "suggested_workouts": workouts,
        "nutrition_tips": [
            "💧 Hydrate with 80oz of water today",
            "🥗 Focus on protein for muscle recovery",
            "🍌 Eat carbs 1-2 hours before training"
        ],
        "recovery_tips": [
            "😴 Aim for 8+ hours of sleep tonight",
            "🧊 Consider ice bath after high-intensity session",
            "🧘 Do 10 minutes of stretching post-workout"
        ],
        "performance_prediction": {
            "optimal_training_window": "4:00 PM - 7:00 PM",
            "expected_performance": random.randint(75, 95),
            "injury_risk": "Low" if recovery >= 70 else "Moderate"
        }
    }

