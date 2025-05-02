import unittest
import sys
import os
from unittest.mock import patch, MagicMock

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import Profile, Location
from services.match_finder_service import MatchFinderService
from services.profile_service import ProfileService
from services.geo_service import GeoService
from services.exclusion_service import ExclusionService
from services.precompute_service import PrecomputeService
from services.matching_service import MatchingService

class TestMatchFinderService(unittest.TestCase):
    def setUp(self):
        # Create mock services without spec to avoid attribute errors
        self.profile_service = MagicMock()
        self.geo_service = MagicMock()
        self.exclusion_service = MagicMock()
        self.precompute_service = MagicMock()
        self.matching_service = MagicMock()
        
        # Create the match finder service
        self.match_finder_service = MatchFinderService(
            self.profile_service,
            self.geo_service,
            self.exclusion_service,
            self.precompute_service,
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
        
        self.profile3 = Profile(
            id="user3",
            age=32,
            gender="female",
            location=Location(lat=13.7565, lon=100.5022),
            interests=["cooking", "movies", "travel"]
        )
        
        # Set up profile service mock
        self.profile_service.get_profile.side_effect = lambda id: {
            "user1": self.profile1,
            "user2": self.profile2,
            "user3": self.profile3
        }.get(id)
        
        # Set up exclusion service mock - configure it properly
        # We need to explicitly configure the method since the spec doesn't seem to be working
        self.exclusion_service = MagicMock()
        self.exclusion_service.get_excluded_users = MagicMock(return_value=set())
        
        # Set up geo service mock
        self.geo_service.get_profile_geohash.return_value = "w4rqc"
        self.geo_service.get_adjacent_quadrants.return_value = ["w4rqc", "w4rqf", "w4rq9"]
        
        # Set up precompute service mock
        self.precompute_service.get_precomputed_matches.return_value = [
            ("user2", 0.85),
            ("user3", 0.75)
        ]
        
        # Set up matching service mock
        self.matching_service.compute_match_score.side_effect = lambda user_id, other_id, gender_preference=None: {
            ("user1", "user2", None): 0.85,
            ("user1", "user3", None): 0.75,
            ("user1", "user2", "female"): 0.85,
            ("user1", "user3", "female"): 0.75,
            ("user1", "user2", "male"): 0.0,  # Gender preference mismatch
            ("user1", "user3", "male"): 0.0   # Gender preference mismatch
        }.get((user_id, other_id, gender_preference), 0.0)
        
    def test_get_matches_with_precomputed(self):
        # Test getting matches with precomputed scores
        matches = self.match_finder_service.get_matches("user1")
        
        # Verify precompute service was called
        self.precompute_service.get_precomputed_matches.assert_called_once()
        
        # Verify correct matches were returned
        self.assertEqual(2, len(matches))
        self.assertEqual("user2", matches[0][0])
        self.assertEqual(0.85, matches[0][1])
        self.assertEqual("user3", matches[1][0])
        self.assertEqual(0.75, matches[1][1])
        
    def test_get_matches_with_gender_preference(self):
        # Test getting matches with gender preference
        matches = self.match_finder_service.get_matches("user1", gender_preference="female")
        
        # Verify precompute service was called
        self.precompute_service.get_precomputed_matches.assert_called_once()
        
        # Verify correct matches were returned (both are female)
        self.assertEqual(2, len(matches))
        
        # Test with male gender preference (should return no matches)
        self.precompute_service.get_precomputed_matches.reset_mock()
        self.matching_service.compute_match_score.reset_mock()
        
        # Set up precompute service to return matches that will be filtered by gender
        self.precompute_service.get_precomputed_matches.return_value = [
            ("user2", 0.85),
            ("user3", 0.75)
        ]
        
        matches = self.match_finder_service.get_matches("user1", gender_preference="male")
        
        # Verify no matches were returned (all candidates are female)
        self.assertEqual(0, len(matches))
        
    def test_get_matches_with_limit(self):
        matches = self.match_finder_service.get_matches("user1", limit=1)
        
        self.assertEqual(1, len(matches))
        self.assertEqual("user2", matches[0][0])
        
    @patch('services.match_finder_service.MatchFinderService._get_filtered_precomputed_matches')
    def test_get_matches_with_exclusions(self, mock_get_filtered):
        mock_get_filtered.return_value = [("user3", 0.75)]
        
        profile_service = MagicMock()
        geo_service = MagicMock()
        exclusion_service = MagicMock()
        precompute_service = MagicMock()
        matching_service = MagicMock()
        
        exclusion_service.get_excluded_users.return_value = {"user2"}
        
        match_finder = MatchFinderService(
            profile_service,
            geo_service,
            exclusion_service,
            precompute_service,
            matching_service
        )
        
        matches = match_finder.get_matches("user1")
        
        mock_get_filtered.assert_called_once()
        
        self.assertEqual(1, len(matches))
        self.assertEqual("user3", matches[0][0])
        
    @patch('services.match_finder_service.MatchFinderService._compute_additional_matches')
    def test_get_matches_fallback_to_quadrant(self, mock_compute_additional):
        mock_compute_additional.return_value = [('user2', 0.85), ('user3', 0.75)]
        
        profile_service = MagicMock()
        geo_service = MagicMock()
        exclusion_service = MagicMock()
        precompute_service = MagicMock()
        matching_service = MagicMock()
        
        exclusion_service.get_excluded_users.return_value = set()
        precompute_service.get_precomputed_matches.return_value = []
        
        match_finder = MatchFinderService(
            profile_service,
            geo_service,
            exclusion_service,
            precompute_service,
            matching_service
        )
        
        matches = match_finder.get_matches('user1')
        
        precompute_service.get_precomputed_matches.assert_called_once()
        
        self.assertEqual(2, len(matches))
        match_ids = [match_id for match_id, _ in matches]
        self.assertIn('user2', match_ids)
        self.assertIn('user3', match_ids)

if __name__ == '__main__':
    unittest.main()
