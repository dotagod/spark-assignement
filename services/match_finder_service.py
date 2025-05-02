from typing import List, Set, Tuple
from services.profile_service import ProfileService
from services.geo_service import GeoService
from services.matching_service import MatchingService
from services.precompute_service import PrecomputeService
from services.exclusion_service import ExclusionService
from services.interfaces import IMatchFinderService, IProfileService, IGeoService, IMatchingService, IPrecomputeService, IExclusionService

class MatchFinderService(IMatchFinderService):
    """Service for finding and filtering matches for users."""
    
    def __init__(self, profile_service: ProfileService, geo_service: GeoService,
                 matching_service: MatchingService, precompute_service: PrecomputeService,
                 exclusion_service: ExclusionService):
        self.profile_service = profile_service
        self.geo_service = geo_service
        self.matching_service = matching_service
        self.precompute_service = precompute_service
        self.exclusion_service = exclusion_service
        
    def get_matches(self, user_id: str, limit: int = 8, gender_preference: str = None) -> List[Tuple[str, float]]:
        """Get top matches for a user.
        
        Args:
            user_id: ID of the user to find matches for
            limit: Maximum number of matches to return
            gender_preference: Optional gender preference filter
            
        Returns:
            List of (user_id, score) tuples
        """
        excluded = self._get_excluded_users(user_id)
        
        scores = self._get_filtered_precomputed_matches(user_id, excluded, gender_preference)
        
        if len(scores) < limit:
            additional_scores = self._compute_additional_matches(user_id, scores, excluded, gender_preference)
            scores.extend(additional_scores)
            scores.sort(key=lambda x: x[1], reverse=True)
            
        return scores[:limit]
        
    def _get_excluded_users(self, user_id: str) -> Set[str]:
        """Get the set of excluded users for a given user.
        
        Args:
            user_id: ID of the user
            
        Returns:
            Set of excluded user IDs
        """
        excluded = self.exclusion_service.get_excluded_users(user_id)
        excluded.add(user_id)
        return excluded
    
    def _get_filtered_precomputed_matches(self, user_id: str, excluded: Set[str], gender_preference: str = None) -> List[Tuple[str, float]]:
        """Get precomputed matches filtered by exclusions and gender preference.
        
        Args:
            user_id: ID of the user
            excluded: Set of user IDs to exclude
            gender_preference: Optional gender preference filter
            
        Returns:
            List of (user_id, score) tuples
        """
        scores = self.precompute_service.get_precomputed_matches(user_id, excluded)
        
        if gender_preference:
            scores = [
                (match_id, score) for match_id, score in scores 
                if self.profile_service.get_profile(match_id).gender == gender_preference
            ]
        
        scores = [(match_id, score) for match_id, score in scores if score > 0]
        
        scores.sort(key=lambda x: x[1], reverse=True)
        return scores
    
    def _compute_additional_matches(self, user_id: str, existing_scores: List[Tuple[str, float]], 
                                   excluded: Set[str], gender_preference: str = None) -> List[Tuple[str, float]]:
        """Compute additional matches on-the-fly when precomputed matches are insufficient.
        
        Args:
            user_id: ID of the user
            existing_scores: List of already computed (user_id, score) tuples
            excluded: Set of user IDs to exclude
            gender_preference: Optional gender preference filter
            
        Returns:
            List of additional (user_id, score) tuples
        """
        user_gh = self.geo_service.get_profile_geohash(user_id)
        if not user_gh:
            return []
            
        quadrants = self.geo_service.get_adjacent_quadrants(user_gh)
        
        users_in_quadrants = set()
        for q in quadrants:
            users_in_quadrants.update(self.geo_service.get_users_in_quadrant(q))
        
        existing_match_ids = {match_id for match_id, _ in existing_scores}
        potential_matches = [
            pid for pid in users_in_quadrants 
            if pid != user_id and pid not in excluded and pid not in existing_match_ids
        ]
        
        additional_scores = []
        for match_id in potential_matches:
            try:
                other = self.profile_service.get_profile(match_id)
                
                if gender_preference and other.gender != gender_preference:
                    continue
                    
                score = self.matching_service.compute_match_score(user_id, match_id, gender_preference)
                if score > 0:
                    additional_scores.append((match_id, score))
            except ValueError:
                continue
                
        return additional_scores
