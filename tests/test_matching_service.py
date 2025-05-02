import unittest
import sys
import os
from unittest.mock import patch, MagicMock

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import Profile, Location
from services.matching_service import MatchingService
from services.profile_service import ProfileService
from services.geo_service import GeoService

class TestMatchingService(unittest.TestCase):
    def setUp(self):
        # Create mock services
        self.profile_service = MagicMock(spec=ProfileService)
        self.geo_service = MagicMock(spec=GeoService)
        
        # Create the matching service
        self.matching_service = MatchingService(self.profile_service, self.geo_service)
        
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
            location=Location(lat=13.7560, lon=100.5020),  # Very close to profile1
            interests=["hiking", "photography", "travel"]
        )
        
        self.profile3 = Profile(
            id="user3",
            age=45,
            gender="male",
            location=Location(lat=13.8563, lon=100.6018),  # Further away
            interests=["cooking", "movies", "music"]
        )
        
        # Set up profile service mock
        self.profile_service.get_profile.side_effect = lambda id: {
            "user1": self.profile1,
            "user2": self.profile2,
            "user3": self.profile3
        }.get(id)
        
        # Set up geo service mock for distance calculation
        def calculate_distance_mock(loc1, loc2):
            # Using string representation as keys since Location objects aren't hashable
            loc_pairs = {
                f"{self.profile1.location.lat},{self.profile1.location.lon}|{self.profile2.location.lat},{self.profile2.location.lon}": 0.5,
                f"{self.profile2.location.lat},{self.profile2.location.lon}|{self.profile1.location.lat},{self.profile1.location.lon}": 0.5,
                f"{self.profile1.location.lat},{self.profile1.location.lon}|{self.profile3.location.lat},{self.profile3.location.lon}": 15.0,
                f"{self.profile3.location.lat},{self.profile3.location.lon}|{self.profile1.location.lat},{self.profile1.location.lon}": 15.0,
                f"{self.profile2.location.lat},{self.profile2.location.lon}|{self.profile3.location.lat},{self.profile3.location.lon}": 14.5,
                f"{self.profile3.location.lat},{self.profile3.location.lon}|{self.profile2.location.lat},{self.profile2.location.lon}": 14.5,
            }
            key = f"{loc1.lat},{loc1.lon}|{loc2.lat},{loc2.lon}"
            return loc_pairs.get(key, 0)
            
        self.geo_service.calculate_distance.side_effect = calculate_distance_mock
        
    def test_compute_age_score(self):
        # Test age score calculation
        score = self.matching_service._compute_age_score(30, 28)
        self.assertAlmostEqual(0.3, score, delta=0.05)  # 30% weight, small age difference
        
        score = self.matching_service._compute_age_score(30, 50)
        self.assertAlmostEqual(0.0, score, delta=0.05)  # 30% weight, large age difference
        
    def test_compute_interest_score(self):
        # Test interest score calculation
        # 1 common interest out of 5 total
        score = self.matching_service._compute_interest_score(
            ["hiking", "reading", "cooking"],
            ["travel", "photography", "hiking"]
        )
        self.assertAlmostEqual(0.06, score, delta=0.05)  # 30% weight, 1/5 interests match
        
        # No common interests
        score = self.matching_service._compute_interest_score(
            ["hiking", "reading", "cooking"],
            ["travel", "photography", "music"]
        )
        self.assertAlmostEqual(0.0, score, delta=0.05)  # 30% weight, 0/6 interests match
        
        # All interests match
        score = self.matching_service._compute_interest_score(
            ["hiking", "reading"],
            ["hiking", "reading"]
        )
        self.assertAlmostEqual(0.3, score, delta=0.05)  # 30% weight, 2/2 interests match
        
    def test_compute_location_score(self):
        # Test location score calculation
        # Close locations (0.5 km)
        self.geo_service.calculate_distance.return_value = 0.5
        score = self.matching_service._compute_location_score(
            self.profile1.location, self.profile2.location
        )
        self.assertAlmostEqual(0.38, score, delta=0.05)  # 40% weight, close distance
        
        # Far locations (15 km, beyond max_distance of 10 km)
        self.geo_service.calculate_distance.return_value = 15.0
        score = self.matching_service._compute_location_score(
            self.profile1.location, self.profile3.location
        )
        self.assertAlmostEqual(0.0, score, delta=0.05)  # 40% weight, beyond max distance
        
    def test_compute_match_score(self):
        # Test overall match score calculation
        # Good match: close age, some common interests, close location
        score = self.matching_service.compute_match_score("user1", "user2")
        self.assertGreater(score, 0.5)  # Should be a good match
        
        # Poor match: different age, few common interests, far location
        score = self.matching_service.compute_match_score("user1", "user3")
        self.assertLess(score, 0.3)  # Should be a poor match
        
    def test_compute_match_score_with_gender_preference(self):
        # Test match score with gender preference
        # Matching gender preference
        score = self.matching_service.compute_match_score("user1", "user2", gender_preference="female")
        self.assertGreater(score, 0.0)  # Should match
        
        # Non-matching gender preference
        score = self.matching_service.compute_match_score("user1", "user3", gender_preference="female")
        self.assertEqual(score, 0.0)  # Should not match
        
    def test_is_within_matching_distance(self):
        # Test distance matching
        # Close profiles
        result = self.matching_service.is_within_matching_distance("user1", "user2")
        self.assertTrue(result)
        
        # Distant profiles
        result = self.matching_service.is_within_matching_distance("user1", "user3")
        self.assertFalse(result)
        
    def test_score_calculator_compatibility(self):
        # Test that the service can be used as a ScoreCalculator
        calculator = self.matching_service.get_score_calculator()
        
        # Verify it's the same object
        self.assertEqual(self.matching_service, calculator)

if __name__ == '__main__':
    unittest.main()
