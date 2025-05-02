from typing import Dict, Set, Tuple, List
import math
import sys
from models import Location

import geohash

class GeoIndex:
    def __init__(self, precision: int = 5):
        self.precision = precision
        self.quadrant_index: Dict[str, Set[str]] = {}

    def add_location(self, user_id: str, location: Location) -> str:
        """Add a user location and return their geohash quadrant."""
        quadrant = geohash.encode(location.lat, location.lon, precision=self.precision)
        if quadrant not in self.quadrant_index:
            self.quadrant_index[quadrant] = set()
        self.quadrant_index[quadrant].add(user_id)
        return quadrant

    def get_adjacent_quadrants(self, quadrant: str) -> List[str]:
        """Get list of adjacent geohash quadrants including the original quadrant."""
        if not quadrant:
            return []
        
        try:
            lat, lon = geohash.decode(quadrant)
            precision = len(quadrant)
            
            lat_offset = 0.05
            lon_offset = 0.05
            
            result = [quadrant]
            
            # Adjacent cells
            result.append(geohash.encode(lat + lat_offset, lon, precision))

            result.append(geohash.encode(lat + lat_offset, lon + lon_offset, precision))

            result.append(geohash.encode(lat, lon + lon_offset, precision))

            result.append(geohash.encode(lat - lat_offset, lon + lon_offset, precision))
            result.append(geohash.encode(lat - lat_offset, lon, precision))

            result.append(geohash.encode(lat - lat_offset, lon - lon_offset, precision))

            result.append(geohash.encode(lat, lon - lon_offset, precision))

            result.append(geohash.encode(lat + lat_offset, lon - lon_offset, precision))
            
            return list(set(result))
        except Exception as e:
            print(f"Error calculating adjacent geohashes: {e}")
            return [quadrant]

    def get_users_in_quadrant(self, quadrant: str) -> Set[str]:
        """Get all users in a quadrant."""
        return self.quadrant_index.get(quadrant, set())
    
    def remove_from_quadrant(self, quadrant: str, user_id: str) -> bool:
        """Remove a user from a geohash quadrant.
        
        Args:
            quadrant: The geohash quadrant to remove from
            user_id: The user ID to remove
            
        Returns:
            bool: True if the user was found and removed, False otherwise
        """
        if quadrant in self.quadrant_index and user_id in self.quadrant_index[quadrant]:
            self.quadrant_index[quadrant].remove(user_id)
            return True
        return False
        
    def get_geohash(self, user_id: str) -> str:
        """Get the geohash quadrant for a user."""
        for quadrant, users in self.quadrant_index.items():
            if user_id in users:
                return quadrant
        return ""

    @staticmethod
    def calculate_distance(loc1: Location, loc2: Location) -> float:
        """Calculate distance between two locations in kilometers."""
        R = 6371
        lat1, lon1 = math.radians(loc1.lat), math.radians(loc1.lon)
        lat2, lon2 = math.radians(loc2.lat), math.radians(loc2.lon)
        
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        return R * c
