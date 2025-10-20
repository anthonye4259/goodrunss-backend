"""
Google Maps Integration
Handles location services, directions, and mapping
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Tuple
from datetime import datetime
import requests
import math
import os

from ...database import get_db
from ...models import User, Court

router = APIRouter(prefix="/maps", tags=["maps"])

# Google Maps API configuration
GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")

@router.post("/geocode")
async def geocode_address(address: str):
    """Convert address to coordinates"""
    if not GOOGLE_MAPS_API_KEY:
        raise HTTPException(status_code=500, detail="Google Maps API not configured")
    
    try:
        geocode_url = "https://maps.googleapis.com/maps/api/geocode/json"
        params = {
            "address": address,
            "key": GOOGLE_MAPS_API_KEY
        }
        
        response = requests.get(geocode_url, params=params)
        data = response.json()
        
        if data["status"] != "OK":
            raise HTTPException(status_code=400, detail=f"Geocoding failed: {data['status']}")
        
        location = data["results"][0]["geometry"]["location"]
        
        return {
            "address": address,
            "latitude": location["lat"],
            "longitude": location["lng"],
            "formatted_address": data["results"][0]["formatted_address"]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Geocoding error: {str(e)}")

@router.post("/nearby-courts")
async def find_nearby_courts(
    latitude: float,
    longitude: float,
    radius_km: float = 10.0,
    limit: int = 20,
    db: Session = Depends(get_db)
):
    """Find nearby basketball courts"""
    try:
        # Get all courts within radius (using Haversine formula)
        courts = db.query(Court).all()
        nearby_courts = []
        
        for court in courts:
            distance = calculate_distance(
                latitude,
                longitude,
                court.latitude,
                court.longitude
            )
            
            if distance <= radius_km:
                nearby_courts.append({
                    "id": court.id,
                    "name": court.name,
                    "address": court.address,
                    "latitude": court.latitude,
                    "longitude": court.longitude,
                    "distance_km": round(distance, 2),
                    "available": court.available,
                    "price_per_hour": court.price_per_hour
                })
        
        # Sort by distance
        nearby_courts.sort(key=lambda x: x["distance_km"])
        
        return {
            "courts": nearby_courts[:limit],
            "count": len(nearby_courts),
            "search_center": {
                "latitude": latitude,
                "longitude": longitude
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Nearby courts error: {str(e)}")

def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate distance between two points using Haversine formula"""
    R = 6371  # Earth's radius in kilometers
    
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    
    a = (math.sin(dlat/2) * math.sin(dlat/2) +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
         math.sin(dlon/2) * math.sin(dlon/2))
    
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    distance = R * c
    
    return distance