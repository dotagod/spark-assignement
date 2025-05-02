import unittest
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from test_profile_service import TestProfileService
from test_geo_service import TestGeoService
from test_exclusion_service import TestExclusionService
from test_matching_service import TestMatchingService
from test_precompute_service import TestPrecomputeService
from test_match_finder_service import TestMatchFinderService

if __name__ == '__main__':
    test_loader = unittest.TestLoader()
    test_suite = test_loader.discover(os.path.dirname(__file__), pattern='test_*.py')
    
    test_runner = unittest.TextTestRunner(verbosity=2)
    result = test_runner.run(test_suite)
    
    sys.exit(not result.wasSuccessful())
