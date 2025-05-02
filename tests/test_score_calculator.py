import unittest
import sys
import os
from unittest.mock import patch, MagicMock

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from score_calculator import ScoreCalculator
from models import Profile, Location

class TestScoreCalculator(unittest.TestCase):
    def setUp(self):
        self.score_calculator = ScoreCalculator(max_distance_km=10)
        
    def test_compute_age_score(self):
        """Test age score calculation."""
        self.assertAlmostEqual(self.score_calculator._compute_age_score(25, 25), 0.3)
        self.assertAlmostEqual(self.score_calculator._compute_age_score(25, 35), 0.15)
        self.assertAlmostEqual(self.score_calculator._compute_age_score(25, 45), 0.0)
        self.assertAlmostEqual(self.score_calculator._compute_age_score(25, 50), 0.0)
        
    def test_compute_interest_score(self):
        """Test interest score calculation."""
        interests1 = ["music", "movies", "hiking"]
        interests2 = ["music", "movies", "hiking"]
        self.assertAlmostEqual(self.score_calculator._compute_interest_score(interests1, interests2), 0.3)
        
        interests1 = ["music", "movies", "hiking"]
        interests2 = ["music", "reading", "cooking"]
        self.assertAlmostEqual(self.score_calculator._compute_interest_score(interests1, interests2), 0.06)
        
        interests1 = ["music", "movies", "hiking"]
        interests2 = ["reading", "cooking", "gaming"]
        self.assertAlmostEqual(self.score_calculator._compute_interest_score(interests1, interests2), 0.0)
        
        self.assertAlmostEqual(self.score_calculator._compute_interest_score([], []), 0.0)
        
    def test_compute_location_score(self):
        """Test location score calculation."""
        loc1 = Location(lat=37.7749, lon=-122.4194)
        loc2 = Location(lat=37.7749, lon=-122.4194)
        self.assertAlmostEqual(self.score_calculator._compute_location_score(loc1, loc2), 0.4)
        
        with patch('geo_index.GeoIndex.calculate_distance') as mock_distance:
            mock_distance.return_value = 5.0
            self.assertAlmostEqual(self.score_calculator._compute_location_score(loc1, loc2), 0.2)
            
            mock_distance.return_value = 10.0
            self.assertAlmostEqual(self.score_calculator._compute_location_score(loc1, loc2), 0.0)
            
            mock_distance.return_value = 15.0
            self.assertAlmostEqual(self.score_calculator._compute_location_score(loc1, loc2), 0.0)
            
    def test_is_within_matching_distance(self):
        """Test checking if users are within matching distance."""
        user1 = Profile(
            id="user1",
            age=25,
            gender="male",
            location=Location(lat=37.7749, lon=-122.4194),
            interests=["music", "movies"]
        )
        user2 = Profile(
            id="user2",
            age=27,
            gender="female",
            location=Location(lat=37.7749, lon=-122.4194),
            interests=["music", "hiking"]
        )
        
        with patch('geo_index.GeoIndex.calculate_distance') as mock_distance:
            mock_distance.return_value = 5.0
            self.assertTrue(self.score_calculator.is_within_matching_distance(user1, user2))
            
            mock_distance.return_value = 10.0
            self.assertTrue(self.score_calculator.is_within_matching_distance(user1, user2))
            
            mock_distance.return_value = 10.1
            self.assertFalse(self.score_calculator.is_within_matching_distance(user1, user2))
            
    def test_compute_match_score(self):
        """Test overall match score calculation."""
        user1 = Profile(
            id="user1",
            age=25,
            gender="male",
            location=Location(lat=37.7749, lon=-122.4194),
            interests=["music", "movies", "hiking"]
        )
        user2 = Profile(
            id="user2",
            age=27,
            gender="female",
            location=Location(lat=37.7749, lon=-122.4194),
            interests=["music", "hiking", "reading"]
        )
        
        with patch.object(ScoreCalculator, '_compute_age_score') as mock_age_score, \
             patch.object(ScoreCalculator, '_compute_interest_score') as mock_interest_score, \
             patch.object(ScoreCalculator, '_compute_location_score') as mock_location_score:
            
            mock_age_score.return_value = 0.25
            mock_interest_score.return_value = 0.2
            mock_location_score.return_value = 0.35
            
            score = self.score_calculator.compute_match_score(user1, user2)
            self.assertAlmostEqual(score, 0.8, places=1)
            
            score = self.score_calculator.compute_match_score(user1, user2, gender_preference="female")
            self.assertAlmostEqual(score, 0.8, places=1)
            
            score = self.score_calculator.compute_match_score(user1, user2, gender_preference="male")
            self.assertEqual(score, 0.0)

if __name__ == '__main__':
    unittest.main()
