import unittest
import sys
import os
from unittest.mock import patch, MagicMock

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from matchmaker import MatchMaker
from models import Profile, Location
from geo_index import GeoIndex
from score_calculator import ScoreCalculator
from exclusion_manager import ExclusionManager
from match_store import MatchStore

class TestMatchMaker(unittest.TestCase):
    def setUp(self):
        self.matchmaker = MatchMaker()
        
        self.profile1 = Profile(
            id="user1",
            age=25,
            gender="male",
            location=Location(lat=37.7749, lon=-122.4194),
            interests=["music", "movies", "hiking"]
        )
        
        self.profile2 = Profile(
            id="user2",
            age=27,
            gender="female",
            location=Location(lat=37.7749, lon=-122.4194),
            interests=["music", "hiking", "reading"]
        )
        
        self.profile3 = Profile(
            id="user3",
            age=30,
            gender="male",
            location=Location(lat=37.8044, lon=-122.2711),
            interests=["music", "photography", "travel"]
        )
        
        self.profile4 = Profile(
            id="user4",
            age=28,
            gender="female",
            location=Location(lat=40.7128, lon=-74.0060),
            interests=["music", "art", "cooking"]
        )
        
    def test_get_adjacent_geohashes(self):
        """Test getting adjacent geohashes."""
        with patch.object(GeoIndex, 'get_adjacent_quadrants') as mock_get_adjacent:
            mock_get_adjacent.return_value = ["abc12", "abc13", "abc14"]
            
            result = self.matchmaker._get_adjacent_geohashes("abc12")
            
            self.assertEqual(result, ["abc12", "abc13", "abc14"])
            mock_get_adjacent.assert_called_once_with("abc12")
            
    def test_add_profile(self):
        """Test adding a profile."""
        with patch.object(GeoIndex, 'add_location') as mock_add_location, \
             patch.object(MatchMaker, '_precompute_matches') as mock_precompute:
            
            mock_add_location.return_value = "abc12"
            
            self.matchmaker.add_profile(self.profile1)
            
            self.assertIn(self.profile1.id, self.matchmaker.profiles)
            self.assertEqual(self.matchmaker.profiles[self.profile1.id], self.profile1)
            
            mock_add_location.assert_called_once_with(self.profile1.id, self.profile1.location)
            mock_precompute.assert_called_once_with(self.profile1.id, "abc12")
            
    def test_add_exclusion(self):
        """Test adding an exclusion."""
        self.matchmaker.profiles[self.profile1.id] = self.profile1
        self.matchmaker.profiles[self.profile2.id] = self.profile2
        
        with patch.object(ExclusionManager, 'add_exclusion') as mock_add_exclusion:
            self.matchmaker.add_exclusion(self.profile1.id, self.profile2.id, "blocked")
            
            mock_add_exclusion.assert_called_once_with(self.profile1.id, self.profile2.id, "blocked")
            
    def test_add_exclusion_nonexistent_users(self):
        """Test adding an exclusion with nonexistent users."""
        with patch.object(ExclusionManager, 'add_exclusion') as mock_add_exclusion:
            self.matchmaker.add_exclusion("nonexistent1", "nonexistent2", "blocked")
            
            mock_add_exclusion.assert_not_called()
            
    def test_get_matches_with_exclusions(self):
        """Test getting matches with exclusions."""
        # Add profiles
        self.matchmaker.profiles = {
            self.profile1.id: self.profile1,
            self.profile2.id: self.profile2,
            self.profile3.id: self.profile3
        }
        
        # Mock methods
        with patch.object(GeoIndex, 'get_geohash') as mock_get_geohash, \
             patch.object(ExclusionManager, 'get_excluded_users') as mock_get_excluded, \
             patch.object(MatchStore, 'get_precomputed_matches') as mock_get_precomputed:
            
            mock_get_geohash.return_value = "abc12"
            mock_get_excluded.return_value = {self.profile3.id}  # Exclude user3
            mock_get_precomputed.return_value = [
                (self.profile2.id, 0.8),
                (self.profile3.id, 0.7)
            ]
            
            matches = self.matchmaker.get_matches(self.profile1.id)
            
            self.assertEqual(len(matches), 2)
            self.assertEqual(matches[0][0], self.profile2.id)
            self.assertEqual(matches[0][1], 0.8)
            self.assertEqual(matches[1][0], self.profile3.id)
            self.assertEqual(matches[1][1], 0.7)
            
            mock_get_excluded.assert_called_once_with(self.profile1.id)
            mock_get_precomputed.assert_called_once()
            
    def test_get_matches_with_gender_preference(self):
        """Test getting matches with gender preference."""
        # Add profiles
        self.matchmaker.profiles = {
            self.profile1.id: self.profile1,
            self.profile2.id: self.profile2,
            self.profile3.id: self.profile3
        }
        
        # Mock methods
        with patch.object(GeoIndex, 'get_geohash') as mock_get_geohash, \
             patch.object(ExclusionManager, 'get_excluded_users') as mock_get_excluded, \
             patch.object(MatchStore, 'get_precomputed_matches') as mock_get_precomputed:
            
            mock_get_geohash.return_value = "abc12"
            mock_get_excluded.return_value = set()
            mock_get_precomputed.return_value = [
                (self.profile2.id, 0.8),
                (self.profile3.id, 0.7)
            ]
            
            matches = self.matchmaker.get_matches(self.profile1.id, gender_preference="female")
            
            self.assertEqual(len(matches), 1)
            self.assertEqual(matches[0][0], self.profile2.id)
            self.assertEqual(matches[0][1], 0.8)
            
    def test_precompute_matches(self):
        """Test precomputing matches."""
        self.matchmaker.profiles = {
            self.profile1.id: self.profile1,
            self.profile2.id: self.profile2,
            self.profile3.id: self.profile3
        }
        
        with patch.object(MatchMaker, '_get_adjacent_geohashes') as mock_get_adjacent, \
             patch.object(GeoIndex, 'get_users_in_quadrant') as mock_get_users, \
             patch.object(ScoreCalculator, 'is_within_matching_distance') as mock_within_distance, \
             patch.object(ScoreCalculator, 'compute_match_score') as mock_compute_score, \
             patch.object(GeoIndex, 'add_location') as mock_add_location, \
             patch.object(MatchStore, 'store_match_score') as mock_store_score, \
             patch.object(MatchStore, 'store_precomputed_matches') as mock_store_precomputed:
            
            mock_get_adjacent.return_value = ["abc12", "abc13"]
            mock_get_users.side_effect = lambda gh: {
                "abc12": {self.profile1.id, self.profile2.id},
                "abc13": {self.profile3.id}
            }.get(gh, set())
            mock_within_distance.return_value = True
            mock_compute_score.return_value = 0.75
            mock_add_location.side_effect = lambda user_id, location: {
                self.profile1.id: "abc12",
                self.profile2.id: "abc12",
                self.profile3.id: "abc13"
            }.get(user_id, "")
            
            self.matchmaker._precompute_matches(self.profile1.id, "abc12")
            
            self.assertGreaterEqual(mock_get_adjacent.call_count, 1)
            self.assertTrue(mock_get_adjacent.called_with("abc12"))
            
            self.assertGreaterEqual(mock_get_users.call_count, 2)
            self.assertGreaterEqual(mock_compute_score.call_count, 2)
            self.assertGreaterEqual(mock_store_score.call_count, 2)
            self.assertGreaterEqual(mock_store_precomputed.call_count, 1)
            mock_store_precomputed.assert_any_call(self.profile1.id, ["abc12", "abc13"])
            
    def test_get_matches_nonexistent_user(self):
        """Test getting matches for nonexistent user."""
        matches = self.matchmaker.get_matches("nonexistent")
        
        self.assertEqual(matches, [])
        
    def test_bulk_add_profiles(self):
        """Test bulk adding profiles."""
        with patch.object(MatchMaker, 'add_profile') as mock_add_profile:
            self.matchmaker.bulk_add_profiles([self.profile1, self.profile2, self.profile3])
            
            self.assertEqual(mock_add_profile.call_count, 3)
            mock_add_profile.assert_any_call(self.profile1)
            mock_add_profile.assert_any_call(self.profile2)
            mock_add_profile.assert_any_call(self.profile3)

if __name__ == '__main__':
    unittest.main()
