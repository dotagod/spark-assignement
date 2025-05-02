from fastapi import FastAPI, HTTPException
from matchmaker import MatchMaker
from models import Profile, Location
from typing import List, Dict, Any
import sys
sys.path.append('.')
from generate_dummy_data import generate_user_data

app = FastAPI(title="Matchmaking Engine")
matchmaker = MatchMaker()

@app.post("/profiles")
async def create_profile(profile: Profile) -> Dict[str, str]:
    """Create a new user profile."""
    try:
        matchmaker.add_profile(profile)
        return {"message": f"Profile created successfully for user {profile.id}"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.put("/profiles/{user_id}")
async def update_profile(user_id: str, profile: Profile) -> Dict[str, str]:
    """Update an existing user profile.
    
    Args:
        user_id: ID of the user to update
        profile: Updated profile data
    """
    try:
        matchmaker.update_profile(user_id, profile)
        return {"message": f"Profile updated successfully for user {user_id}"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/profiles/bulk")
async def bulk_create_profiles(profiles: List[Profile]) -> Dict[str, str]:
    """Bulk create user profiles."""
    try:
        matchmaker.bulk_add_profiles(profiles)
        return {"message": f"Profiles created successfully for users {', '.join([p.id for p in profiles])}"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/profiles/{user_id}/matches")
async def get_matches(
    user_id: str, 
    gender_preference: str = None,
    page: int = 1,
    page_size: int = 5
) -> Dict[str, Any]:
    """Get paginated matches for a user across all nearby quadrants.
    
    Args:
        user_id: ID of the user to find matches for
        gender_preference: Optional gender preference
        page: Page number (1-indexed)
        page_size: Number of matches per page
    """
    if user_id not in matchmaker.profiles:
        raise HTTPException(status_code=404, detail="User not found")
    
    if page < 1:
        raise HTTPException(status_code=400, detail="Page must be greater than 0")
    
    if page_size < 1 or page_size > 50:
        raise HTTPException(status_code=400, detail="Page size must be between 1 and 50")
    
    limit = page_size
    offset = (page - 1) * page_size
    
    all_matches = matchmaker.get_matches(user_id, limit=100, gender_preference=gender_preference)
    total_matches = len(all_matches)
    total_pages = (total_matches + page_size - 1) // page_size
    
    paginated_matches = all_matches[offset:offset + limit] if offset < total_matches else []
    
    results = [
        {
            "id": match_id,
            "score": score,
            "profile": matchmaker.profiles[match_id].dict()
        }
        for match_id, score in paginated_matches
    ]
    
    return {
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
        "total_matches": total_matches,
        "results": results,
        "has_next": page < total_pages,
        "has_prev": page > 1
    }

@app.post("/profiles/{user_id}/exclusions")
async def add_exclusion(
    user_id: str,
    excluded_user: Dict[str, str]
) -> Dict[str, str]:
    """Add a user to an exclusion list (blocked/matched/disliked).
    
    Args:
        user_id: ID of the user to add an exclusion for
        excluded_user: Dictionary containing excluded_id and type
            - excluded_id: ID of the user to exclude
            - type: Type of exclusion (blocked/matched/disliked)
    """
    if user_id not in matchmaker.profiles:
        raise HTTPException(status_code=404, detail="User not found")
        
    excluded_id = excluded_user.get("excluded_id")
    exclusion_type = excluded_user.get("type")
    
    if not excluded_id:
        raise HTTPException(status_code=400, detail="excluded_id is required")
    if not exclusion_type:
        raise HTTPException(status_code=400, detail="type is required")
    
    if excluded_id not in matchmaker.profiles:
        raise HTTPException(status_code=404, detail="Excluded user not found")
    if exclusion_type not in ["blocked", "matched", "disliked"]:
        raise HTTPException(status_code=400, detail="Invalid exclusion type")
    
    matchmaker.add_exclusion(user_id, excluded_id, exclusion_type)
    return {"message": f"User {excluded_id} added to {exclusion_type} list for user {user_id}"}

@app.get("/profiles")
async def get_all_profiles() -> List[Dict[str, Any]]:
    """Get all user profiles in the system."""
    return [profile.dict() for profile in matchmaker.profiles.values()]

@app.get("/quadrants/{quadrant}/profiles")
async def get_profiles_by_quadrant(quadrant: str) -> List[Dict[str, Any]]:
    """Get profiles in a specific geohash quadrant.
    
    Args:
        quadrant: Geohash quadrant string
    """
    user_ids = matchmaker.geo_index.get_users_in_quadrant(quadrant)
    return [matchmaker.profiles[user_id].dict() for user_id in user_ids]

@app.post("/data/seed")
async def seed_dummy_data(count: int = 100, base_lat: float = 13.7563, base_lon: float = 100.5018, radius: float = 0.01) -> Dict[str, Any]:
    """Generate and seed dummy user data.
    
    Args:
        count: Number of dummy users to generate (default: 100)
        base_lat: Base latitude for location generation (default: Bangkok)
        base_lon: Base longitude for location generation (default: Bangkok)
        radius: Radius for location variation (default: 0.01 degrees)
    """
    if count < 1 or count > 10000:
        raise HTTPException(status_code=400, detail="Count must be between 1 and 10000")
        
    try:
        # Generate dummy user data
        users_data = generate_user_data(
            num_users=count,
            base_lat=base_lat,
            base_lon=base_lon,
            radius=radius
        )
        
        # Convert to Profile objects
        profiles = []
        for user in users_data:
            profile = Profile(
                id=user["id"],
                age=user["age"],
                gender=user["gender"],
                location=Location(lat=user["location"]["lat"], lon=user["location"]["lon"]),
                interests=user["interests"]
            )
            profiles.append(profile)
        
        # Add profiles to matchmaker
        matchmaker.bulk_add_profiles(profiles)
        
        return {
            "message": f"Successfully generated and added {len(profiles)} dummy profiles",
            "count": len(profiles),
            "base_location": {"lat": base_lat, "lon": base_lon}
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating dummy data: {str(e)}")

