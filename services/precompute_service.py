from typing import Dict, List, Set, Tuple
from services.profile_service import ProfileService
from services.geo_service import GeoService
from services.matching_service import MatchingService
from services.interfaces import IPrecomputeService, IProfileService, IGeoService, IMatchingService

class PrecomputeService(IPrecomputeService):
    """Service for precomputing and storing match scores."""
    
    def __init__(self, profile_service: ProfileService, geo_service: GeoService, 
                 matching_service: MatchingService):
        self.profile_service = profile_service
        self.geo_service = geo_service
        self.matching_service = matching_service
        self.quadrant_scores: Dict[str, Dict[str, Dict[str, float]]] = {}
        self.precomputed_matches: Dict[str, List[Tuple[str, float]]] = {}
        
    def get_match_store(self):
        """Get the match store.
        
        Returns:
            The MatchStore instance - this is now the service itself for backward compatibility
        """
        return self
        
    def ensure_quadrant_exists(self, quadrant: str, user_id: str) -> None:
        """Ensure quadrant and user score dictionaries exist.
        
        Args:
            quadrant: The geohash quadrant
            user_id: The user ID
        """
        if quadrant not in self.quadrant_scores:
            self.quadrant_scores[quadrant] = {}
        if user_id not in self.quadrant_scores[quadrant]:
            self.quadrant_scores[quadrant][user_id] = {}
            
    def store_match_score(self, user_id: str, other_id: str, user_gh: str, 
                         other_gh: str, score: float) -> None:
        """Store match score for both users in their respective quadrants.
        
        Args:
            user_id: First user ID
            other_id: Second user ID
            user_gh: First user's geohash
            other_gh: Second user's geohash
            score: Match score
        """
        self.ensure_quadrant_exists(user_gh, user_id)
        self.quadrant_scores[user_gh][user_id][other_id] = score

        self.ensure_quadrant_exists(other_gh, other_id)
        self.quadrant_scores[other_gh][other_id][user_id] = score
        
    def get_user_matches(self, user_id: str, quadrant: str, 
                        excluded_users: Set[str]) -> List[Tuple[str, float]]:
        """Get all matches for a user in a quadrant, excluding specified users.
        
        Args:
            user_id: The user ID
            quadrant: The geohash quadrant
            excluded_users: Set of user IDs to exclude
            
        Returns:
            List of (user_id, score) tuples
        """
        if (quadrant not in self.quadrant_scores or 
            user_id not in self.quadrant_scores[quadrant]):
            return []

        scores = []
        for other_id, score in self.quadrant_scores[quadrant][user_id].items():
            if other_id not in excluded_users:
                scores.append((other_id, score))
        return scores
        
    def get_user_matches_from_quadrants(self, user_id: str, quadrants: List[str],
                                      excluded_users: Set[str]) -> List[Tuple[str, float]]:
        """Get all matches for a user from multiple quadrants, excluding specified users.
        
        Args:
            user_id: The user ID
            quadrants: List of geohash quadrants
            excluded_users: Set of user IDs to exclude
            
        Returns:
            List of (user_id, score) tuples
        """
        all_scores = []
        
        for quadrant in quadrants:
            if (quadrant in self.quadrant_scores and 
                user_id in self.quadrant_scores[quadrant]):
                for other_id, score in self.quadrant_scores[quadrant][user_id].items():
                    if other_id not in excluded_users:
                        all_scores.append((other_id, score))
        
        unique_scores = {}
        for other_id, score in all_scores:
            if other_id not in unique_scores or score > unique_scores[other_id]:
                unique_scores[other_id] = score
                
        return [(other_id, score) for other_id, score in unique_scores.items()]
        
    def precompute_matches(self, user_id: str) -> None:
        """Precompute match scores for a user with others in nearby quadrants.
        
        Args:
            user_id: ID of the user to precompute matches for
        """
        user_gh = self.geo_service.get_profile_geohash(user_id)
        if not user_gh:
            return
            
        nearby_quadrants = self.geo_service.get_adjacent_quadrants(user_gh)
        self.ensure_quadrant_exists(user_gh, user_id)
        
        # Process matches in two phases
        self._compute_scores_in_nearby_quadrants(user_id, user_gh, nearby_quadrants)
        self._compute_scores_in_other_quadrants(user_id, user_gh, nearby_quadrants)
        
        # Store the precomputed matches
        self.store_precomputed_matches(user_id, nearby_quadrants)
        
        # Update precomputed matches for other users
        self._update_other_users_precomputed_matches(user_id)
        
    def _compute_scores_in_nearby_quadrants(self, user_id: str, user_gh: str, nearby_quadrants: List[str]) -> None:
        """Compute match scores with users in nearby geohash quadrants.
        
        Args:
            user_id: ID of the user
            user_gh: Geohash of the user
            nearby_quadrants: List of nearby geohash quadrants
        """
        for gh in nearby_quadrants:
            for other_id in self.geo_service.get_users_in_quadrant(gh):
                if other_id == user_id:
                    continue
                    
                if not self.matching_service.is_within_matching_distance(user_id, other_id):
                    continue
                    
                score = self.matching_service.compute_match_score(user_id, other_id)
                if score > 0:
                    other_gh = self.geo_service.get_profile_geohash(other_id)
                    self.store_match_score(user_id, other_id, user_gh, other_gh, score)
    
    def _compute_scores_in_other_quadrants(self, user_id: str, user_gh: str, nearby_quadrants: List[str]) -> None:
        """Compute match scores with users in non-adjacent quadrants.
        
        Args:
            user_id: ID of the user
            user_gh: Geohash of the user
            nearby_quadrants: List of nearby geohash quadrants
        """
        profiles = self.profile_service.get_profiles()
        for other_id in profiles:
            if other_id == user_id:
                continue
                
            other_gh = self.geo_service.get_profile_geohash(other_id)
            if other_gh in nearby_quadrants:
                continue
                
            if not self.matching_service.is_within_matching_distance(user_id, other_id):
                continue
                
            score = self.matching_service.compute_match_score(user_id, other_id)
            if score > 0:
                self.store_match_score(user_id, other_id, user_gh, other_gh, score)
    
    def _update_other_users_precomputed_matches(self, user_id: str) -> None:
        """Update precomputed matches for other users after adding/updating a user.
        
        Args:
            user_id: ID of the user that was added/updated
        """
        profiles = self.profile_service.get_profiles()
        for other_id in profiles:
            if other_id == user_id:
                continue
                
            other_gh = self.geo_service.get_profile_geohash(other_id)
            if not other_gh:
                continue
                
            other_nearby_quadrants = self.geo_service.get_adjacent_quadrants(other_gh)
            self.store_precomputed_matches(other_id, other_nearby_quadrants)
            
    def store_precomputed_matches(self, user_id: str, quadrants: List[str]) -> None:
        """Store precomputed matches for a user from all specified quadrants.
        
        Args:
            user_id: ID of the user
            quadrants: List of geohash quadrants
        """
        all_scores = []
        
        for quadrant in quadrants:
            if (quadrant in self.quadrant_scores and 
                user_id in self.quadrant_scores[quadrant]):
                for other_id, score in self.quadrant_scores[quadrant][user_id].items():
                    all_scores.append((other_id, score))
        
        unique_scores = {}
        for other_id, score in all_scores:
            if other_id not in unique_scores or score > unique_scores[other_id]:
                unique_scores[other_id] = score
        
        self.precomputed_matches[user_id] = [(other_id, score) 
                                           for other_id, score in unique_scores.items()]
    
    def get_precomputed_matches(self, user_id: str, excluded_ids: Set[str]) -> List[Tuple[str, float]]:
        """Get precomputed matches for a user, excluding specified user IDs.
        
        Args:
            user_id: ID of the user
            excluded_ids: Set of user IDs to exclude
            
        Returns:
            List of (user_id, score) tuples
        """
        if user_id not in self.precomputed_matches:
            return []
        
        return [(other_id, score) for other_id, score in self.precomputed_matches[user_id]
                if other_id not in excluded_ids]
