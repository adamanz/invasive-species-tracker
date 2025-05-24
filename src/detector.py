"""Integrated invasive species detector combining all components."""

from typing import List, Dict, Tuple, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass
import json
from pathlib import Path

from src.gee.satellite_data import Sentinel2Extractor, LandsatExtractor
from src.gee.temporal_analysis import TemporalAnalyzer, InvasionTracker
from src.gee.change_detection import SpectralChangeDetector, EarlyWarningSystem, MultiScaleChangeDetector
from src.analysis.spectral_analyzer import ClaudeSpectralAnalyzer
from src.analysis.change_analyzer import ClaudeChangeAnalyzer
from src.validation.framework import ValidationFramework
from src.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class DetectionResult:
    """Container for comprehensive detection results."""
    location: Tuple[float, float]
    detection_date: datetime
    invasive_detected: bool
    confidence: float
    species: Optional[List[str]]
    outbreak_stage: Optional[str]
    spread_analysis: Optional[Dict[str, Any]]
    recommended_actions: List[str]
    detailed_report: Dict[str, Any]


class InvasiveSpeciesDetector:
    """Main detector integrating all components for invasive species detection."""
    
    def __init__(self, satellite: str = "sentinel2"):
        """Initialize the integrated detector.
        
        Args:
            satellite: Primary satellite to use ('sentinel2' or 'landsat')
        """
        # Initialize satellite data extractor
        if satellite.lower() == "sentinel2":
            self.extractor = Sentinel2Extractor()
        else:
            self.extractor = LandsatExtractor()
        
        # Initialize analysis components
        self.temporal_analyzer = TemporalAnalyzer(self.extractor)
        self.change_detector = SpectralChangeDetector(self.extractor)
        self.multi_scale_detector = MultiScaleChangeDetector(self.extractor)
        self.early_warning = EarlyWarningSystem(self.extractor)
        self.invasion_tracker = InvasionTracker(self.temporal_analyzer)
        
        # Initialize Claude AI analyzers
        self.spectral_ai = ClaudeSpectralAnalyzer()
        self.change_ai = ClaudeChangeAnalyzer()
        
        # Initialize validation
        self.validator = ValidationFramework()
        
        logger.info(f"Invasive species detector initialized with {satellite}")
    
    def detect_at_location(
        self,
        location: Tuple[float, float],
        date: datetime,
        comprehensive: bool = True
    ) -> DetectionResult:
        """Perform invasive species detection at a specific location.
        
        Args:
            location: (longitude, latitude) tuple
            date: Date for detection
            comprehensive: Whether to perform full analysis
            
        Returns:
            DetectionResult with findings
        """
        logger.info(f"Starting detection at {location} for {date}")
        
        # Step 1: Extract spectral signature
        signature = self.extractor.extract_spectral_signature(location, date)
        if not signature:
            return self._create_null_result(location, date, "No imagery available")
        
        # Step 2: Direct spectral analysis with Claude
        spectral_analysis = self.spectral_ai.analyze_single_signature(
            signature,
            species_of_interest=[
                "Water Hyacinth", "Brazilian Waterweed", "Purple Loosestrife",
                "Kudzu", "Giant Salvinia", "Hydrilla"
            ]
        )
        
        # Quick return if not comprehensive
        if not comprehensive:
            return self._create_result_from_spectral(
                location, date, spectral_analysis
            )
        
        # Step 3: Create baseline and detect changes
        baseline = self.temporal_analyzer.create_baseline_composite(
            location,
            date - timedelta(days=90),
            date - timedelta(days=30)
        )
        
        change_events = []
        if baseline:
            # Detect spectral anomalies
            anomalies = self.change_detector.detect_spectral_anomalies(
                location, date, baseline_days=60
            )
            change_events.extend(anomalies)
            
            # Detect gradual changes
            gradual = self.change_detector.track_gradual_changes(
                location,
                date - timedelta(days=120),
                date
            )
            change_events.extend(gradual)
        
        # Step 4: Analyze changes with Claude
        outbreak_analysis = {}
        if change_events:
            # Analyze most significant change
            most_significant = max(change_events, key=lambda x: x.magnitude)
            outbreak_analysis = self.change_ai.analyze_change_for_invasion(
                most_significant, baseline
            )
        
        # Step 5: Temporal pattern analysis
        temporal_analysis = {}
        if len(change_events) > 2:
            temporal_analysis = self.change_ai.analyze_temporal_progression(
                change_events,
                {'ecosystem_type': 'wetland/aquatic'}  # Could be enhanced
            )
        
        # Step 6: Spatial spread analysis
        spatial_analysis = self._analyze_spatial_spread(location, date)
        
        # Step 7: Generate comprehensive report
        comprehensive_report = self._generate_comprehensive_report(
            spectral_analysis,
            outbreak_analysis,
            temporal_analysis,
            spatial_analysis,
            change_events
        )
        
        # Step 8: Generate alert if needed
        alert = None
        if outbreak_analysis.get('outbreak_likelihood', 0) > 70:
            alert = self.change_ai.generate_outbreak_alert(
                location, comprehensive_report
            )
        
        # Create final result
        return self._create_comprehensive_result(
            location, date, comprehensive_report, alert
        )
    
    def monitor_region(
        self,
        bounds: List[Tuple[float, float]],
        date: datetime,
        grid_size_meters: int = 1000
    ) -> Dict[str, Any]:
        """Monitor a region for invasive species.
        
        Args:
            bounds: [(min_lon, min_lat), (max_lon, max_lat)]
            date: Date for monitoring
            grid_size_meters: Grid resolution
            
        Returns:
            Regional monitoring results
        """
        logger.info(f"Monitoring region {bounds}")
        
        # Detect hotspots
        hotspots = self.multi_scale_detector.detect_invasion_hotspots(
            bounds, date, grid_size_meters
        )
        
        # Analyze top hotspots with Claude
        detailed_hotspots = []
        if hotspots.get('hotspot_clusters'):
            for cluster in hotspots['hotspot_clusters'][:5]:  # Top 5
                center = cluster['center']
                result = self.detect_at_location(
                    center, date, comprehensive=False
                )
                detailed_hotspots.append({
                    'location': center,
                    'cluster_size': len(cluster['members']),
                    'detection_result': result
                })
        
        return {
            'region_bounds': bounds,
            'analysis_date': date.isoformat(),
            'grid_resolution_m': grid_size_meters,
            'total_hotspots': hotspots.get('hotspots_detected', 0),
            'hotspot_clusters': len(hotspots.get('hotspot_clusters', [])),
            'detailed_analysis': detailed_hotspots,
            'regional_risk_level': self._assess_regional_risk(detailed_hotspots)
        }
    
    def track_invasion_progression(
        self,
        location: Tuple[float, float],
        start_date: datetime,
        end_date: datetime,
        interval_days: int = 14
    ) -> Dict[str, Any]:
        """Track invasion progression over time.
        
        Args:
            location: Center point to track
            start_date: Start of tracking period
            end_date: End of tracking period
            interval_days: Days between observations
            
        Returns:
            Invasion progression analysis
        """
        logger.info(f"Tracking invasion progression at {location}")
        
        # Extract temporal signatures
        signatures = self.extractor.extract_temporal_signatures(
            location, start_date, end_date, interval_days
        )
        
        if len(signatures) < 3:
            return {'error': 'Insufficient temporal data'}
        
        # Analyze each signature
        temporal_detections = []
        for sig in signatures:
            analysis = self.spectral_ai.analyze_single_signature(sig)
            temporal_detections.append({
                'date': sig.acquisition_date,
                'invasive_likelihood': analysis.get('detection_confidence', 0),
                'detected': analysis.get('invasive_species_likely', False)
            })
        
        # Track invasion front
        invasion_tracking = self.invasion_tracker.track_invasion_front(
            location, start_date, end_date
        )
        
        # Analyze progression with Claude
        change_events = self.change_detector.track_gradual_changes(
            location, start_date, end_date
        )
        
        progression_analysis = {}
        if change_events:
            progression_analysis = self.change_ai.analyze_temporal_progression(
                change_events,
                {'tracking_period': f"{start_date.date()} to {end_date.date()}"}
            )
        
        return {
            'location': location,
            'tracking_period': {
                'start': start_date.isoformat(),
                'end': end_date.isoformat()
            },
            'temporal_detections': temporal_detections,
            'invasion_front_analysis': invasion_tracking,
            'progression_analysis': progression_analysis,
            'spread_detected': invasion_tracking.get('spread_detected', False),
            'spread_directions': invasion_tracking.get('primary_spread_directions', [])
        }
    
    def validate_detection(
        self,
        detection_result: DetectionResult,
        ground_truth_file: Optional[str] = None
    ) -> Dict[str, Any]:
        """Validate detection against ground truth.
        
        Args:
            detection_result: Result to validate
            ground_truth_file: Optional CSV file with ground truth
            
        Returns:
            Validation metrics
        """
        if ground_truth_file:
            self.validator.load_ground_truth_csv(ground_truth_file)
        
        # Validate the detection
        validation = self.validator.validate_detection(
            detection_result.location,
            detection_result.detection_date,
            detection_result.invasive_detected,
            detection_result.confidence,
            detection_result.species[0] if detection_result.species else None
        )
        
        if validation:
            metrics = self.validator.calculate_metrics()
            return {
                'validation_performed': True,
                'metrics': metrics,
                'individual_result': {
                    'correct': validation.ground_truth == validation.predicted,
                    'confidence': validation.prediction_confidence
                }
            }
        
        return {'validation_performed': False, 'reason': 'No matching ground truth'}
    
    def _analyze_spatial_spread(
        self,
        location: Tuple[float, float],
        date: datetime
    ) -> Dict[str, Any]:
        """Analyze spatial spread patterns around location."""
        # Extract spatial context
        context = self.extractor.extract_spatial_context(
            location, date, radius_meters=500, sample_points=8
        )
        
        if not context['center'] or len(context['surrounding']) < 4:
            return {}
        
        # Get change events for spatial analysis
        center_changes = self.change_detector.detect_spectral_anomalies(
            location, date
        )
        
        surrounding_changes = {}
        directions = ['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW']
        
        for i, sig in enumerate(context['surrounding']):
            if i < len(directions):
                direction = directions[i]
                changes = self.change_detector.detect_spectral_anomalies(
                    (sig.longitude, sig.latitude), date
                )
                if changes:
                    surrounding_changes[direction] = changes
        
        # Analyze with Claude
        if center_changes or surrounding_changes:
            return self.change_ai.analyze_spatial_spread_pattern(
                center_changes, surrounding_changes
            )
        
        return {}
    
    def _generate_comprehensive_report(
        self,
        spectral: Dict[str, Any],
        outbreak: Dict[str, Any],
        temporal: Dict[str, Any],
        spatial: Dict[str, Any],
        events: List[Any]
    ) -> Dict[str, Any]:
        """Generate comprehensive analysis report."""
        report = {
            'spectral_analysis': spectral,
            'outbreak_analysis': outbreak,
            'temporal_analysis': temporal,
            'spatial_analysis': spatial,
            'change_events_detected': len(events),
            'combined_confidence': self._calculate_combined_confidence(
                spectral, outbreak, temporal, spatial
            )
        }
        
        # Determine overall invasion status
        confidences = [
            spectral.get('detection_confidence', 0),
            outbreak.get('outbreak_likelihood', 0),
            temporal.get('invasion_progression_detected', False) * 80,
            spatial.get('spatial_outbreak_pattern', '') != 'none' * 70
        ]
        
        report['overall_invasive_detected'] = max(confidences) > 70
        report['highest_confidence_source'] = self._get_highest_confidence_source(
            spectral, outbreak, temporal, spatial
        )
        
        return report
    
    def _calculate_combined_confidence(
        self,
        spectral: Dict[str, Any],
        outbreak: Dict[str, Any],
        temporal: Dict[str, Any],
        spatial: Dict[str, Any]
    ) -> float:
        """Calculate combined confidence from all analyses."""
        weights = {
            'spectral': 0.3,
            'outbreak': 0.3,
            'temporal': 0.2,
            'spatial': 0.2
        }
        
        confidences = {
            'spectral': spectral.get('detection_confidence', 0) / 100,
            'outbreak': outbreak.get('outbreak_likelihood', 0) / 100,
            'temporal': 0.8 if temporal.get('invasion_progression_detected') else 0.2,
            'spatial': 0.7 if spatial.get('spatial_outbreak_pattern') not in ['none', None] else 0.3
        }
        
        weighted_sum = sum(
            confidences[key] * weights[key]
            for key in weights
        )
        
        return round(weighted_sum * 100, 1)
    
    def _get_highest_confidence_source(
        self,
        spectral: Dict[str, Any],
        outbreak: Dict[str, Any],
        temporal: Dict[str, Any],
        spatial: Dict[str, Any]
    ) -> str:
        """Determine which analysis has highest confidence."""
        sources = {
            'spectral': spectral.get('detection_confidence', 0),
            'outbreak': outbreak.get('outbreak_likelihood', 0),
            'temporal': 80 if temporal.get('invasion_progression_detected') else 20,
            'spatial': 70 if spatial.get('spatial_outbreak_pattern') not in ['none', None] else 30
        }
        
        return max(sources.items(), key=lambda x: x[1])[0]
    
    def _assess_regional_risk(self, hotspots: List[Dict[str, Any]]) -> str:
        """Assess overall regional risk level."""
        if not hotspots:
            return 'low'
        
        high_risk = sum(
            1 for h in hotspots
            if h['detection_result'].confidence > 70
        )
        
        if high_risk >= 3:
            return 'high'
        elif high_risk >= 1:
            return 'moderate'
        else:
            return 'low'
    
    def _create_null_result(
        self,
        location: Tuple[float, float],
        date: datetime,
        reason: str
    ) -> DetectionResult:
        """Create null result when detection cannot be performed."""
        return DetectionResult(
            location=location,
            detection_date=date,
            invasive_detected=False,
            confidence=0,
            species=None,
            outbreak_stage=None,
            spread_analysis=None,
            recommended_actions=["Retry with different date"],
            detailed_report={'error': reason}
        )
    
    def _create_result_from_spectral(
        self,
        location: Tuple[float, float],
        date: datetime,
        analysis: Dict[str, Any]
    ) -> DetectionResult:
        """Create result from spectral analysis only."""
        return DetectionResult(
            location=location,
            detection_date=date,
            invasive_detected=analysis.get('invasive_species_likely', False),
            confidence=analysis.get('detection_confidence', 0),
            species=analysis.get('possible_species', []),
            outbreak_stage='unknown',
            spread_analysis=None,
            recommended_actions=['Perform comprehensive analysis for details'],
            detailed_report={'spectral_analysis': analysis}
        )
    
    def _create_comprehensive_result(
        self,
        location: Tuple[float, float],
        date: datetime,
        report: Dict[str, Any],
        alert: Optional[Dict[str, Any]]
    ) -> DetectionResult:
        """Create comprehensive detection result."""
        # Extract key information
        invasive_detected = report.get('overall_invasive_detected', False)
        confidence = report.get('combined_confidence', 0)
        
        # Get species from various sources
        species = []
        if report.get('spectral_analysis', {}).get('possible_species'):
            species.extend(report['spectral_analysis']['possible_species'])
        if report.get('outbreak_analysis', {}).get('possible_species'):
            species.extend(report['outbreak_analysis']['possible_species'])
        
        # Remove duplicates
        species = list(set(species))
        
        # Get outbreak stage
        outbreak_stage = report.get('outbreak_analysis', {}).get('outbreak_stage', 'unknown')
        
        # Get recommended actions
        actions = []
        if alert and alert.get('recommended_actions'):
            actions = [a['action'] for a in alert['recommended_actions']]
        elif invasive_detected:
            actions = [
                "Conduct field validation",
                "Monitor spread direction",
                "Prepare treatment plan"
            ]
        
        return DetectionResult(
            location=location,
            detection_date=date,
            invasive_detected=invasive_detected,
            confidence=confidence,
            species=species[:3] if species else None,  # Top 3 species
            outbreak_stage=outbreak_stage,
            spread_analysis=report.get('spatial_analysis'),
            recommended_actions=actions,
            detailed_report=report
        )