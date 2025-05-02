import unittest
import sys
import os
from unittest.mock import patch, MagicMock

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import Profile, Location
from services.profile_service import ProfileService

class TestProfileService(unittest.TestCase):
    def setUp(self):
        self.profile_service = ProfileService()
        
        # Create test profiles
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
        
    def test_add_profile(self):
        # Add a profile
        self.profile_service.add_profile(self.profile1)
        
        # Verify profile was added
        profiles = self.profile_service.get_profiles()
        self.assertIn("user1", profiles)
        self.assertEqual(self.profile1, profiles["user1"])
        
    def test_update_profile(self):
        # Add a profile
        self.profile_service.add_profile(self.profile1)
        
        # Create updated profile
        updated_profile = Profile(
            id="user1",
            age=31,  # Updated age
            gender="male",
            location=Location(lat=13.7563, lon=100.5018),
            interests=["hiking", "reading", "cooking", "gaming"]  # Added interest
        )
        
        # Update the profile
        self.profile_service.update_profile("user1", updated_profile)
        
        # Verify profile was updated
        profiles = self.profile_service.get_profiles()
        self.assertEqual(31, profiles["user1"].age)
        self.assertIn("gaming", profiles["user1"].interests)
        
    def test_update_profile_nonexistent(self):
        # Try to update a non-existent profile
        with self.assertRaises(ValueError):
            self.profile_service.update_profile("nonexistent", self.profile1)
            
    def test_update_profile_id_mismatch(self):
        # Add a profile
        self.profile_service.add_profile(self.profile1)
        
        # Create profile with different ID
        profile_with_different_id = Profile(
            id="different_id",
            age=30,
            gender="male",
            location=Location(lat=13.7563, lon=100.5018),
            interests=["hiking", "reading", "cooking"]
        )
        
        # Update should correct the ID
        self.profile_service.update_profile("user1", profile_with_different_id)
        
        # Verify ID was corrected
        profiles = self.profile_service.get_profiles()
        self.assertEqual("user1", profiles["user1"].id)
        
    def test_get_profile(self):
        # Add a profile
        self.profile_service.add_profile(self.profile1)
        
        # Get the profile
        profile = self.profile_service.get_profile("user1")
        
        # Verify correct profile was returned
        self.assertEqual(self.profile1, profile)
        
    def test_get_profile_nonexistent(self):
        # Try to get a non-existent profile
        with self.assertRaises(ValueError):
            self.profile_service.get_profile("nonexistent")
            
    def test_get_all_profiles(self):
        # Add multiple profiles
        self.profile_service.add_profile(self.profile1)
        self.profile_service.add_profile(self.profile2)
        
        # Get all profiles
        profiles = self.profile_service.get_all_profiles()
        
        # Verify all profiles are returned
        self.assertEqual(2, len(profiles))
        self.assertIn(self.profile1, profiles)
        self.assertIn(self.profile2, profiles)
        
    def test_bulk_add_profiles(self):
        # Bulk add profiles
        self.profile_service.bulk_add_profiles([self.profile1, self.profile2])
        
        # Verify all profiles were added
        profiles = self.profile_service.get_profiles()
        self.assertEqual(2, len(profiles))
        self.assertIn("user1", profiles)
        self.assertIn("user2", profiles)
        
    def test_get_profiles(self):
        # Add profiles
        self.profile_service.add_profile(self.profile1)
        self.profile_service.add_profile(self.profile2)
        
        # Get profiles dictionary
        profiles = self.profile_service.get_profiles()
        
        # Verify dictionary contains expected profiles
        self.assertEqual(2, len(profiles))
        self.assertIn("user1", profiles)
        self.assertIn("user2", profiles)
        self.assertEqual(self.profile1, profiles["user1"])
        self.assertEqual(self.profile2, profiles["user2"])

if __name__ == '__main__':
    unittest.main()
