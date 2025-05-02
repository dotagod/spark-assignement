from typing import Dict, Set
from services.interfaces import IExclusionService

class ExclusionService(IExclusionService):
    """Service for managing user exclusions (blocked, matched, disliked)."""
    
    def __init__(self):
        self.blocked_users: Dict[str, Set[str]] = {}
        self.matched_users: Dict[str, Set[str]] = {}
        self.disliked_users: Dict[str, Set[str]] = {}
        
    def get_exclusion_manager(self):
        """Get the exclusion manager.
        
        Returns:
            The ExclusionManager instance - this is now the service itself for backward compatibility
        """
        return self
        
    def initialize_user(self, user_id: str) -> None:
        """Initialize exclusion sets for a new user.
        
        Args:
            user_id: ID of the user to initialize
        """
        self.blocked_users[user_id] = set()
        self.matched_users[user_id] = set()
        self.disliked_users[user_id] = set()
        
    def add_exclusion(self, user_id: str, excluded_id: str, exclusion_type: str) -> None:
        """Add a user to an exclusion list.
        
        Args:
            user_id: ID of the user adding the exclusion
            excluded_id: ID of the user to exclude
            exclusion_type: Type of exclusion (blocked, matched, disliked)
            
        Raises:
            ValueError: If the exclusion_type is invalid
        """
        if exclusion_type not in ["blocked", "matched", "disliked"]:
            raise ValueError(f"Invalid exclusion type: {exclusion_type}")
            
        if exclusion_type == "blocked":
            self.blocked_users[user_id].add(excluded_id)
        elif exclusion_type == "matched":
            self.matched_users[user_id].add(excluded_id)
        elif exclusion_type == "disliked":
            self.disliked_users[user_id].add(excluded_id)
        
    def get_excluded_users(self, user_id: str) -> Set[str]:
        """Get all excluded users for a user.
        
        Args:
            user_id: ID of the user
            
        Returns:
            Set of excluded user IDs
        """
        return (self.blocked_users.get(user_id, set()) |
                self.matched_users.get(user_id, set()) |
                self.disliked_users.get(user_id, set()))
