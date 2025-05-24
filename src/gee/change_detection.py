"""Advanced change detection algorithms for invasive species monitoring."""

import ee
import numpy as np
from typing import List, Dict, Tuple, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass
from src.gee.satellite_data import SpectralSignature, Sentinel2Extractor
from src.gee.temporal_analysis import TemporalAnalyzer, TemporalComposite
from src.utils.logger import get_logger
from src.gee.auth import get_authenticated_session

logger = get_logger(__name__)


@dataclass
class ChangeEvent:
    """Container for detected change events."""
    location: Tuple[float, float]
    detection_date: datetime
    change_type: str  # 'sudden', 'gradual', 'seasonal'
    magnitude: float  # 0-1 normalized change magnitude
    confidence: float  # 0-1 confidence score
    affected_bands: List[str]
    metadata: Dict[str, Any]


class SpectralChangeDetector:
    """Detects spectral changes indicative of invasive species."""
    
    def __init__(self, extractor: Sentinel2Extractor):
        """Initialize change detector."""
        self.ee = get_authenticated_session()
        self.extractor = extractor
        self.temporal_analyzer = TemporalAnalyzer(extractor)
        logger.info("Spectral change detector initialized")
    
    def detect_spectral_anomalies(
        self,
        location: Tuple[float, float],
        reference_date: datetime,
        baseline_days: int = 90,
        sensitivity: float = 2.0
    ) -> List[ChangeEvent]:
        """Detect spectral anomalies that may indicate invasive species.
        
        Args:
            location: (longitude, latitude) tuple
            reference_date: Date to check for anomalies
            baseline_days: Days of baseline data to use
            sensitivity: Standard deviations for anomaly threshold
            
        Returns:
            List of detected change events
        """
        events = []
        
        # Create baseline
        baseline_start = reference_date - timedelta(days=baseline_days)
        baseline = self.temporal_analyzer.create_baseline_composite(
            location, baseline_start, reference_date
        )
        
        if not baseline:
            logger.warning("Could not create baseline for anomaly detection")
            return events
        
        # Get current observation
        current = self.extractor.extract_spectral_signature(location, reference_date)
        
        if not current:
            return events
        
        # Detect changes
        changes = self.temporal_analyzer.detect_changes(baseline, current, sensitivity)
        
        if changes['significant_change']:
            # Calculate overall magnitude
            magnitudes = []
            for anomaly in changes['anomalies']:
                z_score = anomaly['z_score']
                magnitudes.append(min(z_score / 5.0, 1.0))  # Normalize to 0-1
            
            event = ChangeEvent(
                location=location,
                detection_date=current.acquisition_date,
                change_type='sudden',
                magnitude=np.mean(magnitudes),
                confidence=min(0.2 * len(changes['anomalies']), 1.0),
                affected_bands=changes['bands_changed'],
                metadata={
                    'baseline_period': changes['baseline_period'],
                    'anomalies': changes['anomalies']
                }
            )
            events.append(event)
            logger.info(f"Detected spectral anomaly at {location} on {reference_date}")
        
        return events
    
    def track_gradual_changes(
        self,
        location: Tuple[float, float],
        start_date: datetime,
        end_date: datetime,
        window_days: int = 30,
        step_days: int = 15
    ) -> List[ChangeEvent]:
        """Track gradual vegetation changes over time.
        
        Args:
            location: (longitude, latitude) tuple
            start_date: Start of monitoring period
            end_date: End of monitoring period
            window_days: Size of moving window
            step_days: Step size for moving window
            
        Returns:
            List of gradual change events
        """
        events = []
        current_date = start_date + timedelta(days=window_days)
        
        # Store previous metrics for trend analysis
        previous_metrics = None
        trend_buffer = []
        
        while current_date <= end_date:
            # Create composite for current window
            window_start = current_date - timedelta(days=window_days)
            composite = self.temporal_analyzer.create_baseline_composite(
                location, window_start, current_date
            )
            
            if composite:
                # Calculate vegetation metrics
                b8 = composite.median_values.get('B8', 0)
                b4 = composite.median_values.get('B4', 1)
                ndvi = (b8 - b4) / (b8 + b4) if (b8 + b4) > 0 else 0
                
                current_metrics = {
                    'date': current_date,
                    'ndvi': ndvi,
                    'nir': b8,
                    'red': b4
                }
                
                # Add to trend buffer
                trend_buffer.append(current_metrics)
                if len(trend_buffer) > 5:
                    trend_buffer.pop(0)
                
                # Analyze trend if we have enough data
                if len(trend_buffer) >= 3:
                    ndvi_values = [m['ndvi'] for m in trend_buffer]
                    
                    # Calculate trend
                    x = np.arange(len(ndvi_values))
                    slope, _ = np.polyfit(x, ndvi_values, 1)
                    
                    # Significant positive trend might indicate invasion
                    if slope > 0.05:  # Threshold for significant increase
                        event = ChangeEvent(
                            location=location,
                            detection_date=current_date,
                            change_type='gradual',
                            magnitude=min(abs(slope) * 10, 1.0),
                            confidence=0.6,
                            affected_bands=['B8', 'B4'],
                            metadata={
                                'trend_slope': float(slope),
                                'ndvi_values': ndvi_values,
                                'window_days': window_days
                            }
                        )
                        events.append(event)
                        logger.info(f"Detected gradual change at {location}")
                
                previous_metrics = current_metrics
            
            current_date += timedelta(days=step_days)
        
        return events
    
    def detect_phenological_anomalies(
        self,
        location: Tuple[float, float],
        year: int,
        historical_years: int = 3
    ) -> List[ChangeEvent]:
        """Detect anomalies in seasonal patterns.
        
        Args:
            location: (longitude, latitude) tuple
            year: Year to analyze
            historical_years: Number of historical years for comparison
            
        Returns:
            List of phenological anomaly events
        """
        events = []
        
        # Get current year phenology
        current_phenology = self.temporal_analyzer.analyze_phenology(location, year)
        
        # Get historical phenology
        historical_patterns = []
        for hist_year in range(year - historical_years, year):
            hist_phenology = self.temporal_analyzer.analyze_phenology(location, hist_year)
            if hist_phenology.get('seasonal_patterns'):
                historical_patterns.append(hist_phenology)
        
        if not historical_patterns:
            logger.warning("Insufficient historical data for phenological analysis")
            return events
        
        # Compare current to historical
        for season in ['spring', 'summer', 'fall', 'winter']:
            current_ndvi = current_phenology.get('seasonal_patterns', {}).get(season, {}).get('ndvi', 0)
            
            # Calculate historical average
            hist_ndvis = [
                hp.get('seasonal_patterns', {}).get(season, {}).get('ndvi', 0)
                for hp in historical_patterns
            ]
            hist_mean = np.mean(hist_ndvis) if hist_ndvis else 0
            hist_std = np.std(hist_ndvis) if len(hist_ndvis) > 1 else 0.1
            
            # Check for anomaly
            if hist_std > 0:
                z_score = abs(current_ndvi - hist_mean) / hist_std
                
                if z_score > 2.0:  # Significant anomaly
                    event = ChangeEvent(
                        location=location,
                        detection_date=datetime(year, 6, 1),  # Mid-year
                        change_type='seasonal',
                        magnitude=min(z_score / 4.0, 1.0),
                        confidence=0.7,
                        affected_bands=['B8', 'B4'],
                        metadata={
                            'season': season,
                            'current_ndvi': current_ndvi,
                            'historical_mean': hist_mean,
                            'z_score': z_score
                        }
                    )
                    events.append(event)
                    logger.info(f"Detected phenological anomaly in {season} at {location}")
        
        return events


class MultiScaleChangeDetector:
    """Detects changes at multiple spatial and temporal scales."""
    
    def __init__(self, extractor: Sentinel2Extractor):
        """Initialize multi-scale detector."""
        self.extractor = extractor
        self.spectral_detector = SpectralChangeDetector(extractor)
        logger.info("Multi-scale change detector initialized")
    
    def detect_invasion_hotspots(
        self,
        region_bounds: List[Tuple[float, float]],
        reference_date: datetime,
        grid_size_meters: int = 500
    ) -> Dict[str, Any]:
        """Detect invasion hotspots across a region.
        
        Args:
            region_bounds: [(min_lon, min_lat), (max_lon, max_lat)]
            reference_date: Date for detection
            grid_size_meters: Grid cell size
            
        Returns:
            Dictionary with hotspot analysis
        """
        min_lon, min_lat = region_bounds[0]
        max_lon, max_lat = region_bounds[1]
        
        # Create grid
        grid_points = []
        lat_step = grid_size_meters / 110540.0  # Approximate meters to degrees
        lon_step = grid_size_meters / (111320.0 * np.cos(np.radians((min_lat + max_lat) / 2)))
        
        current_lat = min_lat
        while current_lat <= max_lat:
            current_lon = min_lon
            while current_lon <= max_lon:
                grid_points.append((current_lon, current_lat))
                current_lon += lon_step
            current_lat += lat_step
        
        logger.info(f"Analyzing {len(grid_points)} grid cells")
        
        # Detect changes at each grid point
        hotspots = []
        for point in grid_points:
            events = self.spectral_detector.detect_spectral_anomalies(
                point, reference_date, baseline_days=60, sensitivity=1.5
            )
            
            if events:
                hotspots.append({
                    'location': point,
                    'change_magnitude': events[0].magnitude,
                    'confidence': events[0].confidence
                })
        
        # Cluster nearby hotspots
        clustered_hotspots = self._cluster_hotspots(hotspots, cluster_distance=grid_size_meters * 2)
        
        return {
            'analysis_date': reference_date.isoformat(),
            'region_bounds': region_bounds,
            'grid_size_meters': grid_size_meters,
            'total_cells_analyzed': len(grid_points),
            'hotspots_detected': len(hotspots),
            'hotspot_clusters': clustered_hotspots
        }
    
    def _cluster_hotspots(
        self,
        hotspots: List[Dict[str, Any]],
        cluster_distance: float
    ) -> List[Dict[str, Any]]:
        """Cluster nearby hotspots."""
        if not hotspots:
            return []
        
        # Simple distance-based clustering
        clusters = []
        used = set()
        
        for i, hotspot in enumerate(hotspots):
            if i in used:
                continue
            
            cluster = {
                'center': hotspot['location'],
                'members': [hotspot],
                'total_magnitude': hotspot['change_magnitude']
            }
            used.add(i)
            
            # Find nearby hotspots
            for j, other in enumerate(hotspots):
                if j in used:
                    continue
                
                # Calculate distance
                dist = self._haversine_distance(
                    hotspot['location'],
                    other['location']
                )
                
                if dist <= cluster_distance:
                    cluster['members'].append(other)
                    cluster['total_magnitude'] += other['change_magnitude']
                    used.add(j)
            
            cluster['average_magnitude'] = cluster['total_magnitude'] / len(cluster['members'])
            clusters.append(cluster)
        
        return sorted(clusters, key=lambda x: x['average_magnitude'], reverse=True)
    
    def _haversine_distance(self, point1: Tuple[float, float], point2: Tuple[float, float]) -> float:
        """Calculate distance between two points in meters."""
        lon1, lat1 = point1
        lon2, lat2 = point2
        
        R = 6371000  # Earth radius in meters
        
        lat1_rad = np.radians(lat1)
        lat2_rad = np.radians(lat2)
        delta_lat = np.radians(lat2 - lat1)
        delta_lon = np.radians(lon2 - lon1)
        
        a = np.sin(delta_lat/2)**2 + np.cos(lat1_rad) * np.cos(lat2_rad) * np.sin(delta_lon/2)**2
        c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1-a))
        
        return R * c


class EarlyWarningSystem:
    """Early warning system for invasive species detection."""
    
    def __init__(self, extractor: Sentinel2Extractor):
        """Initialize early warning system."""
        self.extractor = extractor
        self.change_detector = SpectralChangeDetector(extractor)
        self.multi_scale = MultiScaleChangeDetector(extractor)
        logger.info("Early warning system initialized")
    
    def monitor_location(
        self,
        location: Tuple[float, float],
        current_date: datetime,
        alert_thresholds: Dict[str, float] = None
    ) -> Dict[str, Any]:
        """Monitor a location for invasion indicators.
        
        Args:
            location: (longitude, latitude) tuple
            current_date: Current monitoring date
            alert_thresholds: Custom alert thresholds
            
        Returns:
            Monitoring report with alert levels
        """
        if not alert_thresholds:
            alert_thresholds = {
                'sudden_change': 0.7,
                'gradual_change': 0.6,
                'phenological_anomaly': 0.8
            }
        
        report = {
            'location': location,
            'monitoring_date': current_date.isoformat(),
            'alerts': [],
            'risk_level': 'low'
        }
        
        # Check for sudden changes
        sudden_events = self.change_detector.detect_spectral_anomalies(
            location, current_date, baseline_days=30
        )
        
        for event in sudden_events:
            if event.magnitude > alert_thresholds['sudden_change']:
                report['alerts'].append({
                    'type': 'sudden_change',
                    'severity': 'high',
                    'magnitude': event.magnitude,
                    'date': event.detection_date.isoformat(),
                    'details': event.metadata
                })
        
        # Check for gradual changes
        gradual_events = self.change_detector.track_gradual_changes(
            location,
            current_date - timedelta(days=90),
            current_date
        )
        
        for event in gradual_events:
            if event.magnitude > alert_thresholds['gradual_change']:
                report['alerts'].append({
                    'type': 'gradual_change',
                    'severity': 'medium',
                    'magnitude': event.magnitude,
                    'date': event.detection_date.isoformat(),
                    'details': event.metadata
                })
        
        # Determine overall risk level
        if any(alert['severity'] == 'high' for alert in report['alerts']):
            report['risk_level'] = 'high'
        elif any(alert['severity'] == 'medium' for alert in report['alerts']):
            report['risk_level'] = 'medium'
        
        return report