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
        print(f"DEBUG: Precomputing matches for user {user_id} in quadrant {user_gh}")
        
        # Use our _get_adjacent_geohashes method to get all adjacent quadrants
        nearby_quadrants = self._get_adjacent_geohashes(user_gh)
        print(f"DEBUG: Found {len(nearby_quadrants)} adjacent quadrants: {nearby_quadrants}")
        
        # Initialize user's score dictionary
        self.match_store.ensure_quadrant_exists(user_gh, user_id)
        
        # Compute scores with users in nearby quadrants
        for gh in nearby_quadrants:
            for other_id in self.geo_index.get_users_in_quadrant(gh):
                if other_id != user_id:
                    other = self.profiles[other_id]
                    if self.score_calculator.is_within_matching_distance(user, other):
                        # Calculate score without gender preference for precomputation
                        # This allows us to filter by gender preference at query time
                        score = self.score_calculator.compute_match_score(user, other, None)
                        
                        # Only store non-zero scores
                        if score > 0:
                            other_gh = self.geo_index.add_location(other_id, other.location)
                            self.match_store.store_match_score(user_id, other_id, user_gh, other_gh, score)
        
        # Also compute matches for this user with existing users in other quadrants
        # This ensures comprehensive matching data
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
        print(f"DEBUG: Stored precomputed matches for user {user_id} across {len(nearby_quadrants)} quadrants")
        
        # Count matches by quadrant for debugging
        match_count = 0
        quadrant_counts = {}
        for match_id, score in self.match_store.get_precomputed_matches(user_id, set()):
            match_count += 1
            match_gh = self.geo_index.get_geohash(match_id)
            quadrant_counts[match_gh] = quadrant_counts.get(match_gh, 0) + 1
        
        print(f"DEBUG: User {user_id} now has {match_count} precomputed matches")
        print(f"DEBUG: Matches by quadrant: {quadrant_counts}")
        
        for other_id, other in self.profiles.items():
            if other_id != user_id:
                other_gh = self.geo_index.add_location(other_id, other.location)
                other_quadrants = self._get_adjacent_geohashes(other_gh)
                if user_gh in other_quadrants:
                    self.match_store.store_precomputed_matches(other_id, other_quadrants)
                    print(f"DEBUG: Updated precomputed matches for {other_id} to include {user_id}")

    def get_matches(self, user_id: str, limit: int = 8, gender_preference: str = None) -> List[Tuple[str, float]]:
        """Get top matches for a user using precomputed matches for constant time lookup.
        Applies gender preference and exclusion filtering at query time.
        """
        if user_id not in self.profiles:
            print(f"DEBUG: User {user_id} not found in profiles!")
            return []
            
        print(f"\nDEBUG: Getting matches for user {user_id}")
        user_gh = self.geo_index.get_geohash(user_id)
        print(f"DEBUG: User {user_id} is in quadrant {user_gh}")
        
        excluded = self.exclusion_manager.get_excluded_users(user_id)
        excluded.add(user_id)  # Make sure user doesn't match with themselves
        print(f"DEBUG: Excluded users: {excluded}")
        
        scores = self.match_store.get_precomputed_matches(user_id, excluded)
        print(f"DEBUG: Retrieved {len(scores)} precomputed matches")
        if gender_preference:
            filtered_scores = []
            for match_id, score in scores:
                if self.profiles[match_id].gender == gender_preference:
                    filtered_scores.append((match_id, score))
            scores = filtered_scores
        scores = [(match_id, score) for match_id, score in scores if score > 0]
        scores.sort(key=lambda x: x[1], reverse=True)
        if len(scores) < limit:
            print(f"DEBUG: Not enough matches ({len(scores)}), searching adjacent quadrants...")
            user_gh = self.geo_index.get_geohash(user_id)
            quadrants = self._get_adjacent_geohashes(user_gh)
            print(f"DEBUG: Searching in {len(quadrants)} quadrants: {quadrants}")
            
            users_in_quadrants = set()
            for q in quadrants:
                users_in_q = self.geo_index.get_users_in_quadrant(q)
                print(f"DEBUG: Found {len(users_in_q)} users in quadrant {q}: {users_in_q}")
                users_in_quadrants.update(users_in_q)
            
            print(f"DEBUG: Total users in all quadrants: {len(users_in_quadrants)}")
            existing_match_ids = {match_id for match_id, _ in scores}
            potential_matches = [pid for pid in users_in_quadrants 
                                if pid != user_id and pid not in excluded and pid not in existing_match_ids]
            print(f"DEBUG: Potential new matches to evaluate: {potential_matches}")
            for match_id in potential_matches:
                other = self.profiles[match_id]
                if gender_preference and other.gender != gender_preference:
                    continue
                score = self.score_calculator.compute_match_score(self.profiles[user_id], other, gender_preference)
                if score > 0:
                    scores.append((match_id, score))
            scores.sort(key=lambda x: x[1], reverse=True)
        final_matches = scores[:limit]
        print(f"DEBUG: Returning {len(final_matches)} matches: {final_matches}")
        
        # Print quadrant info for each match
        for match_id, score in final_matches:
            match_gh = self.geo_index.get_geohash(match_id)
            print(f"DEBUG: Match {match_id} is in quadrant {match_gh} with score {score}")
            
        return final_matches

    def _get_adjacent_geohashes(self, gh: str) -> List[str]:
        """
        Get all adjacent geohash quadrants (including the original).
        """
        adjacent_quadrants = self.geo_index.get_adjacent_quadrants(gh)
        print(f"DEBUG: For quadrant {gh}, found adjacent quadrants: {adjacent_quadrants}")
        return adjacent_quadrants

    def add_exclusion(self, user_id: str, excluded_id: str, exclusion_type: str) -> None:
        """Add a user to an exclusion list."""
        if user_id in self.profiles and excluded_id in self.profiles:
            self.exclusion_manager.add_exclusion(user_id, excluded_id, exclusion_type)
