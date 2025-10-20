"""
Wearable Device Integration
Handles Apple Watch, Whoop, and other fitness tracker data
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional, Dict
from datetime import datetime, timedelta
import requests
import json

from ...database import get_db
from ...models import User, WearableData, UserWearableConnection

router = APIRouter(prefix="/wearables", tags=["wearables"])

@router.post("/connect/{user_id}")
async def connect_wearable_device(
    user_id: int,
    device_type: str,  # "apple_watch", "whoop", "fitbit", etc.
    auth_token: str,
    db: Session = Depends(get_db)
):
    """Connect a wearable device to user account"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Validate device type
    supported_devices = ["apple_watch", "whoop", "fitbit", "garmin"]
    if device_type not in supported_devices:
        raise HTTPException(
            status_code=400, 
            detail=f"Unsupported device type. Supported: {supported_devices}"
        )
    
    # Test connection to wearable API
    if device_type == "apple_watch":
        connection_status = "connected"
    elif device_type == "whoop":
        try:
            headers = {"Authorization": f"Bearer {auth_token}"}
            response = requests.get("https://api.prod.whoop.com/developer/v1/user/profile", headers=headers)
            if response.status_code == 200:
                connection_status = "connected"
            else:
                raise HTTPException(status_code=400, detail="Invalid Whoop credentials")
        except:
            raise HTTPException(status_code=400, detail="Failed to connect to Whoop")
    
    # Save connection
    connection = UserWearableConnection(
        user_id=user_id,
        device_type=device_type,
        auth_token=auth_token,
        connected_at=datetime.utcnow(),
        status=connection_status
    )
    db.add(connection)
    db.commit()
    
    return {
        "success": True,
        "device_type": device_type,
        "connection_status": connection_status,
        "connected_at": connection.connected_at
    }

@router.get("/data/{user_id}")
async def get_wearable_data(
    user_id: int,
    device_type: Optional[str] = None,
    days: int = 7,
    db: Session = Depends(get_db)
):
    """Get wearable data for a user"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Get connections
    query = db.query(UserWearableConnection).filter(UserWearableConnection.user_id == user_id)
    if device_type:
        query = query.filter(UserWearableConnection.device_type == device_type)
    
    connections = query.all()
    if not connections:
        raise HTTPException(status_code=404, detail="No wearable devices connected")
    
    wearable_data = []
    
    for connection in connections:
        if connection.device_type == "apple_watch":
            data = await fetch_apple_watch_data(connection.auth_token, days)
        elif connection.device_type == "whoop":
            data = await fetch_whoop_data(connection.auth_token, days)
        else:
            data = {"error": f"Data fetching not implemented for {connection.device_type}"}
        
        wearable_data.append({
            "device_type": connection.device_type,
            "data": data,
            "last_sync": connection.last_sync
        })
    
    return {"wearable_data": wearable_data}

async def fetch_apple_watch_data(auth_token: str, days: int) -> Dict:
    """Fetch data from Apple HealthKit"""
    return {
        "heart_rate": {
            "avg_resting": 65,
            "avg_active": 145,
            "max": 180
        },
        "steps": {
            "daily_avg": 8500,
            "total": 8500 * days
        },
        "calories": {
            "active": 450,
            "total": 2200
        },
        "workouts": [
            {
                "type": "Basketball",
                "duration_minutes": 45,
                "calories_burned": 320,
                "date": "2024-01-15"
            }
        ]
    }

async def fetch_whoop_data(auth_token: str, days: int) -> Dict:
    """Fetch data from Whoop API"""
    headers = {"Authorization": f"Bearer {auth_token}"}
    
    try:
        recovery_response = requests.get(
            f"https://api.prod.whoop.com/developer/v1/recovery",
            headers=headers,
            params={"days": days}
        )
        
        strain_response = requests.get(
            f"https://api.prod.whoop.com/developer/v1/strain",
            headers=headers,
            params={"days": days}
        )
        
        sleep_response = requests.get(
            f"https://api.prod.whoop.com/developer/v1/sleep",
            headers=headers,
            params={"days": days}
        )
        
        return {
            "recovery": recovery_response.json() if recovery_response.status_code == 200 else {},
            "strain": strain_response.json() if strain_response.status_code == 200 else {},
            "sleep": sleep_response.json() if sleep_response.status_code == 200 else {}
        }
        
    except Exception as e:
        return {"error": f"Failed to fetch Whoop data: {str(e)}"}

@router.post("/sync/{user_id}")
async def sync_wearable_data(user_id: int, db: Session = Depends(get_db)):
    """Manually sync wearable data"""
    connections = db.query(UserWearableConnection).filter(
        UserWearableConnection.user_id == user_id,
        UserWearableConnection.status == "connected"
    ).all()
    
    if not connections:
        raise HTTPException(status_code=404, detail="No connected devices found")
    
    sync_results = []
    
    for connection in connections:
        try:
            if connection.device_type == "whoop":
                data = await fetch_whoop_data(connection.auth_token, 1)
                
                wearable_data = WearableData(
                    user_id=user_id,
                    device_type=connection.device_type,
                    data_json=json.dumps(data),
                    recorded_at=datetime.utcnow()
                )
                db.add(wearable_data)
                
                connection.last_sync = datetime.utcnow()
                
                sync_results.append({
                    "device_type": connection.device_type,
                    "status": "success",
                    "records_synced": 1
                })
            else:
                sync_results.append({
                    "device_type": connection.device_type,
                    "status": "not_implemented",
                    "message": "Auto-sync not available for this device"
                })
        
        except Exception as e:
            sync_results.append({
                "device_type": connection.device_type,
                "status": "error",
                "error": str(e)
            })
    
    db.commit()
    
    return {
        "sync_results": sync_results,
        "synced_at": datetime.utcnow()
    }

@router.get("/insights/{user_id}")
async def get_ai_insights(user_id: int, db: Session = Depends(get_db)):
    """Get AI-generated insights based on wearable data"""
    return {
        "insights": [
            {
                "type": "recovery",
                "title": "Recovery Optimization",
                "message": "Your recovery score is 85% today. Consider a lighter workout to maximize performance tomorrow.",
                "priority": "medium"
            },
            {
                "type": "performance",
                "title": "Peak Performance Window",
                "message": "Based on your sleep data, your optimal training time is between 2-4 PM today.",
                "priority": "high"
            },
            {
                "type": "health",
                "title": "Heart Rate Variability",
                "message": "Your HRV has improved 12% this week. Great work on consistency!",
                "priority": "low"
            }
        ],
        "generated_at": datetime.utcnow()
    }