from typing import Dict, Set

class ExclusionManager:
    def __init__(self):
        self.blocked_users: Dict[str, Set[str]] = {}
        self.matched_users: Dict[str, Set[str]] = {}
        self.disliked_users: Dict[str, Set[str]] = {}

    def initialize_user(self, user_id: str) -> None:
        """Initialize exclusion sets for a new user."""
        self.blocked_users[user_id] = set()
        self.matched_users[user_id] = set()
        self.disliked_users[user_id] = set()

    def add_exclusion(self, user_id: str, excluded_id: str, exclusion_type: str) -> None:
        """Add a user to the specified exclusion list."""
        if exclusion_type == "blocked":
            self.blocked_users[user_id].add(excluded_id)
        elif exclusion_type == "matched":
            self.matched_users[user_id].add(excluded_id)
        elif exclusion_type == "disliked":
            self.disliked_users[user_id].add(excluded_id)

    def get_excluded_users(self, user_id: str) -> Set[str]:
        """Get all excluded users for a given user."""
        return (self.blocked_users.get(user_id, set()) |
                self.matched_users.get(user_id, set()) |
                self.disliked_users.get(user_id, set()))
