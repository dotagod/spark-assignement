from fastapi import FastAPI, HTTPException, Depends
from models import Profile, Location
from typing import List, Dict, Any
import sys
sys.path.append('.')
from generate_dummy_data import generate_user_data
from services.service_locator import ServiceLocator
from services.interfaces import (
    IProfileService,
    IGeoService,
    IExclusionService,
    IMatchingService,
    IPrecomputeService,
    IMatchFinderService
)
from services.config import configure_services

app = FastAPI(title="Matchmaking Engine")

# Configure services on startup
@app.on_event("startup")
async def startup_event():
    configure_services()

@app.post("/profiles")
async def create_profile(profile: Profile) -> Dict[str, str]:
    """Create a new user profile."""
    try:
        profile_service = ServiceLocator.get(IProfileService)
        geo_service = ServiceLocator.get(IGeoService)
        exclusion_service = ServiceLocator.get(IExclusionService)
        precompute_service = ServiceLocator.get(IPrecomputeService)
        
        # Add the profile
        profile_service.add_profile(profile)
        
        # Index the profile location
        geo_hash = geo_service.index_profile(profile.id, profile.location)
        
        # Initialize exclusions
        exclusion_service.initialize_user(profile.id)
        
        # Precompute matches
        precompute_service.precompute_matches(profile.id)
        
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
        profile_service = ServiceLocator.get(IProfileService)
        geo_service = ServiceLocator.get(IGeoService)
        precompute_service = ServiceLocator.get(IPrecomputeService)
        
        profiles = profile_service.get_profiles()
        if user_id not in profiles:
            raise ValueError(f"Profile with ID {user_id} not found")
            
        # Ensure ID consistency
        if profile.id != user_id:
            profile.id = user_id
            
        # Remove from old geohash quadrant if exists
        old_gh = geo_service.get_profile_geohash(user_id)
        if old_gh:
            geo_service.remove_from_index(old_gh, user_id)
            
        # Update the profile
        profile_service.update_profile(user_id, profile)
        
        # Add to new quadrant
        geo_service.index_profile(user_id, profile.location)
        
        # Recompute matches
        precompute_service.precompute_matches(user_id)
        
        return {"message": f"Profile updated successfully for user {user_id}"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/profiles/bulk")
async def bulk_create_profiles(profiles: List[Profile]) -> Dict[str, str]:
    """Bulk create user profiles."""
    try:
        profile_service = ServiceLocator.get(IProfileService)
        geo_service = ServiceLocator.get(IGeoService)
        exclusion_service = ServiceLocator.get(IExclusionService)
        precompute_service = ServiceLocator.get(IPrecomputeService)
        
        # Add profiles
        profile_service.bulk_add_profiles(profiles)
        
        # Process each profile
        for profile in profiles:
            # Index location
            geo_service.index_profile(profile.id, profile.location)
            
            # Initialize exclusions
            exclusion_service.initialize_user(profile.id)
            
            # Precompute matches
            precompute_service.precompute_matches(profile.id)
        
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
    profile_service = ServiceLocator.get(IProfileService)
    match_finder_service = ServiceLocator.get(IMatchFinderService)
    
    profiles = profile_service.get_profiles()
    if user_id not in profiles:
        raise HTTPException(status_code=404, detail="User not found")
    
    if page < 1:
        raise HTTPException(status_code=400, detail="Page must be greater than 0")
    
    if page_size < 1 or page_size > 50:
        raise HTTPException(status_code=400, detail="Page size must be between 1 and 50")
    
    limit = page_size
    offset = (page - 1) * page_size
    
    all_matches = match_finder_service.get_matches(user_id, limit=100, gender_preference=gender_preference)
    total_matches = len(all_matches)
    total_pages = (total_matches + page_size - 1) // page_size
    
    paginated_matches = all_matches[offset:offset + limit] if offset < total_matches else []
    
    profiles = profile_service.get_profiles()
    results = [
        {
            "id": match_id,
            "score": score,
            "profile": profiles[match_id].dict()
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
    profile_service = ServiceLocator.get(IProfileService)
    exclusion_service = ServiceLocator.get(IExclusionService)
    
    profiles = profile_service.get_profiles()
    if user_id not in profiles:
        raise HTTPException(status_code=404, detail="User not found")
        
    excluded_id = excluded_user.get("excluded_id")
    exclusion_type = excluded_user.get("type")
    
    if not excluded_id:
        raise HTTPException(status_code=400, detail="excluded_id is required")
    if not exclusion_type:
        raise HTTPException(status_code=400, detail="type is required")
    
    if excluded_id not in profiles:
        raise HTTPException(status_code=404, detail="Excluded user not found")
    if exclusion_type not in ["blocked", "matched", "disliked"]:
        raise HTTPException(status_code=400, detail="Invalid exclusion type")
    
    exclusion_service.add_exclusion(user_id, excluded_id, exclusion_type)
    return {"message": f"User {excluded_id} added to {exclusion_type} list for user {user_id}"}

@app.get("/profiles")
async def get_all_profiles() -> List[Dict[str, Any]]:
    """Get all user profiles in the system."""
    profile_service = ServiceLocator.get(IProfileService)
    profiles = profile_service.get_profiles()
    return [profile.dict() for profile in profiles.values()]

@app.get("/quadrants/{quadrant}/profiles")
async def get_profiles_by_quadrant(quadrant: str) -> List[Dict[str, Any]]:
    """Get profiles in a specific geohash quadrant.
    
    Args:
        quadrant: Geohash quadrant string
    """
    profile_service = ServiceLocator.get(IProfileService)
    geo_service = ServiceLocator.get(IGeoService)
    
    user_ids = geo_service.get_users_in_quadrant(quadrant)
    profiles = profile_service.get_profiles()
    return [profiles[user_id].dict() for user_id in user_ids if user_id in profiles]

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
        # Get services
        profile_service = ServiceLocator.get(IProfileService)
        geo_service = ServiceLocator.get(IGeoService)
        exclusion_service = ServiceLocator.get(IExclusionService)
        precompute_service = ServiceLocator.get(IPrecomputeService)
        
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
        
        # Add profiles
        profile_service.bulk_add_profiles(profiles)
        
        # Process each profile
        for profile in profiles:
            # Index location
            geo_service.index_profile(profile.id, profile.location)
            
            # Initialize exclusions
            exclusion_service.initialize_user(profile.id)
            
            # Precompute matches
            precompute_service.precompute_matches(profile.id)
        
        return {
            "message": f"Successfully generated and added {len(profiles)} dummy profiles",
            "count": len(profiles),
            "base_location": {"lat": base_lat, "lon": base_lon}
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating dummy data: {str(e)}")

