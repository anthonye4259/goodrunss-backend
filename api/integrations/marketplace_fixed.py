"""
Marketplace Integration - FIXED VERSION
No database dependencies that cause Pydantic errors
"""

from fastapi import APIRouter, HTTPException
from typing import Optional, List, Dict
from datetime import datetime
from math import radians, sin, cos, sqrt, atan2
import json

router = APIRouter(prefix="/marketplace", tags=["marketplace"])

def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate distance between two coordinates in miles"""
    R = 3959
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1-a))
    return round(R * c, 1)

# Sample data for testing
SAMPLE_LISTINGS = [
    {
        "id": 1,
        "title": "Wilson Basketball - Like New",
        "description": "Official NBA game ball, barely used.",
        "price": 25.00,
        "type": "sell",
        "condition": "Like New",
        "category": "basketball",
        "seller": "Mike Johnson",
        "distance": "0.5 miles",
        "image": "/basketball-action.png",
        "zip_code": "10001",
        "latitude": 40.75,
        "longitude": -73.98,
        "is_available": True,
        "created_at": datetime.utcnow().isoformat()
    },
    {
        "id": 2,
        "title": "Tennis Racket - Wilson Pro Staff",
        "description": "High-performance racket, great for intermediate players.",
        "price": 15.00,
        "type": "rent",
        "rental_period": "per day",
        "condition": "Good",
        "category": "tennis",
        "seller": "Sarah Chen",
        "distance": "1.2 miles",
        "image": "/tennis-racket.png",
        "zip_code": "10001",
        "latitude": 40.76,
        "longitude": -73.97,
        "is_available": True,
        "created_at": datetime.utcnow().isoformat()
    }
]

@router.get("/listings")
async def get_marketplace_listings(
    type: Optional[str] = None,
    category: Optional[str] = None,
    search: Optional[str] = None,
    zip_code: Optional[str] = None,
    user_lat: float = 40.7489,  # Default to Empire State Building for demo
    user_lon: float = -73.9680  # Default to Empire State Building for demo
):
    """Get marketplace listings with optional filters and search."""
    filtered = SAMPLE_LISTINGS.copy()

    if type:
        filtered = [l for l in filtered if l["type"].lower() == type.lower()]
    if category:
        filtered = [l for l in filtered if l["category"].lower() == category.lower()]
    if search:
        search_lower = search.lower()
        filtered = [l for l in filtered if search_lower in l["title"].lower() or search_lower in l["description"].lower()]

    # Calculate distances
    for listing in filtered:
        distance = calculate_distance(user_lat, user_lon, listing["latitude"], listing["longitude"])
        listing["distance"] = f"{distance} miles"

    # Sort by distance
    filtered.sort(key=lambda x: float(x["distance"].split()[0]))

    return {
        "listings": filtered,
        "total": len(filtered),
        "filters": {
            "type": type,
            "category": category,
            "search": search,
            "zip_code": zip_code
        }
    }

@router.get("/listings/{listing_id}")
async def get_listing(listing_id: int):
    """Get a specific marketplace listing by ID."""
    listing = next((l for l in SAMPLE_LISTINGS if l["id"] == listing_id), None)
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
    return listing

@router.post("/listings")
async def create_listing(listing_data: dict):
    """Create a new marketplace listing."""
    new_id = max([l["id"] for l in SAMPLE_LISTINGS]) + 1 if SAMPLE_LISTINGS else 1
    new_listing = {
        "id": new_id,
        "title": listing_data.get("title", ""),
        "description": listing_data.get("description", ""),
        "price": listing_data.get("price", 0.0),
        "type": listing_data.get("type", "sell"),
        "rental_period": listing_data.get("rental_period"),
        "condition": listing_data.get("condition", "Good"),
        "category": listing_data.get("category", "sports"),
        "seller": listing_data.get("seller", "Anonymous"),
        "zip_code": listing_data.get("zip_code", ""),
        "latitude": listing_data.get("latitude", 40.7489),
        "longitude": listing_data.get("longitude", -73.9680),
        "image": listing_data.get("image"),
        "is_available": True,
        "created_at": datetime.utcnow().isoformat()
    }
    SAMPLE_LISTINGS.append(new_listing)
    return new_listing

@router.delete("/listings/{listing_id}")
async def delete_listing(listing_id: int):
    """Delete a marketplace listing."""
    global SAMPLE_LISTINGS
    SAMPLE_LISTINGS = [l for l in SAMPLE_LISTINGS if l["id"] != listing_id]
    return {"message": "Listing deleted successfully"}

@router.get("/categories")
async def get_categories():
    """Get available marketplace categories."""
    return {
        "categories": ["basketball", "tennis", "golf", "soccer", "baseball", "volleyball", "equipment", "accessories"]
    }

