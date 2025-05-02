from typing import Dict, List, Tuple, Set

class MatchStore:
    def __init__(self):
        self.quadrant_scores: Dict[str, Dict[str, Dict[str, float]]] = {}
        self.precomputed_matches: Dict[str, List[Tuple[str, float]]] = {}

    def ensure_quadrant_exists(self, quadrant: str, user_id: str) -> None:
        """Ensure quadrant and user score dictionaries exist."""
        if quadrant not in self.quadrant_scores:
            self.quadrant_scores[quadrant] = {}
        if user_id not in self.quadrant_scores[quadrant]:
            self.quadrant_scores[quadrant][user_id] = {}

    def store_match_score(self, user_id: str, other_id: str, user_gh: str, 
                         other_gh: str, score: float) -> None:
        """Store match score for both users in their respective quadrants."""
        self.ensure_quadrant_exists(user_gh, user_id)
        self.quadrant_scores[user_gh][user_id][other_id] = score

        self.ensure_quadrant_exists(other_gh, other_id)
        self.quadrant_scores[other_gh][other_id][user_id] = score

    def get_user_matches(self, user_id: str, quadrant: str, 
                        excluded_users: Set[str]) -> List[Tuple[str, float]]:
        """Get all matches for a user in a quadrant, excluding specified users."""
        if (quadrant not in self.quadrant_scores or 
            user_id not in self.quadrant_scores[quadrant]):
            return []

        scores = []
        for other_id, score in self.quadrant_scores[quadrant][user_id].items():
            if other_id not in excluded_users:
                scores.append((other_id, score))
        return scores
        
    def store_precomputed_matches(self, user_id: str, quadrants: List[str]) -> None:
        """Store precomputed matches for a user from all specified quadrants.
        
        This creates a precomputed list of all potential matches for a user
        across all neighboring quadrants for constant time lookup.
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
    
    def get_precomputed_matches(self, user_id: str, excluded_users: Set[str]) -> List[Tuple[str, float]]:
        """Get precomputed matches for a user, excluding specified users.
        
        This is a constant time operation since matches are precomputed.
        """
        if user_id not in self.precomputed_matches:
            return []
        
        return [(other_id, score) for other_id, score in self.precomputed_matches[user_id]
                if other_id not in excluded_users]
    
    def get_user_matches_from_quadrants(self, user_id: str, quadrants: List[str],
                                      excluded_users: Set[str]) -> List[Tuple[str, float]]:
        """Get all matches for a user from multiple quadrants, excluding specified users.
        
        This allows retrieving matches from neighboring quadrants as well.
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
