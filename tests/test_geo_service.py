import unittest
import sys
import os
from unittest.mock import patch, MagicMock
import math

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import Location
from services.geo_service import GeoService

class TestGeoService(unittest.TestCase):
    def setUp(self):
        self.geo_service = GeoService()
        
    def test_index_profile(self):
        # Test adding a profile to the geospatial index
        location = Location(lat=13.7563, lon=100.5018)
        geohash = self.geo_service.index_profile("user1", location)
        
        # Verify geohash is returned
        self.assertIsNotNone(geohash)
        self.assertTrue(len(geohash) > 0)
        
        # Verify user is in the quadrant
        users = self.geo_service.get_users_in_quadrant(geohash)
        self.assertIn("user1", users)
        
    def test_remove_from_index(self):
        # Add a user to the index
        location = Location(lat=13.7563, lon=100.5018)
        geohash = self.geo_service.index_profile("user1", location)
        
        # Remove the user
        result = self.geo_service.remove_from_index(geohash, "user1")
        self.assertTrue(result)
        
        # Verify user is no longer in the quadrant
        users = self.geo_service.get_users_in_quadrant(geohash)
        self.assertNotIn("user1", users)
        
        # Test removing a non-existent user
        result = self.geo_service.remove_from_index(geohash, "nonexistent")
        self.assertFalse(result)
        
    def test_get_users_in_quadrant(self):
        # Add multiple users to the same quadrant
        location = Location(lat=13.7563, lon=100.5018)
        geohash = self.geo_service.index_profile("user1", location)
        self.geo_service.index_profile("user2", location)
        
        # Get users in the quadrant
        users = self.geo_service.get_users_in_quadrant(geohash)
        self.assertIn("user1", users)
        self.assertIn("user2", users)
        self.assertEqual(2, len(users))
        
        # Test empty quadrant
        users = self.geo_service.get_users_in_quadrant("nonexistent")
        self.assertEqual(0, len(users))
        
    def test_get_adjacent_quadrants(self):
        # Test getting adjacent quadrants
        location = Location(lat=13.7563, lon=100.5018)
        geohash = self.geo_service.index_profile("user1", location)
        
        adjacents = self.geo_service.get_adjacent_quadrants(geohash)
        
        # Should return 9 quadrants (original + 8 adjacent)
        self.assertEqual(9, len(adjacents))
        self.assertIn(geohash, adjacents)
        
        # Test with invalid geohash
        adjacents = self.geo_service.get_adjacent_quadrants("")
        self.assertEqual(0, len(adjacents))
        
    def test_get_profile_geohash(self):
        # Add a user to the index
        location = Location(lat=13.7563, lon=100.5018)
        geohash = self.geo_service.index_profile("user1", location)
        
        # Get the user's geohash
        user_geohash = self.geo_service.get_profile_geohash("user1")
        self.assertEqual(geohash, user_geohash)
        
        # Test non-existent user
        user_geohash = self.geo_service.get_profile_geohash("nonexistent")
        self.assertEqual("", user_geohash)
        
    def test_calculate_distance(self):
        # Test distance calculation
        bangkok = Location(lat=13.7563, lon=100.5018)
        singapore = Location(lat=1.3521, lon=103.8198)
        
        # Distance between Bangkok and Singapore is approximately 1450 km
        distance = self.geo_service.calculate_distance(bangkok, singapore)
        self.assertAlmostEqual(1450, distance, delta=50)
        
        # Distance to self should be 0
        distance = self.geo_service.calculate_distance(bangkok, bangkok)
        self.assertAlmostEqual(0, distance, delta=0.1)

if __name__ == '__main__':
    unittest.main()
