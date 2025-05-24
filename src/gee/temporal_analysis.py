"""Temporal analysis and change detection for invasive species monitoring."""

import ee
from typing import List, Dict, Tuple, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass
import pandas as pd
from src.gee.satellite_data import SpectralSignature, SatelliteDataExtractor
from src.utils.logger import get_logger
from src.gee.auth import get_authenticated_session

logger = get_logger(__name__)


@dataclass
class TemporalComposite:
    """Container for temporal composite data."""
    start_date: datetime
    end_date: datetime
    location: Tuple[float, float]
    num_images: int
    median_values: Dict[str, float]
    percentile_10: Dict[str, float]
    percentile_90: Dict[str, float]
    std_dev: Dict[str, float]
    metadata: Dict[str, Any]


class TemporalAnalyzer:
    """Analyzes temporal patterns in satellite imagery for change detection."""
    
    def __init__(self, data_extractor: SatelliteDataExtractor):
        """Initialize temporal analyzer with a data extractor."""
        self.ee = get_authenticated_session()
        self.extractor = data_extractor
        logger.info("Temporal analyzer initialized")
    
    def create_baseline_composite(
        self,
        location: Tuple[float, float],
        start_date: datetime,
        end_date: datetime,
        buffer_meters: int = 100
    ) -> Optional[TemporalComposite]:
        """Create a baseline composite for a location over a time period.
        
        Args:
            location: (longitude, latitude) tuple
            start_date: Start of baseline period
            end_date: End of baseline period
            buffer_meters: Buffer around point
            
        Returns:
            TemporalComposite with statistical summary
        """
        try:
            # Extract all signatures in the period
            signatures = self.extractor.extract_temporal_signatures(
                location, start_date, end_date, interval_days=5
            )
            
            if len(signatures) < 3:
                logger.warning(f"Insufficient data for baseline: only {len(signatures)} images")
                return None
            
            # Convert to pandas for easier statistics
            band_data = {}
            for band in signatures[0].band_names:
                values = [sig.band_values.get(band) for sig in signatures 
                         if sig.band_values.get(band) is not None]
                if values:
                    band_data[band] = values
            
            df = pd.DataFrame(band_data)
            
            # Calculate statistics
            composite = TemporalComposite(
                start_date=start_date,
                end_date=end_date,
                location=location,
                num_images=len(signatures),
                median_values=df.median().to_dict(),
                percentile_10=df.quantile(0.1).to_dict(),
                percentile_90=df.quantile(0.9).to_dict(),
                std_dev=df.std().to_dict(),
                metadata={
                    'dates': [sig.acquisition_date.isoformat() for sig in signatures],
                    'cloud_coverage': [sig.cloud_probability for sig in signatures]
                }
            )
            
            logger.info(f"Created baseline composite with {len(signatures)} images")
            return composite
            
        except Exception as e:
            logger.error(f"Error creating baseline composite: {str(e)}")
            return None
    
    def detect_changes(
        self,
        baseline: TemporalComposite,
        current_signature: SpectralSignature,
        threshold_std: float = 2.0
    ) -> Dict[str, Any]:
        """Detect changes between baseline and current observation.
        
        Args:
            baseline: Baseline temporal composite
            current_signature: Current spectral signature
            threshold_std: Number of standard deviations for anomaly detection
            
        Returns:
            Dictionary with change detection results
        """
        changes = {
            'location': baseline.location,
            'baseline_period': f"{baseline.start_date.date()} to {baseline.end_date.date()}",
            'current_date': current_signature.acquisition_date.date(),
            'anomalies': [],
            'change_magnitude': {},
            'bands_changed': []
        }
        
        # Check each band for changes
        for band in current_signature.band_names:
            current_value = current_signature.band_values.get(band)
            baseline_median = baseline.median_values.get(band)
            baseline_std = baseline.std_dev.get(band)
            
            if all(v is not None for v in [current_value, baseline_median, baseline_std]):
                # Calculate z-score
                if baseline_std > 0:
                    z_score = abs(current_value - baseline_median) / baseline_std
                    
                    # Check if change exceeds threshold
                    if z_score > threshold_std:
                        changes['bands_changed'].append(band)
                        changes['anomalies'].append({
                            'band': band,
                            'z_score': round(z_score, 2),
                            'baseline_median': round(baseline_median, 4),
                            'current_value': round(current_value, 4),
                            'change_percent': round(
                                ((current_value - baseline_median) / baseline_median) * 100, 1
                            )
                        })
                
                # Calculate overall change magnitude
                changes['change_magnitude'][band] = round(
                    current_value - baseline_median, 4
                )
        
        # Summary statistics
        changes['num_bands_changed'] = len(changes['bands_changed'])
        changes['significant_change'] = len(changes['anomalies']) > 0
        
        return changes
    
    def analyze_phenology(
        self,
        location: Tuple[float, float],
        year: int,
        buffer_meters: int = 100
    ) -> Dict[str, Any]:
        """Analyze annual phenological patterns at a location.
        
        Args:
            location: (longitude, latitude) tuple
            year: Year to analyze
            buffer_meters: Buffer around point
            
        Returns:
            Dictionary with phenological analysis
        """
        # Define seasons
        seasons = {
            'spring': (datetime(year, 3, 1), datetime(year, 5, 31)),
            'summer': (datetime(year, 6, 1), datetime(year, 8, 31)),
            'fall': (datetime(year, 9, 1), datetime(year, 11, 30)),
            'winter': (datetime(year-1, 12, 1), datetime(year, 2, 28))
        }
        
        phenology = {
            'location': location,
            'year': year,
            'seasonal_patterns': {}
        }
        
        for season, (start, end) in seasons.items():
            composite = self.create_baseline_composite(
                location, start, end, buffer_meters
            )
            
            if composite:
                # Calculate vegetation activity indicators
                b8 = composite.median_values.get('B8', 0)
                b4 = composite.median_values.get('B4', 1)
                ndvi = (b8 - b4) / (b8 + b4) if (b8 + b4) > 0 else 0
                
                phenology['seasonal_patterns'][season] = {
                    'ndvi': round(ndvi, 3),
                    'nir_reflectance': round(b8, 4),
                    'red_reflectance': round(b4, 4),
                    'num_observations': composite.num_images
                }
        
        # Identify peak growing season
        if phenology['seasonal_patterns']:
            peak_season = max(
                phenology['seasonal_patterns'].items(),
                key=lambda x: x[1].get('ndvi', 0)
            )[0]
            phenology['peak_growing_season'] = peak_season
        
        return phenology
    
    def detect_rapid_changes(
        self,
        location: Tuple[float, float],
        reference_date: datetime,
        lookback_days: int = 30,
        lookahead_days: int = 30,
        interval_days: int = 5
    ) -> Dict[str, Any]:
        """Detect rapid vegetation changes around a reference date.
        
        Args:
            location: (longitude, latitude) tuple
            reference_date: Central date for analysis
            lookback_days: Days to look back
            lookahead_days: Days to look ahead
            interval_days: Sampling interval
            
        Returns:
            Dictionary with rapid change analysis
        """
        # Define time windows
        before_start = reference_date - timedelta(days=lookback_days)
        after_end = reference_date + timedelta(days=lookahead_days)
        
        # Get signatures before and after
        before_sigs = self.extractor.extract_temporal_signatures(
            location, before_start, reference_date, interval_days
        )
        after_sigs = self.extractor.extract_temporal_signatures(
            location, reference_date, after_end, interval_days
        )
        
        if len(before_sigs) < 2 or len(after_sigs) < 2:
            return {
                'error': 'Insufficient temporal data',
                'before_count': len(before_sigs),
                'after_count': len(after_sigs)
            }
        
        # Calculate statistics for before and after periods
        rapid_changes = {
            'location': location,
            'reference_date': reference_date.isoformat(),
            'before_period': f"{before_start.date()} to {reference_date.date()}",
            'after_period': f"{reference_date.date()} to {after_end.date()}",
            'changes_detected': []
        }
        
        # Compare band statistics
        for band in before_sigs[0].band_names:
            before_values = [s.band_values.get(band) for s in before_sigs 
                           if s.band_values.get(band) is not None]
            after_values = [s.band_values.get(band) for s in after_sigs 
                          if s.band_values.get(band) is not None]
            
            if before_values and after_values:
                before_mean = sum(before_values) / len(before_values)
                after_mean = sum(after_values) / len(after_values)
                
                change_percent = ((after_mean - before_mean) / before_mean) * 100
                
                if abs(change_percent) > 20:  # 20% change threshold
                    rapid_changes['changes_detected'].append({
                        'band': band,
                        'before_mean': round(before_mean, 4),
                        'after_mean': round(after_mean, 4),
                        'change_percent': round(change_percent, 1),
                        'direction': 'increase' if change_percent > 0 else 'decrease'
                    })
        
        rapid_changes['rapid_change_detected'] = len(rapid_changes['changes_detected']) > 0
        
        return rapid_changes


class InvasionTracker:
    """Tracks invasive species spread over time."""
    
    def __init__(self, temporal_analyzer: TemporalAnalyzer):
        """Initialize invasion tracker."""
        self.analyzer = temporal_analyzer
        logger.info("Invasion tracker initialized")
    
    def track_invasion_front(
        self,
        center_point: Tuple[float, float],
        start_date: datetime,
        end_date: datetime,
        radius_meters: int = 1000,
        sample_points: int = 8
    ) -> Dict[str, Any]:
        """Track the invasion front movement over time.
        
        Args:
            center_point: Known invasion center (lon, lat)
            start_date: Start of tracking period
            end_date: End of tracking period
            radius_meters: Radius to monitor
            sample_points: Number of directions to sample
            
        Returns:
            Dictionary with invasion front analysis
        """
        import numpy as np
        
        tracking_results = {
            'center_point': center_point,
            'period': f"{start_date.date()} to {end_date.date()}",
            'radius_meters': radius_meters,
            'directional_spread': {}
        }
        
        # Sample points in different directions
        lon, lat = center_point
        directions = ['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW']
        
        for i, direction in enumerate(directions[:sample_points]):
            angle = (2 * np.pi * i) / sample_points
            
            # Calculate offset (approximate meters to degrees)
            offset_lon = (radius_meters / 111320.0) * np.cos(angle) / np.cos(np.radians(lat))
            offset_lat = (radius_meters / 110540.0) * np.sin(angle)
            
            sample_point = (lon + offset_lon, lat + offset_lat)
            
            # Analyze changes at this point
            baseline = self.analyzer.create_baseline_composite(
                sample_point,
                start_date,
                start_date + timedelta(days=30)
            )
            
            current = self.analyzer.create_baseline_composite(
                sample_point,
                end_date - timedelta(days=30),
                end_date
            )
            
            if baseline and current:
                # Compare vegetation activity
                baseline_nir = baseline.median_values.get('B8', 0)
                current_nir = current.median_values.get('B8', 0)
                
                change = ((current_nir - baseline_nir) / baseline_nir * 100) if baseline_nir > 0 else 0
                
                tracking_results['directional_spread'][direction] = {
                    'sample_point': sample_point,
                    'vegetation_change_percent': round(change, 1),
                    'invasion_likely': change > 30  # 30% increase threshold
                }
        
        # Determine primary spread direction
        invaded_directions = [
            d for d, data in tracking_results['directional_spread'].items()
            if data['invasion_likely']
        ]
        tracking_results['primary_spread_directions'] = invaded_directions
        tracking_results['spread_detected'] = len(invaded_directions) > 0
        
        return tracking_results