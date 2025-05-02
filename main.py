from fastapi import FastAPI, HTTPException
from matchmaker import MatchMaker
from models import Profile, Location
from typing import List, Dict, Any

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

@app.post("/profiles/bulk")
async def bulk_create_profiles(profiles: List[Profile]) -> Dict[str, str]:
    """Bulk create user profiles."""
    try:
        matchmaker.bulk_add_profiles(profiles)
        return {"message": f"Profiles created successfully for users {', '.join([p.id for p in profiles])}"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/match/{user_id}")
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

@app.post("/exclusion/{user_id}/{excluded_id}/{exclusion_type}")
async def add_exclusion(
    user_id: str,
    excluded_id: str,
    exclusion_type: str
) -> Dict[str, str]:
    """Add a user to an exclusion list (blocked/matched/disliked)."""
    if user_id not in matchmaker.profiles:
        raise HTTPException(status_code=404, detail="User not found")
    if excluded_id not in matchmaker.profiles:
        raise HTTPException(status_code=404, detail="Excluded user not found")
    if exclusion_type not in ["blocked", "matched", "disliked"]:
        raise HTTPException(status_code=400, detail="Invalid exclusion type")
    
    matchmaker.add_exclusion(user_id, excluded_id, exclusion_type)
    return {"message": f"User {excluded_id} added to {exclusion_type} list for user {user_id}"}

@app.get("/get_all_profiles")
async def get_all_profiles() -> List[Dict[str, Any]]:
    """Get all profiles."""
    return [profile.dict() for profile in matchmaker.profiles.values()]

@app.get("/get_profiles_by_quadrant/{quadrant}")
async def get_profiles_by_quadrant(quadrant: str) -> List[Dict[str, Any]]:
    """Get profiles in a specific quadrant."""
    user_ids = matchmaker.geo_index.get_users_in_quadrant(quadrant)
    return [matchmaker.profiles[user_id].dict() for user_id in user_ids]

