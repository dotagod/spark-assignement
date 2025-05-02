import unittest
import sys
import os
from unittest.mock import patch, MagicMock

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import Profile, Location
from services.precompute_service import PrecomputeService
from services.profile_service import ProfileService
from services.geo_service import GeoService
from services.matching_service import MatchingService

class TestPrecomputeService(unittest.TestCase):
    def setUp(self):
        # Create mock services
        self.profile_service = MagicMock(spec=ProfileService)
        self.geo_service = MagicMock(spec=GeoService)
        self.matching_service = MagicMock(spec=MatchingService)
        
        # Create the precompute service
        self.precompute_service = PrecomputeService(
            self.profile_service, 
            self.geo_service, 
            self.matching_service
        )
        
        # Set up test profiles
        self.profile1 = Profile(
            id="user1",
            age=30,
            gender="male",
            location=Location(lat=13.7563, lon=100.5018),
            interests=["hiking", "reading", "cooking"]
        )
        
        self.profile2 = Profile(
            id="user2",
            age=28,
            gender="female",
            location=Location(lat=13.7560, lon=100.5020),
            interests=["hiking", "photography", "travel"]
        )
        
        # Set up profile service mock
        self.profile_service.get_profiles.return_value = {
            "user1": self.profile1,
            "user2": self.profile2
        }
        
        # Set up geo service mock
        self.geo_service.get_profile_geohash.side_effect = lambda id: {
            "user1": "w4rqc",
            "user2": "w4rqc"  # Same quadrant for simplicity
        }.get(id)
        
        self.geo_service.get_adjacent_quadrants.return_value = ["w4rqc", "w4rqf", "w4rq9"]
        self.geo_service.get_users_in_quadrant.side_effect = lambda q: {
            "w4rqc": {"user1", "user2"},
            "w4rqf": set(),
            "w4rq9": set()
        }.get(q, set())
        
        # Set up matching service mock
        self.matching_service.is_within_matching_distance.return_value = True
        self.matching_service.compute_match_score.return_value = 0.85
        
    def test_ensure_quadrant_exists(self):
        # Test ensuring quadrant exists
        self.precompute_service.ensure_quadrant_exists("w4rqc", "user1")
        
        # Verify quadrant and user are initialized
        self.assertIn("w4rqc", self.precompute_service.quadrant_scores)
        self.assertIn("user1", self.precompute_service.quadrant_scores["w4rqc"])
        
        # Call again to test idempotence
        self.precompute_service.ensure_quadrant_exists("w4rqc", "user1")
        self.assertIn("user1", self.precompute_service.quadrant_scores["w4rqc"])
        
    def test_store_match_score(self):
        # Test storing match scores
        self.precompute_service.store_match_score(
            "user1", "user2", "w4rqc", "w4rqc", 0.85
        )
        
        # Verify scores are stored for both users
        self.assertEqual(
            0.85, 
            self.precompute_service.quadrant_scores["w4rqc"]["user1"]["user2"]
        )
        self.assertEqual(
            0.85, 
            self.precompute_service.quadrant_scores["w4rqc"]["user2"]["user1"]
        )
        
    def test_get_user_matches(self):
        # Set up test data
        self.precompute_service.ensure_quadrant_exists("w4rqc", "user1")
        self.precompute_service.quadrant_scores["w4rqc"]["user1"]["user2"] = 0.85
        self.precompute_service.quadrant_scores["w4rqc"]["user1"]["user3"] = 0.75
        
        # Test getting matches without exclusions
        matches = self.precompute_service.get_user_matches("user1", "w4rqc", set())
        self.assertEqual(2, len(matches))
        
        # Test getting matches with exclusions
        matches = self.precompute_service.get_user_matches("user1", "w4rqc", {"user2"})
        self.assertEqual(1, len(matches))
        self.assertEqual("user3", matches[0][0])
        
    def test_store_precomputed_matches(self):
        # Set up test data
        self.precompute_service.ensure_quadrant_exists("w4rqc", "user1")
        self.precompute_service.quadrant_scores["w4rqc"]["user1"]["user2"] = 0.85
        self.precompute_service.quadrant_scores["w4rqc"]["user1"]["user3"] = 0.75
        
        # Store precomputed matches
        self.precompute_service.store_precomputed_matches("user1", ["w4rqc"])
        
        # Verify matches are stored
        self.assertIn("user1", self.precompute_service.precomputed_matches)
        self.assertEqual(2, len(self.precompute_service.precomputed_matches["user1"]))
        
        # Verify matches are sorted by score
        matches = self.precompute_service.precomputed_matches["user1"]
        self.assertEqual("user2", matches[0][0])
        self.assertEqual(0.85, matches[0][1])
        
    def test_get_precomputed_matches(self):
        # Set up test data
        self.precompute_service.precomputed_matches["user1"] = [
            ("user2", 0.85),
            ("user3", 0.75),
            ("user4", 0.65)
        ]
        
        # Test getting matches without exclusions
        matches = self.precompute_service.get_precomputed_matches("user1", set())
        self.assertEqual(3, len(matches))
        
        # Test getting matches with exclusions
        matches = self.precompute_service.get_precomputed_matches("user1", {"user2", "user4"})
        self.assertEqual(1, len(matches))
        self.assertEqual("user3", matches[0][0])
        
        # Test getting matches for non-existent user
        matches = self.precompute_service.get_precomputed_matches("nonexistent", set())
        self.assertEqual(0, len(matches))
        
    @patch('services.precompute_service.PrecomputeService._compute_scores_in_nearby_quadrants')
    @patch('services.precompute_service.PrecomputeService._compute_scores_in_other_quadrants')
    @patch('services.precompute_service.PrecomputeService._update_other_users_precomputed_matches')
    def test_precompute_matches(self, mock_update_others, mock_compute_others, mock_compute_nearby):
        profile_service = MagicMock()
        geo_service = MagicMock()
        matching_service = MagicMock()
        
        geo_service.get_profile_geohash = MagicMock(return_value="w4rqc")
        geo_service.get_adjacent_quadrants = MagicMock(return_value=["w4rqc"])
        
        service = PrecomputeService(profile_service, geo_service, matching_service)
        
        service.quadrant_scores = {}
        service.precomputed_matches = {}
        
        service.precompute_matches("user1")
        
        geo_service.get_profile_geohash.assert_called_once_with("user1")
        geo_service.get_adjacent_quadrants.assert_called_once_with("w4rqc")
        
        mock_compute_nearby.assert_called_once_with("user1", "w4rqc", ["w4rqc"])
        mock_compute_others.assert_called_once_with("user1", "w4rqc", ["w4rqc"])
        mock_update_others.assert_called_once_with("user1")
        
        self.assertIn("w4rqc", service.quadrant_scores)
        
    def test_match_store_compatibility(self):
        # Test that the service can be used as a MatchStore
        match_store = self.precompute_service.get_match_store()
        
        # Verify it's the same object
        self.assertEqual(self.precompute_service, match_store)

if __name__ == '__main__':
    unittest.main()
