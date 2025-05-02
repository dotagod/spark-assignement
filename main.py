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
async def get_matches(user_id: str, gender_preference: str = None) -> List[Dict[str, Any]]:
    """Get top 8 matches for a user across all nearby quadrants.
    
    Args:
        user_id: ID of the user to find matches for
        gender_preference: Optional gender preference ('male', 'female', or None for any)
    """
    print(matchmaker.profiles)
    if user_id not in matchmaker.profiles:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Validate gender_preference if provided
    if gender_preference and gender_preference not in ["male", "female"]:
        raise HTTPException(status_code=400, detail="Invalid gender preference. Must be 'male', 'female', or not specified.")
    
    matches = matchmaker.get_matches(user_id, gender_preference=gender_preference)
    return [
        {
            "id": match_id,
            "score": score,
            "profile": matchmaker.profiles[match_id].dict()
        }
        for match_id, score in matches
    ]

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

@app.post("/refresh_matches")
async def refresh_matches() -> Dict[str, Any]:
    """Refresh precomputed matches for all profiles.
    
    This is useful after updating the adjacency calculation logic.
    """
    count = 0
    for user_id, profile in matchmaker.profiles.items():
        # Get the user's quadrant
        user_gh = matchmaker.geo_index.add_location(user_id, profile.location)
        # Recompute matches
        matchmaker._precompute_matches(user_id, user_gh)
        count += 1
    
    return {"message": f"Refreshed matches for {count} profiles"}