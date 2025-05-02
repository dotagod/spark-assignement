from typing import Dict, List, Set
import math
import geohash
from models import Location
from services.interfaces import IGeoService

class GeoService(IGeoService):
    """Service for managing geospatial indexing."""
    
    def __init__(self, precision: int = 5):
        self.precision = precision
        self.quadrant_index: Dict[str, Set[str]] = {}
        
    def get_geo_index(self):
        """Get the geospatial index.
        
        Returns:
            The GeoIndex instance - this is now the service itself for backward compatibility
        """
        return self
        
    def index_profile(self, profile_id: str, location: Location) -> str:
        """Add a user location to the geospatial index.
        
        Args:
            profile_id: ID of the profile to index
            location: Location to index
            
        Returns:
            The geohash of the indexed location
        """
        quadrant = geohash.encode(location.lat, location.lon, precision=self.precision)
        if quadrant not in self.quadrant_index:
            self.quadrant_index[quadrant] = set()
        self.quadrant_index[quadrant].add(profile_id)
        return quadrant
        
    def remove_from_index(self, quadrant: str, profile_id: str) -> bool:
        """Remove a user from a geohash quadrant.
        
        Args:
            quadrant: Geohash quadrant to remove from
            profile_id: ID of the profile to remove
            
        Returns:
            True if the user was removed, False otherwise
        """
        if quadrant in self.quadrant_index and profile_id in self.quadrant_index[quadrant]:
            self.quadrant_index[quadrant].remove(profile_id)
            return True
        return False
        
    def get_users_in_quadrant(self, quadrant: str) -> Set[str]:
        """Get all users in a geohash quadrant.
        
        Args:
            quadrant: Geohash quadrant to query
            
        Returns:
            Set of user IDs in the quadrant
        """
        return self.quadrant_index.get(quadrant, set())
        
    def get_adjacent_quadrants(self, quadrant: str) -> List[str]:
        """Get a list of adjacent geohash quadrants.
        
        Args:
            quadrant: The geohash to find adjacents for
            
        Returns:
            List of geohash quadrants, including the original
        """
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
        
    def get_profile_geohash(self, profile_id: str) -> str:
        """Get the geohash for a profile.
        
        Args:
            profile_id: ID of the profile
            
        Returns:
            The geohash string or empty string if not found
        """
        for quadrant, users in self.quadrant_index.items():
            if profile_id in users:
                return quadrant
        return ""
        
    @staticmethod
    def calculate_distance(loc1: Location, loc2: Location) -> float:
        """Calculate distance between two locations in kilometers.
        
        Args:
            loc1: First location
            loc2: Second location
            
        Returns:
            Distance in kilometers
        """
        R = 6371
        lat1, lon1 = math.radians(loc1.lat), math.radians(loc1.lon)
        lat2, lon2 = math.radians(loc2.lat), math.radians(loc2.lon)
        
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        return R * c
