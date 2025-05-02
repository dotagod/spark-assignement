from typing import Dict, Set, Tuple, List
import math
import sys
from models import Location

# Make sure geohash is imported correctly
try:
    import geohash
except ImportError:
    print("Error importing geohash module. Make sure it's installed.")
    print("Try running: pip install python-geohash")
    sys.exit(1)

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
            # Decode the geohash to get lat/lon
            lat, lon = geohash.decode(quadrant)
            precision = len(quadrant)
            
            # Define larger offsets based on precision to ensure different geohashes
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
            # Fallback to just returning the original geohash
            return [quadrant]

    def get_users_in_quadrant(self, quadrant: str) -> Set[str]:
        """Get all users in a quadrant."""
        return self.quadrant_index.get(quadrant, set())
        
    def get_geohash(self, user_id: str) -> str:
        """Get the geohash quadrant for a user."""
        for quadrant, users in self.quadrant_index.items():
            if user_id in users:
                return quadrant
        return ""  # Return empty string if user not found

    @staticmethod
    def calculate_distance(loc1: Location, loc2: Location) -> float:
        """Calculate distance between two locations in kilometers."""
        R = 6371  # Earth's radius in kilometers
        lat1, lon1 = math.radians(loc1.lat), math.radians(loc1.lon)
        lat2, lon2 = math.radians(loc2.lat), math.radians(loc2.lon)
        
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        return R * c
