import unittest
import sys
import os
from unittest.mock import patch, MagicMock

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from geo_index import GeoIndex
from models import Location

class TestGeoIndex(unittest.TestCase):
    def setUp(self):
        self.geo_index = GeoIndex(precision=5)
        
    def test_add_location(self):
        """Test adding a location returns correct geohash and updates index."""
        location = Location(lat=37.7749, lon=-122.4194)
        user_id = "user1"
        
        geohash = self.geo_index.add_location(user_id, location)
        
        self.assertTrue(geohash)
        self.assertEqual(len(geohash), 5)
        
        self.assertIn(geohash, self.geo_index.quadrant_index)
        self.assertIn(user_id, self.geo_index.quadrant_index[geohash])
        
        self.assertEqual(self.geo_index.get_geohash(user_id), geohash)
        
    def test_get_adjacent_quadrants(self):
        """Test getting adjacent quadrants returns correct number of neighbors."""
        location = Location(lat=37.7749, lon=-122.4194)
        user_id = "user1"
        
        geohash = self.geo_index.add_location(user_id, location)
        
        adjacent = self.geo_index.get_adjacent_quadrants(geohash)
        
        self.assertGreaterEqual(len(adjacent), 1)
        self.assertLessEqual(len(adjacent), 9)
        self.assertIn(geohash, adjacent)
        
    def test_get_users_in_quadrant(self):
        """Test retrieving users from a quadrant."""
        sf_location = Location(lat=37.7749, lon=-122.4194)
        oak_location = Location(lat=37.8044, lon=-122.2711)
        
        user1_id = "user1"
        user2_id = "user2"
        user3_id = "user3"
        
        user1_gh = self.geo_index.add_location(user1_id, sf_location)
        user2_gh = self.geo_index.add_location(user2_id, sf_location)
        user3_gh = self.geo_index.add_location(user3_id, oak_location)
        
        users_in_sf = self.geo_index.get_users_in_quadrant(user1_gh)
        
        self.assertIn(user1_id, users_in_sf)
        self.assertIn(user2_id, users_in_sf)
        
        if user1_gh != user3_gh:
            self.assertNotIn(user3_id, users_in_sf)
            
    def test_calculate_distance(self):
        """Test distance calculation between two locations."""
        sf = Location(lat=37.7749, lon=-122.4194)
        oak = Location(lat=37.8044, lon=-122.2711)
        nyc = Location(lat=40.7128, lon=-74.0060)
        
        sf_to_oak = GeoIndex.calculate_distance(sf, oak)
        sf_to_nyc = GeoIndex.calculate_distance(sf, nyc)
        
        self.assertLess(sf_to_oak, 15)
        self.assertGreater(sf_to_oak, 5)
        
        self.assertGreater(sf_to_nyc, 3000)
        
    def test_error_handling_in_adjacent_quadrants(self):
        """Test error handling in get_adjacent_quadrants method."""
        with patch('geohash.decode', side_effect=Exception("Invalid geohash")):
            result = self.geo_index.get_adjacent_quadrants("invalid")
            self.assertEqual(result, ["invalid"])
            
    def test_get_geohash_nonexistent_user(self):
        """Test getting geohash for nonexistent user."""
        self.assertEqual(self.geo_index.get_geohash("nonexistent"), "")

if __name__ == '__main__':
    unittest.main()
