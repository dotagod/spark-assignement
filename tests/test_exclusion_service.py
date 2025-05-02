import unittest
import sys
import os
from unittest.mock import patch, MagicMock

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.exclusion_service import ExclusionService

class TestExclusionService(unittest.TestCase):
    def setUp(self):
        self.exclusion_service = ExclusionService()
        
    def test_initialize_user(self):
        # Initialize a new user
        self.exclusion_service.initialize_user("user1")
        
        # Verify user exists in all exclusion sets
        self.assertIn("user1", self.exclusion_service.blocked_users)
        self.assertIn("user1", self.exclusion_service.matched_users)
        self.assertIn("user1", self.exclusion_service.disliked_users)
        
        # Verify sets are empty
        self.assertEqual(0, len(self.exclusion_service.blocked_users["user1"]))
        self.assertEqual(0, len(self.exclusion_service.matched_users["user1"]))
        self.assertEqual(0, len(self.exclusion_service.disliked_users["user1"]))
        
    def test_add_exclusion_blocked(self):
        # Initialize user
        self.exclusion_service.initialize_user("user1")
        
        # Add blocked exclusion
        self.exclusion_service.add_exclusion("user1", "user2", "blocked")
        
        # Verify user2 is in user1's blocked list
        self.assertIn("user2", self.exclusion_service.blocked_users["user1"])
        
        # Verify user2 is not in other lists
        self.assertNotIn("user2", self.exclusion_service.matched_users["user1"])
        self.assertNotIn("user2", self.exclusion_service.disliked_users["user1"])
        
    def test_add_exclusion_matched(self):
        # Initialize user
        self.exclusion_service.initialize_user("user1")
        
        # Add matched exclusion
        self.exclusion_service.add_exclusion("user1", "user2", "matched")
        
        # Verify user2 is in user1's matched list
        self.assertIn("user2", self.exclusion_service.matched_users["user1"])
        
        # Verify user2 is not in other lists
        self.assertNotIn("user2", self.exclusion_service.blocked_users["user1"])
        self.assertNotIn("user2", self.exclusion_service.disliked_users["user1"])
        
    def test_add_exclusion_disliked(self):
        # Initialize user
        self.exclusion_service.initialize_user("user1")
        
        # Add disliked exclusion
        self.exclusion_service.add_exclusion("user1", "user2", "disliked")
        
        # Verify user2 is in user1's disliked list
        self.assertIn("user2", self.exclusion_service.disliked_users["user1"])
        
        # Verify user2 is not in other lists
        self.assertNotIn("user2", self.exclusion_service.blocked_users["user1"])
        self.assertNotIn("user2", self.exclusion_service.matched_users["user1"])
        
    def test_add_exclusion_invalid_type(self):
        # Initialize user
        self.exclusion_service.initialize_user("user1")
        
        # Add invalid exclusion type
        with self.assertRaises(ValueError):
            self.exclusion_service.add_exclusion("user1", "user2", "invalid")
            
    def test_get_excluded_users(self):
        # Initialize user
        self.exclusion_service.initialize_user("user1")
        
        # Add exclusions of different types
        self.exclusion_service.add_exclusion("user1", "user2", "blocked")
        self.exclusion_service.add_exclusion("user1", "user3", "matched")
        self.exclusion_service.add_exclusion("user1", "user4", "disliked")
        
        # Get all excluded users
        excluded = self.exclusion_service.get_excluded_users("user1")
        
        # Verify all users are in the excluded set
        self.assertIn("user2", excluded)
        self.assertIn("user3", excluded)
        self.assertIn("user4", excluded)
        self.assertEqual(3, len(excluded))
        
    def test_get_excluded_users_nonexistent(self):
        # Get excluded users for non-existent user
        excluded = self.exclusion_service.get_excluded_users("nonexistent")
        
        # Should return empty set
        self.assertEqual(0, len(excluded))
        
    def test_exclusion_manager_compatibility(self):
        # Test that the service can be used as an ExclusionManager
        manager = self.exclusion_service.get_exclusion_manager()
        
        # Verify it's the same object
        self.assertEqual(self.exclusion_service, manager)

if __name__ == '__main__':
    unittest.main()
