"""Google Earth Engine authentication module using API key."""

import os
import ee
from dotenv import load_dotenv
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent))
from src.utils.logger import get_logger

logger = get_logger(__name__)


def initialize_earth_engine():
    """Initialize Google Earth Engine with OAuth authentication."""
    load_dotenv()
    
    project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
    
    if not project_id:
        raise ValueError(
            "Missing required environment variable: "
            "GOOGLE_CLOUD_PROJECT must be set"
        )
    
    logger.info(f"Using project ID from .env: {project_id}")
    
    try:
        # For API key authentication, we need to use OAuth flow
        # The API key is used for other Google Cloud services
        # Don't call Authenticate if already authenticated
        try:
            ee.Initialize(project=project_id)
        except:
            ee.Authenticate()
            ee.Initialize(project=project_id)
        
        logger.info(f"Successfully initialized Earth Engine for project: {project_id}")
        
        # Test the connection with a simple operation
        test = ee.Number(1).add(1).getInfo()
        if test == 2:
            logger.info("Earth Engine connection test successful")
        
        # Test access to a public dataset
        test_collection = ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED').limit(1)
        size = test_collection.size().getInfo()
        logger.info(f"Successfully accessed Sentinel-2 collection, found {size} image(s)")
        
    except Exception as e:
        logger.error(f"Failed to initialize Earth Engine: {str(e)}")
        raise


def get_authenticated_session():
    """Get authenticated Earth Engine session, initializing if needed."""
    try:
        # Check if already initialized
        ee.Number(1).getInfo()
        logger.debug("Earth Engine already initialized")
    except:
        logger.info("Initializing Earth Engine...")
        initialize_earth_engine()
    
    return ee


if __name__ == "__main__":
    """Test Earth Engine connection when module is run directly."""
    print("Testing Google Earth Engine connection...")
    try:
        initialize_earth_engine()
        print("\n✅ Earth Engine connection successful!")
        
        # Additional test: Get info about a specific location
        point = ee.Geometry.Point([-122.4194, 37.7749])  # San Francisco
        elevation = ee.Image('USGS/SRTMGL1_003').sample(point, 30).first().get('elevation').getInfo()
        print(f"✅ Test query successful - Elevation at San Francisco: {elevation}m")
        
    except Exception as e:
        print(f"\n❌ Earth Engine connection failed: {str(e)}")
        print("\nPlease ensure:")
        print("1. You have authenticated with 'earthengine authenticate' command")
        print("2. Your GOOGLE_CLOUD_PROJECT is set correctly in .env")
        print("3. Earth Engine API is enabled in your Google Cloud project")
        sys.exit(1)