from typing import Dict, List
from models import Profile
from services.interfaces import IProfileService

class ProfileService(IProfileService):
    """Service for managing user profiles."""
    
    def __init__(self):
        self._profiles: Dict[str, Profile] = {}
        
    def get_profiles(self) -> Dict[str, Profile]:
        """Get all profiles.
        
        Returns:
            Dictionary of user ID to Profile
        """
        return self._profiles
        
    def add_profile(self, profile: Profile) -> None:
        """Add a new profile.
        
        Args:
            profile: The profile to add
        """
        self._profiles[profile.id] = profile
        
    def update_profile(self, profile_id: str, profile: Profile) -> None:
        """Update an existing profile.
        
        Args:
            profile_id: ID of the profile to update
            profile: The updated profile data
            
        Raises:
            ValueError: If the profile doesn't exist
        """
        if profile_id not in self._profiles:
            raise ValueError(f"Profile with ID {profile_id} not found")
        if profile.id != profile_id:
            profile.id = profile_id
        self._profiles[profile_id] = profile
        
    def get_profile(self, profile_id: str) -> Profile:
        """Get a profile by ID.
        
        Args:
            profile_id: ID of the profile to retrieve
            
        Returns:
            The profile
            
        Raises:
            ValueError: If the profile doesn't exist
        """
        if profile_id not in self._profiles:
            raise ValueError(f"Profile with ID {profile_id} not found")
        return self._profiles[profile_id]
        
    def get_all_profiles(self) -> List[Profile]:
        """Get all profiles.
        
        Returns:
            List of all profiles
        """
        return list(self._profiles.values())
        
    def bulk_add_profiles(self, profiles: List[Profile]) -> None:
        """Bulk add multiple profiles.
        
        Args:
            profiles: List of profiles to add
        """
        for profile in profiles:
            self._profiles[profile.id] = profile
