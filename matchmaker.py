from typing import Dict, List, Set, Tuple
from models import Profile
from geo_index import GeoIndex
from score_calculator import ScoreCalculator
from exclusion_manager import ExclusionManager
from match_store import MatchStore
import geohash

class MatchMaker:
    def __init__(self):
        self.profiles: Dict[str, Profile] = {}
        self.geo_index = GeoIndex()
        self.score_calculator = ScoreCalculator()
        self.exclusion_manager = ExclusionManager()
        self.match_store = MatchStore()

    def add_profile(self, profile: Profile) -> None:
        """Add a new profile and precompute match scores."""
        self.profiles[profile.id] = profile
        profile_gh = self.geo_index.add_location(profile.id, profile.location)
        self.exclusion_manager.initialize_user(profile.id)
        self._precompute_matches(profile.id, profile_gh)

    def bulk_add_profiles(self, profiles: List[Profile]) -> None:
        """Bulk add profiles and precompute match scores."""
        for profile in profiles:
            self.add_profile(profile)

    def _precompute_matches(self, user_id: str, user_gh: str) -> None:
        """Precompute match scores for a user with others in nearby quadrants.
        
        This method computes and stores match scores with all potential matches
        in nearby quadrants, enabling constant time lookup during matching.
        """
        user = self.profiles[user_id]
        nearby_quadrants = self._get_adjacent_geohashes(user_gh)
        self.match_store.ensure_quadrant_exists(user_gh, user_id)
        
        # Compute scores with users in nearby quadrants
        for gh in nearby_quadrants:
            for other_id in self.geo_index.get_users_in_quadrant(gh):
                if other_id != user_id:
                    other = self.profiles[other_id]
                    if self.score_calculator.is_within_matching_distance(user, other):
                        score = self.score_calculator.compute_match_score(user, other, None)
                        if score > 0:
                            other_gh = self.geo_index.add_location(other_id, other.location)
                            self.match_store.store_match_score(user_id, other_id, user_gh, other_gh, score)
        
        # Compute matches with users in other quadrants
        for other_id, other in self.profiles.items():
            if other_id != user_id:
                other_gh = self.geo_index.add_location(other_id, other.location)
                if other_gh in nearby_quadrants:
                    continue
                if self.score_calculator.is_within_matching_distance(user, other):
                    score = self.score_calculator.compute_match_score(user, other, None)
                    if score > 0:
                        self.match_store.store_match_score(user_id, other_id, user_gh, other_gh, score)
        self.match_store.store_precomputed_matches(user_id, nearby_quadrants)
        
        for other_id, other in self.profiles.items():
            if other_id != user_id:
                other_gh = self.geo_index.add_location(other_id, other.location)
                other_nearby_quadrants = self._get_adjacent_geohashes(other_gh)
                self.match_store.store_precomputed_matches(other_id, other_nearby_quadrants)

    def get_matches(self, user_id: str, limit: int = 8, gender_preference: str = None) -> List[Tuple[str, float]]:
        """Get top matches for a user using precomputed matches for constant time lookup.
        Applies gender preference and exclusion filtering at query time.
        """
        if user_id not in self.profiles:
            return []
            
        user_gh = self.geo_index.get_geohash(user_id)
        
        excluded = self.exclusion_manager.get_excluded_users(user_id)
        excluded.add(user_id)
        
        scores = self.match_store.get_precomputed_matches(user_id, excluded)
        if gender_preference:
            filtered_scores = []
            for match_id, score in scores:
                if self.profiles[match_id].gender == gender_preference:
                    filtered_scores.append((match_id, score))
            scores = filtered_scores
        scores = [(match_id, score) for match_id, score in scores if score > 0]
        scores.sort(key=lambda x: x[1], reverse=True)
        if len(scores) < limit:
            user_gh = self.geo_index.get_geohash(user_id)
            quadrants = self._get_adjacent_geohashes(user_gh)
            
            users_in_quadrants = set()
            for q in quadrants:
                users_in_quadrants.update(self.geo_index.get_users_in_quadrant(q))
            
            existing_match_ids = {match_id for match_id, _ in scores}
            potential_matches = [pid for pid in users_in_quadrants 
                                if pid != user_id and pid not in excluded and pid not in existing_match_ids]
            for match_id in potential_matches:
                other = self.profiles[match_id]
                if gender_preference and other.gender != gender_preference:
                    continue
                score = self.score_calculator.compute_match_score(self.profiles[user_id], other, gender_preference)
                if score > 0:
                    scores.append((match_id, score))
            scores.sort(key=lambda x: x[1], reverse=True)
        final_matches = scores[:limit]
        return final_matches

    def _get_adjacent_geohashes(self, gh: str) -> List[str]:
        """
        Get all adjacent geohash quadrants (including the original).
        """
        return self.geo_index.get_adjacent_quadrants(gh)

    def add_exclusion(self, user_id: str, excluded_id: str, exclusion_type: str) -> None:
        """Add a user to an exclusion list."""
        if user_id in self.profiles and excluded_id in self.profiles:
            self.exclusion_manager.add_exclusion(user_id, excluded_id, exclusion_type)
