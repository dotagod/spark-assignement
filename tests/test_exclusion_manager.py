import unittest
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from exclusion_manager import ExclusionManager

class TestExclusionManager(unittest.TestCase):
    def setUp(self):
        self.exclusion_manager = ExclusionManager()
        
    def test_initialize_user(self):
        """Test initializing a new user creates empty exclusion sets."""
        user_id = "user1"
        
        self.exclusion_manager.initialize_user(user_id)
        
        self.assertIn(user_id, self.exclusion_manager.blocked_users)
        self.assertIn(user_id, self.exclusion_manager.matched_users)
        self.assertIn(user_id, self.exclusion_manager.disliked_users)
        
        self.assertEqual(len(self.exclusion_manager.blocked_users[user_id]), 0)
        self.assertEqual(len(self.exclusion_manager.matched_users[user_id]), 0)
        self.assertEqual(len(self.exclusion_manager.disliked_users[user_id]), 0)
        
    def test_add_exclusion_blocked(self):
        """Test adding a blocked exclusion."""
        user_id = "user1"
        excluded_id = "user2"
        
        self.exclusion_manager.initialize_user(user_id)
        
        self.exclusion_manager.add_exclusion(user_id, excluded_id, "blocked")
        
        self.assertIn(excluded_id, self.exclusion_manager.blocked_users[user_id])
        
        self.assertNotIn(excluded_id, self.exclusion_manager.matched_users[user_id])
        self.assertNotIn(excluded_id, self.exclusion_manager.disliked_users[user_id])
        
    def test_add_exclusion_matched(self):
        """Test adding a matched exclusion."""
        user_id = "user1"
        excluded_id = "user2"
        
        self.exclusion_manager.initialize_user(user_id)
        
        self.exclusion_manager.add_exclusion(user_id, excluded_id, "matched")
        
        self.assertIn(excluded_id, self.exclusion_manager.matched_users[user_id])
        
        self.assertNotIn(excluded_id, self.exclusion_manager.blocked_users[user_id])
        self.assertNotIn(excluded_id, self.exclusion_manager.disliked_users[user_id])
        
    def test_add_exclusion_disliked(self):
        """Test adding a disliked exclusion."""
        user_id = "user1"
        excluded_id = "user2"
        
        self.exclusion_manager.initialize_user(user_id)
        
        self.exclusion_manager.add_exclusion(user_id, excluded_id, "disliked")
        
        self.assertIn(excluded_id, self.exclusion_manager.disliked_users[user_id])
        
        self.assertNotIn(excluded_id, self.exclusion_manager.blocked_users[user_id])
        self.assertNotIn(excluded_id, self.exclusion_manager.matched_users[user_id])
        
    def test_get_excluded_users(self):
        """Test getting all excluded users."""
        user_id = "user1"
        blocked_id = "user2"
        matched_id = "user3"
        disliked_id = "user4"
        
        self.exclusion_manager.initialize_user(user_id)
        
        self.exclusion_manager.add_exclusion(user_id, blocked_id, "blocked")
        self.exclusion_manager.add_exclusion(user_id, matched_id, "matched")
        self.exclusion_manager.add_exclusion(user_id, disliked_id, "disliked")
        
        excluded = self.exclusion_manager.get_excluded_users(user_id)
        
        self.assertIn(blocked_id, excluded)
        self.assertIn(matched_id, excluded)
        self.assertIn(disliked_id, excluded)
        self.assertEqual(len(excluded), 3)
        
    def test_get_excluded_users_nonexistent(self):
        """Test getting excluded users for nonexistent user."""
        excluded = self.exclusion_manager.get_excluded_users("nonexistent")
        self.assertEqual(len(excluded), 0)
        
    def test_add_same_exclusion_twice(self):
        """Test adding the same exclusion twice."""
        user_id = "user1"
        excluded_id = "user2"
        
        self.exclusion_manager.initialize_user(user_id)
        
        self.exclusion_manager.add_exclusion(user_id, excluded_id, "blocked")
        self.exclusion_manager.add_exclusion(user_id, excluded_id, "blocked")
        
        self.assertIn(excluded_id, self.exclusion_manager.blocked_users[user_id])
        self.assertEqual(len(self.exclusion_manager.blocked_users[user_id]), 1)

if __name__ == '__main__':
    unittest.main()
