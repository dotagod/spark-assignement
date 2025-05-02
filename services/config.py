"""Service configuration and initialization."""

from services.profile_service import ProfileService
from services.geo_service import GeoService
from services.exclusion_service import ExclusionService
from services.matching_service import MatchingService
from services.precompute_service import PrecomputeService
from services.match_finder_service import MatchFinderService
from services.service_locator import ServiceLocator
from services.interfaces import (
    IProfileService, 
    IGeoService, 
    IExclusionService,
    IMatchingService,
    IPrecomputeService,
    IMatchFinderService
)

def configure_services():
    """Initialize and register all services with the service locator."""
    # Initialize services in dependency order
    profile_service = ProfileService()
    geo_service = GeoService()
    exclusion_service = ExclusionService()
    
    # Register basic services
    ServiceLocator.register(IProfileService, profile_service)
    ServiceLocator.register(IGeoService, geo_service)
    ServiceLocator.register(IExclusionService, exclusion_service)
    
    # Initialize and register services with dependencies
    matching_service = MatchingService(profile_service, geo_service)
    ServiceLocator.register(IMatchingService, matching_service)
    
    precompute_service = PrecomputeService(profile_service, geo_service, matching_service)
    ServiceLocator.register(IPrecomputeService, precompute_service)
    
    match_finder_service = MatchFinderService(
        profile_service, 
        geo_service, 
        matching_service, 
        precompute_service, 
        exclusion_service
    )
    ServiceLocator.register(IMatchFinderService, match_finder_service)
    
    return {
        'profile_service': profile_service,
        'geo_service': geo_service,
        'exclusion_service': exclusion_service,
        'matching_service': matching_service,
        'precompute_service': precompute_service,
        'match_finder_service': match_finder_service
    }
