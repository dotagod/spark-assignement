from models import Profile, Location
from geo_index import GeoIndex
from typing import List

class ScoreCalculator:
    def __init__(self, max_distance_km: float = 10):
        self.max_distance_km = max_distance_km
        self.geo_index = GeoIndex()

    def compute_match_score(self, user1: Profile, user2: Profile, gender_preference: str = None) -> float:
        """Compute match score between two users.
        
        Args:
            user1: First user profile
            user2: Second user profile
            gender_preference: Optional gender preference ('male', 'female', or None for any)
        """
        # Check gender preference if specified
        if gender_preference and user2.gender != gender_preference:
            return 0.0  # Not matching gender preference
        
        # Age similarity (30%)
        age_diff = abs(user1.age - user2.age)
        age_score = max(0, 1 - (age_diff / 20)) * 0.3
        
        # Shared interests (30%)
        shared_interests = len(set(user1.interests) & set(user2.interests))
        total_interests = len(set(user1.interests) | set(user2.interests))
        interest_score = (shared_interests / total_interests if total_interests > 0 else 0) * 0.3
        
        # Location proximity (40%)
        location_score = self._compute_location_score(user1.location, user2.location)
        
        return age_score + interest_score + location_score

    def _compute_age_score(self, age1: int, age2: int) -> float:
        """Compute age similarity score (30%)."""
        age_diff = abs(age1 - age2)
        return max(0, 1 - (age_diff / 20)) * 0.3

    def _compute_interest_score(self, interests1: List[str], interests2: List[str]) -> float:
        """Compute shared interests score (30%)."""
        shared = len(set(interests1) & set(interests2))
        total = len(set(interests1) | set(interests2))
        return (shared / total if total > 0 else 0) * 0.3

    def _compute_location_score(self, loc1: Location, loc2: Location) -> float:
        """Compute location proximity score (40%)."""
        distance = self.geo_index.calculate_distance(loc1, loc2)
        return max(0, 1 - (distance / self.max_distance_km)) * 0.4

    def is_within_matching_distance(self, user1: Profile, user2: Profile) -> bool:
        """Check if two users are within matching distance."""
        distance = self.geo_index.calculate_distance(user1.location, user2.location)
        return distance <= self.max_distance_km
