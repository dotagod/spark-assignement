from typing import List
from models import Profile, Location
from services.profile_service import ProfileService
from services.geo_service import GeoService
from services.interfaces import IMatchingService, IProfileService, IGeoService

class MatchingService(IMatchingService):
    """Service for calculating match scores between users."""
    
    def __init__(self, profile_service: ProfileService, geo_service: GeoService, max_distance_km: float = 10):
        self.profile_service = profile_service
        self.geo_service = geo_service
        self.max_distance_km = max_distance_km
        
    def get_score_calculator(self):
        """Get the score calculator.
        
        Returns:
            The ScoreCalculator instance - this is now the service itself for backward compatibility
        """
        return self
        
    def _compute_age_score(self, age1: int, age2: int) -> float:
        """Compute age similarity score (30%).
        
        Args:
            age1: First user's age
            age2: Second user's age
            
        Returns:
            Age similarity score component
        """
        age_diff = abs(age1 - age2)
        return max(0, 1 - (age_diff / 20)) * 0.3

    def _compute_interest_score(self, interests1: List[str], interests2: List[str]) -> float:
        """Compute shared interests score (30%).
        
        Args:
            interests1: First user's interests
            interests2: Second user's interests
            
        Returns:
            Interest similarity score component
        """
        shared = len(set(interests1) & set(interests2))
        total = len(set(interests1) | set(interests2))
        return (shared / total if total > 0 else 0) * 0.3

    def _compute_location_score(self, loc1: Location, loc2: Location) -> float:
        """Compute location proximity score (40%).
        
        Args:
            loc1: First user's location
            loc2: Second user's location
            
        Returns:
            Location proximity score component
        """
        distance = self.geo_service.calculate_distance(loc1, loc2)
        return max(0, 1 - (distance / self.max_distance_km)) * 0.4
        
    def compute_match_score(self, user_id: str, other_id: str, gender_preference: str = None) -> float:
        """Compute the match score between two users.
        
        Args:
            user_id: ID of the first user
            other_id: ID of the second user
            gender_preference: Optional gender preference filter
            
        Returns:
            The computed match score
        """
        user = self.profile_service.get_profile(user_id)
        other = self.profile_service.get_profile(other_id)
        
        # Check gender preference if specified
        if gender_preference and other.gender != gender_preference:
            return 0.0  # Not matching gender preference
        
        # Age similarity (30%)
        age_score = self._compute_age_score(user.age, other.age)
        
        # Shared interests (30%)
        interest_score = self._compute_interest_score(user.interests, other.interests)
        
        # Location proximity (40%)
        location_score = self._compute_location_score(user.location, other.location)
        
        return age_score + interest_score + location_score
        
    def is_within_matching_distance(self, user_id: str, other_id: str) -> bool:
        """Check if two users are within matching distance.
        
        Args:
            user_id: ID of the first user
            other_id: ID of the second user
            
        Returns:
            True if users are within matching distance, False otherwise
        """
        user = self.profile_service.get_profile(user_id)
        other = self.profile_service.get_profile(other_id)
        distance = self.geo_service.calculate_distance(user.location, other.location)
        return distance <= self.max_distance_km
