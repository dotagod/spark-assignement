import unittest
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from match_store import MatchStore

class TestMatchStore(unittest.TestCase):
    def setUp(self):
        self.match_store = MatchStore()
        
    def test_ensure_quadrant_exists(self):
        """Test ensuring quadrant and user dictionaries exist."""
        quadrant = "abc12"
        user_id = "user1"
        
        self.match_store.ensure_quadrant_exists(quadrant, user_id)
        
        self.assertIn(quadrant, self.match_store.quadrant_scores)
        self.assertIn(user_id, self.match_store.quadrant_scores[quadrant])
        self.assertEqual(len(self.match_store.quadrant_scores[quadrant][user_id]), 0)
        
    def test_store_match_score(self):
        """Test storing match scores for both users."""
        user_id = "user1"
        other_id = "user2"
        user_gh = "abc12"
        other_gh = "abc13"
        score = 0.85
        
        self.match_store.store_match_score(user_id, other_id, user_gh, other_gh, score)
        
        self.assertIn(user_gh, self.match_store.quadrant_scores)
        self.assertIn(user_id, self.match_store.quadrant_scores[user_gh])
        self.assertIn(other_id, self.match_store.quadrant_scores[user_gh][user_id])
        self.assertEqual(self.match_store.quadrant_scores[user_gh][user_id][other_id], score)
        
        self.assertIn(other_gh, self.match_store.quadrant_scores)
        self.assertIn(other_id, self.match_store.quadrant_scores[other_gh])
        self.assertIn(user_id, self.match_store.quadrant_scores[other_gh][other_id])
        self.assertEqual(self.match_store.quadrant_scores[other_gh][other_id][user_id], score)
        
    def test_get_user_matches(self):
        """Test getting user matches from a quadrant."""
        user_id = "user1"
        other_id1 = "user2"
        other_id2 = "user3"
        excluded_id = "user4"
        quadrant = "abc12"
        
        self.match_store.ensure_quadrant_exists(quadrant, user_id)
        self.match_store.quadrant_scores[quadrant][user_id][other_id1] = 0.8
        self.match_store.quadrant_scores[quadrant][user_id][other_id2] = 0.7
        self.match_store.quadrant_scores[quadrant][user_id][excluded_id] = 0.9
        
        matches = self.match_store.get_user_matches(user_id, quadrant, {excluded_id})
        
        self.assertEqual(len(matches), 2)
        self.assertIn((other_id1, 0.8), matches)
        self.assertIn((other_id2, 0.7), matches)
        self.assertNotIn((excluded_id, 0.9), matches)
        
    def test_get_user_matches_nonexistent(self):
        """Test getting matches for nonexistent user or quadrant."""
        matches = self.match_store.get_user_matches("user1", "nonexistent", set())
        self.assertEqual(matches, [])
        
        self.match_store.quadrant_scores["abc12"] = {}
        matches = self.match_store.get_user_matches("nonexistent", "abc12", set())
        self.assertEqual(matches, [])
        
    def test_store_precomputed_matches(self):
        """Test storing precomputed matches from multiple quadrants."""
        user_id = "user1"
        other_id1 = "user2"
        other_id2 = "user3"
        quadrant1 = "abc12"
        quadrant2 = "abc13"
        
        self.match_store.ensure_quadrant_exists(quadrant1, user_id)
        self.match_store.ensure_quadrant_exists(quadrant2, user_id)
        self.match_store.quadrant_scores[quadrant1][user_id][other_id1] = 0.8
        self.match_store.quadrant_scores[quadrant2][user_id][other_id2] = 0.7
        
        self.match_store.store_precomputed_matches(user_id, [quadrant1, quadrant2])
        
        self.assertIn(user_id, self.match_store.precomputed_matches)
        precomputed = self.match_store.precomputed_matches[user_id]
        self.assertEqual(len(precomputed), 2)
        self.assertIn((other_id1, 0.8), precomputed)
        self.assertIn((other_id2, 0.7), precomputed)
        
    def test_store_precomputed_matches_duplicate_users(self):
        """Test storing precomputed matches with duplicate users across quadrants."""
        user_id = "user1"
        other_id = "user2"
        quadrant1 = "abc12"
        quadrant2 = "abc13"
        
        self.match_store.ensure_quadrant_exists(quadrant1, user_id)
        self.match_store.ensure_quadrant_exists(quadrant2, user_id)
        self.match_store.quadrant_scores[quadrant1][user_id][other_id] = 0.8
        self.match_store.quadrant_scores[quadrant2][user_id][other_id] = 0.9
        
        self.match_store.store_precomputed_matches(user_id, [quadrant1, quadrant2])
        
        self.assertIn(user_id, self.match_store.precomputed_matches)
        precomputed = self.match_store.precomputed_matches[user_id]
        self.assertEqual(len(precomputed), 1)
        self.assertIn((other_id, 0.9), precomputed)
        self.assertNotIn((other_id, 0.8), precomputed)
        
    def test_get_precomputed_matches(self):
        """Test getting precomputed matches with exclusions."""
        user_id = "user1"
        other_id1 = "user2"
        other_id2 = "user3"
        excluded_id = "user4"
        
        self.match_store.precomputed_matches[user_id] = [
            (other_id1, 0.8),
            (other_id2, 0.7),
            (excluded_id, 0.9)
        ]
        
        matches = self.match_store.get_precomputed_matches(user_id, {excluded_id})
        
        self.assertEqual(len(matches), 2)
        self.assertIn((other_id1, 0.8), matches)
        self.assertIn((other_id2, 0.7), matches)
        self.assertNotIn((excluded_id, 0.9), matches)
        
    def test_get_precomputed_matches_nonexistent(self):
        """Test getting precomputed matches for nonexistent user."""
        matches = self.match_store.get_precomputed_matches("nonexistent", set())
        self.assertEqual(matches, [])
        
    def test_get_user_matches_from_quadrants(self):
        """Test getting user matches from multiple quadrants."""
        user_id = "user1"
        other_id1 = "user2"
        other_id2 = "user3"
        excluded_id = "user4"
        quadrant1 = "abc12"
        quadrant2 = "abc13"
        
        self.match_store.ensure_quadrant_exists(quadrant1, user_id)
        self.match_store.ensure_quadrant_exists(quadrant2, user_id)
        self.match_store.quadrant_scores[quadrant1][user_id][other_id1] = 0.8
        self.match_store.quadrant_scores[quadrant2][user_id][other_id2] = 0.7
        self.match_store.quadrant_scores[quadrant1][user_id][excluded_id] = 0.9
        
        matches = self.match_store.get_user_matches_from_quadrants(
            user_id, [quadrant1, quadrant2], {excluded_id}
        )
        
        self.assertEqual(len(matches), 2)
        self.assertIn((other_id1, 0.8), matches)
        self.assertIn((other_id2, 0.7), matches)
        self.assertNotIn((excluded_id, 0.9), matches)
        
    def test_get_user_matches_from_quadrants_duplicate_users(self):
        """Test getting user matches from multiple quadrants with duplicate users."""
        user_id = "user1"
        other_id = "user2"
        quadrant1 = "abc12"
        quadrant2 = "abc13"
        
        self.match_store.ensure_quadrant_exists(quadrant1, user_id)
        self.match_store.ensure_quadrant_exists(quadrant2, user_id)
        self.match_store.quadrant_scores[quadrant1][user_id][other_id] = 0.8
        self.match_store.quadrant_scores[quadrant2][user_id][other_id] = 0.9
        
        matches = self.match_store.get_user_matches_from_quadrants(
            user_id, [quadrant1, quadrant2], set()
        )
        
        self.assertEqual(len(matches), 1)
        self.assertIn((other_id, 0.9), matches)
        self.assertNotIn((other_id, 0.8), matches)

if __name__ == '__main__':
    unittest.main()
