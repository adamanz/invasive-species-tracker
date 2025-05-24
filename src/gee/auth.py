"""Google Earth Engine authentication module using API key."""

import os
import ee
from dotenv import load_dotenv
from loguru import logger


def initialize_earth_engine():
    """Initialize Google Earth Engine with API key authentication."""
    load_dotenv()
    
    project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
    api_key = os.getenv('GOOGLE_CLOUD_API_KEY')
    
    if not project_id or not api_key:
        raise ValueError(
            "Missing required environment variables: "
            "GOOGLE_CLOUD_PROJECT and GOOGLE_CLOUD_API_KEY must be set"
        )
    
    try:
        # Initialize with API key
        credentials = ee.ServiceAccountCredentials(None, key_data=api_key)
        ee.Initialize(
            credentials=credentials,
            project=project_id,
            opt_url='https://earthengine.googleapis.com'
        )
        logger.info(f"Successfully initialized Earth Engine for project: {project_id}")
        
        # Test the connection
        test_image = ee.Image('COPERNICUS/S2/20230101T000000_20230101T235959_T00XXX')
        test_image.getInfo()
        logger.info("Earth Engine connection test successful")
        
    except Exception as e:
        logger.error(f"Failed to initialize Earth Engine: {str(e)}")
        raise


def get_authenticated_session():
    """Get authenticated Earth Engine session, initializing if needed."""
    try:
        # Check if already initialized
        ee.Image(1).getInfo()
        logger.debug("Earth Engine already initialized")
    except:
        logger.info("Initializing Earth Engine...")
        initialize_earth_engine()
    
    return ee