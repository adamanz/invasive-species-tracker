"""Base classes for satellite data access focused on spectral extraction."""

import ee
from typing import Dict, List, Tuple, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass
import numpy as np
from src.utils.logger import get_logger
from src.gee.auth import get_authenticated_session

logger = get_logger(__name__)


@dataclass
class SpectralSignature:
    """Container for spectral data at a specific location and time."""
    latitude: float
    longitude: float
    acquisition_date: datetime
    satellite: str
    band_names: List[str]
    band_values: Dict[str, float]
    cloud_probability: float
    metadata: Dict[str, Any]


class SatelliteDataExtractor:
    """Base class for extracting spectral data from satellite imagery."""
    
    def __init__(self):
        """Initialize the satellite data extractor."""
        self.ee = get_authenticated_session()
        logger.info("Satellite data extractor initialized")
    
    def extract_spectral_signature(
        self,
        point: Tuple[float, float],
        date: datetime,
        buffer_meters: int = 30
    ) -> Optional[SpectralSignature]:
        """Extract spectral signature at a specific point and date.
        
        Args:
            point: (longitude, latitude) tuple
            date: Target date for imagery
            buffer_meters: Buffer around point for averaging
            
        Returns:
            SpectralSignature object or None if no data available
        """
        raise NotImplementedError("Subclasses must implement this method")
    
    def extract_temporal_signatures(
        self,
        point: Tuple[float, float],
        start_date: datetime,
        end_date: datetime,
        interval_days: int = 5
    ) -> List[SpectralSignature]:
        """Extract time series of spectral signatures.
        
        Args:
            point: (longitude, latitude) tuple
            start_date: Start of time period
            end_date: End of time period
            interval_days: Days between samples
            
        Returns:
            List of SpectralSignature objects
        """
        signatures = []
        current_date = start_date
        
        while current_date <= end_date:
            signature = self.extract_spectral_signature(point, current_date)
            if signature:
                signatures.append(signature)
            current_date += timedelta(days=interval_days)
        
        return signatures
    
    def extract_spatial_context(
        self,
        center_point: Tuple[float, float],
        date: datetime,
        radius_meters: int = 100,
        sample_points: int = 8
    ) -> Dict[str, List[SpectralSignature]]:
        """Extract spectral signatures in a spatial context around a point.
        
        Args:
            center_point: (longitude, latitude) tuple
            date: Target date for imagery
            radius_meters: Radius for context extraction
            sample_points: Number of surrounding points to sample
            
        Returns:
            Dict with 'center' and 'surrounding' spectral signatures
        """
        context = {
            'center': [],
            'surrounding': []
        }
        
        # Get center point signature
        center_sig = self.extract_spectral_signature(center_point, date)
        if center_sig:
            context['center'].append(center_sig)
        
        # Get surrounding points in a circle
        lon, lat = center_point
        for i in range(sample_points):
            angle = (2 * np.pi * i) / sample_points
            # Approximate meters to degrees (rough conversion)
            offset_lon = (radius_meters / 111320.0) * np.cos(angle) / np.cos(np.radians(lat))
            offset_lat = (radius_meters / 110540.0) * np.sin(angle)
            
            surrounding_point = (lon + offset_lon, lat + offset_lat)
            sig = self.extract_spectral_signature(surrounding_point, date)
            if sig:
                context['surrounding'].append(sig)
        
        return context


class Sentinel2Extractor(SatelliteDataExtractor):
    """Extractor for Sentinel-2 satellite data."""
    
    BAND_NAMES = ['B2', 'B3', 'B4', 'B5', 'B6', 'B7', 'B8', 'B8A', 'B11', 'B12']
    COLLECTION_ID = 'COPERNICUS/S2_SR_HARMONIZED'
    
    def __init__(self):
        """Initialize Sentinel-2 extractor."""
        super().__init__()
        self.collection = self.ee.ImageCollection(self.COLLECTION_ID)
        logger.info("Sentinel-2 extractor initialized")
    
    def extract_spectral_signature(
        self,
        point: Tuple[float, float],
        date: datetime,
        buffer_meters: int = 30
    ) -> Optional[SpectralSignature]:
        """Extract Sentinel-2 spectral signature."""
        try:
            # Create geometry
            ee_point = self.ee.Geometry.Point(point)
            ee_buffer = ee_point.buffer(buffer_meters)
            
            # Date range (±5 days to find imagery)
            start = date - timedelta(days=5)
            end = date + timedelta(days=5)
            
            # Filter collection
            filtered = (self.collection
                       .filterBounds(ee_buffer)
                       .filterDate(start.isoformat(), end.isoformat())
                       .filter(self.ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 20)))
            
            # Get the first image
            image = filtered.first()
            
            # Check if image exists
            image_info = image.getInfo()
            if not image_info:
                logger.debug(f"No Sentinel-2 imagery found for {point} on {date}")
                return None
            
            # Apply cloud masking
            image = self._mask_clouds(image)
            
            # Extract band values
            band_values = {}
            for band in self.BAND_NAMES:
                value = image.select(band).reduceRegion(
                    reducer=self.ee.Reducer.mean(),
                    geometry=ee_buffer,
                    scale=10,
                    maxPixels=1000
                ).getInfo()
                band_values[band] = value.get(band, None)
            
            # Get metadata
            properties = image.getInfo()['properties']
            
            # Extract date from system properties
            timestamp = properties.get('system:time_start', 0)
            acquisition_date = datetime.fromtimestamp(timestamp / 1000) if timestamp else date
            
            return SpectralSignature(
                latitude=point[1],
                longitude=point[0],
                acquisition_date=acquisition_date,
                satellite='Sentinel-2',
                band_names=self.BAND_NAMES,
                band_values=band_values,
                cloud_probability=properties.get('CLOUDY_PIXEL_PERCENTAGE', 0),
                metadata={
                    'product_id': properties.get('PRODUCT_ID', 'N/A'),
                    'spacecraft': properties.get('SPACECRAFT_NAME', 'Sentinel-2'),
                    'processing_baseline': properties.get('PROCESSING_BASELINE', 'N/A'),
                    'system_index': properties.get('system:index', 'N/A')
                }
            )
            
        except Exception as e:
            logger.error(f"Error extracting Sentinel-2 signature: {str(e)}")
            return None
    
    def _mask_clouds(self, image):
        """Apply cloud masking to Sentinel-2 image."""
        qa = image.select('QA60')
        
        # Bits 10 and 11 are clouds and cirrus
        cloud_bit_mask = 1 << 10
        cirrus_bit_mask = 1 << 11
        
        # Both flags should be set to zero, indicating clear conditions
        mask = (qa.bitwiseAnd(cloud_bit_mask).eq(0)
               .And(qa.bitwiseAnd(cirrus_bit_mask).eq(0)))
        
        # Scale the bands
        return image.updateMask(mask).divide(10000)


class LandsatExtractor(SatelliteDataExtractor):
    """Extractor for Landsat 8/9 satellite data."""
    
    BAND_NAMES = ['B2', 'B3', 'B4', 'B5', 'B6', 'B7']
    COLLECTION_IDS = [
        'LANDSAT/LC08/C02/T1_L2',
        'LANDSAT/LC09/C02/T1_L2'
    ]
    
    def __init__(self):
        """Initialize Landsat extractor."""
        super().__init__()
        # Merge Landsat 8 and 9 collections
        self.collection = self.ee.ImageCollection(self.COLLECTION_IDS[0]).merge(
            self.ee.ImageCollection(self.COLLECTION_IDS[1])
        )
        logger.info("Landsat 8/9 extractor initialized")
    
    def extract_spectral_signature(
        self,
        point: Tuple[float, float],
        date: datetime,
        buffer_meters: int = 30
    ) -> Optional[SpectralSignature]:
        """Extract Landsat spectral signature."""
        try:
            # Create geometry
            ee_point = self.ee.Geometry.Point(point)
            ee_buffer = ee_point.buffer(buffer_meters)
            
            # Date range (±8 days for Landsat revisit)
            start = date - timedelta(days=8)
            end = date + timedelta(days=8)
            
            # Filter collection
            filtered = (self.collection
                       .filterBounds(ee_buffer)
                       .filterDate(start.isoformat(), end.isoformat())
                       .filter(self.ee.Filter.lt('CLOUD_COVER', 20)))
            
            # Get the first image
            image = filtered.first()
            
            if not image:
                logger.debug(f"No Landsat imagery found for {point} on {date}")
                return None
            
            # Apply scaling and cloud masking
            image = self._process_landsat(image)
            
            # Extract band values
            band_values = {}
            for band in self.BAND_NAMES:
                value = image.select(f'SR_{band}').reduceRegion(
                    reducer=self.ee.Reducer.mean(),
                    geometry=ee_buffer,
                    scale=30,
                    maxPixels=1000
                ).getInfo()
                band_values[band] = value.get(f'SR_{band}', None)
            
            # Get metadata
            properties = image.getInfo()['properties']
            
            return SpectralSignature(
                latitude=point[1],
                longitude=point[0],
                acquisition_date=datetime.fromisoformat(
                    properties['DATE_ACQUIRED']
                ),
                satellite=f"Landsat-{properties.get('SPACECRAFT_ID', '').split('_')[1]}",
                band_names=self.BAND_NAMES,
                band_values=band_values,
                cloud_probability=properties.get('CLOUD_COVER', 0),
                metadata={
                    'scene_id': properties.get('LANDSAT_SCENE_ID'),
                    'wrs_path': properties.get('WRS_PATH'),
                    'wrs_row': properties.get('WRS_ROW')
                }
            )
            
        except Exception as e:
            logger.error(f"Error extracting Landsat signature: {str(e)}")
            return None
    
    def _process_landsat(self, image):
        """Apply scaling factors and cloud masking."""
        # Apply scaling factors
        optical_bands = image.select('SR_B.*').multiply(0.0000275).add(-0.2)
        
        # Cloud masking using QA_PIXEL
        qa_pixel = image.select('QA_PIXEL')
        cloud_bit = 1 << 3
        cloud_shadow_bit = 1 << 4
        
        mask = (qa_pixel.bitwiseAnd(cloud_bit).eq(0)
               .And(qa_pixel.bitwiseAnd(cloud_shadow_bit).eq(0)))
        
        return optical_bands.updateMask(mask)