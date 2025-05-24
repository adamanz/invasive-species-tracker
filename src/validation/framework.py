"""Validation framework for invasive species detection results."""

import json
import pandas as pd
from typing import List, Dict, Tuple, Optional, Any
from datetime import datetime
from dataclasses import dataclass, asdict
from pathlib import Path
import numpy as np
from src.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class GroundTruthPoint:
    """Container for ground truth validation data."""
    location: Tuple[float, float]
    observation_date: datetime
    invasive_present: bool
    species: Optional[str]
    coverage_percent: Optional[float]
    observer: str
    notes: Optional[str]
    confidence: float = 1.0  # Observer confidence in identification


@dataclass
class ValidationResult:
    """Container for validation results."""
    location: Tuple[float, float]
    ground_truth: bool
    predicted: bool
    prediction_confidence: float
    detection_date: datetime
    species_match: Optional[bool]
    metadata: Dict[str, Any]


class ValidationFramework:
    """Framework for validating invasive species detection results."""
    
    def __init__(self, data_dir: str = "data/validation"):
        """Initialize validation framework."""
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.ground_truth_data = []
        self.validation_results = []
        logger.info("Validation framework initialized")
    
    def add_ground_truth(self, ground_truth: GroundTruthPoint):
        """Add a ground truth observation."""
        self.ground_truth_data.append(ground_truth)
        logger.info(f"Added ground truth point at {ground_truth.location}")
    
    def load_ground_truth_csv(self, csv_path: str):
        """Load ground truth data from CSV file.
        
        Expected columns:
        - longitude, latitude
        - observation_date
        - invasive_present (boolean)
        - species (optional)
        - coverage_percent (optional)
        - observer
        - notes (optional)
        """
        try:
            df = pd.read_csv(csv_path)
            
            for _, row in df.iterrows():
                ground_truth = GroundTruthPoint(
                    location=(row['longitude'], row['latitude']),
                    observation_date=pd.to_datetime(row['observation_date']),
                    invasive_present=bool(row['invasive_present']),
                    species=row.get('species', None),
                    coverage_percent=row.get('coverage_percent', None),
                    observer=row['observer'],
                    notes=row.get('notes', None)
                )
                self.add_ground_truth(ground_truth)
            
            logger.info(f"Loaded {len(df)} ground truth points from {csv_path}")
            
        except Exception as e:
            logger.error(f"Error loading ground truth CSV: {str(e)}")
    
    def validate_detection(
        self,
        location: Tuple[float, float],
        detection_date: datetime,
        predicted_invasive: bool,
        prediction_confidence: float,
        predicted_species: Optional[str] = None,
        tolerance_meters: float = 100,
        tolerance_days: int = 30
    ) -> Optional[ValidationResult]:
        """Validate a detection against ground truth data.
        
        Args:
            location: Detection location
            detection_date: Date of detection
            predicted_invasive: Whether invasive species was predicted
            prediction_confidence: Confidence of prediction (0-1)
            predicted_species: Predicted species name
            tolerance_meters: Spatial tolerance for matching
            tolerance_days: Temporal tolerance for matching
            
        Returns:
            ValidationResult if ground truth found, None otherwise
        """
        # Find matching ground truth
        matching_truth = self._find_matching_ground_truth(
            location, detection_date, tolerance_meters, tolerance_days
        )
        
        if not matching_truth:
            return None
        
        # Check species match if both specified
        species_match = None
        if predicted_species and matching_truth.species:
            species_match = predicted_species.lower() in matching_truth.species.lower()
        
        result = ValidationResult(
            location=location,
            ground_truth=matching_truth.invasive_present,
            predicted=predicted_invasive,
            prediction_confidence=prediction_confidence,
            detection_date=detection_date,
            species_match=species_match,
            metadata={
                'ground_truth_date': matching_truth.observation_date.isoformat(),
                'ground_truth_species': matching_truth.species,
                'predicted_species': predicted_species,
                'spatial_distance_m': self._calculate_distance(
                    location, matching_truth.location
                )
            }
        )
        
        self.validation_results.append(result)
        return result
    
    def calculate_metrics(self) -> Dict[str, float]:
        """Calculate validation metrics."""
        if not self.validation_results:
            return {
                'accuracy': 0,
                'precision': 0,
                'recall': 0,
                'f1_score': 0,
                'num_validations': 0
            }
        
        # Calculate confusion matrix elements
        true_positives = sum(
            1 for r in self.validation_results
            if r.ground_truth and r.predicted
        )
        true_negatives = sum(
            1 for r in self.validation_results
            if not r.ground_truth and not r.predicted
        )
        false_positives = sum(
            1 for r in self.validation_results
            if not r.ground_truth and r.predicted
        )
        false_negatives = sum(
            1 for r in self.validation_results
            if r.ground_truth and not r.predicted
        )
        
        total = len(self.validation_results)
        
        # Calculate metrics
        accuracy = (true_positives + true_negatives) / total if total > 0 else 0
        
        precision = (
            true_positives / (true_positives + false_positives)
            if (true_positives + false_positives) > 0 else 0
        )
        
        recall = (
            true_positives / (true_positives + false_negatives)
            if (true_positives + false_negatives) > 0 else 0
        )
        
        f1_score = (
            2 * (precision * recall) / (precision + recall)
            if (precision + recall) > 0 else 0
        )
        
        # Calculate species accuracy if applicable
        species_validations = [
            r for r in self.validation_results
            if r.species_match is not None
        ]
        species_accuracy = (
            sum(1 for r in species_validations if r.species_match) / len(species_validations)
            if species_validations else None
        )
        
        return {
            'accuracy': round(accuracy, 3),
            'precision': round(precision, 3),
            'recall': round(recall, 3),
            'f1_score': round(f1_score, 3),
            'true_positives': true_positives,
            'true_negatives': true_negatives,
            'false_positives': false_positives,
            'false_negatives': false_negatives,
            'num_validations': total,
            'species_accuracy': round(species_accuracy, 3) if species_accuracy else None
        }
    
    def generate_validation_report(self, output_path: Optional[str] = None) -> Dict[str, Any]:
        """Generate a comprehensive validation report."""
        metrics = self.calculate_metrics()
        
        # Analyze confidence vs accuracy
        confidence_analysis = self._analyze_confidence_correlation()
        
        # Spatial accuracy analysis
        spatial_analysis = self._analyze_spatial_accuracy()
        
        # Temporal accuracy analysis
        temporal_analysis = self._analyze_temporal_accuracy()
        
        report = {
            'report_date': datetime.now().isoformat(),
            'overall_metrics': metrics,
            'confidence_analysis': confidence_analysis,
            'spatial_analysis': spatial_analysis,
            'temporal_analysis': temporal_analysis,
            'ground_truth_summary': {
                'total_points': len(self.ground_truth_data),
                'invasive_present': sum(1 for gt in self.ground_truth_data if gt.invasive_present),
                'species_distribution': self._get_species_distribution()
            }
        }
        
        if output_path:
            with open(output_path, 'w') as f:
                json.dump(report, f, indent=2)
            logger.info(f"Validation report saved to {output_path}")
        
        return report
    
    def _find_matching_ground_truth(
        self,
        location: Tuple[float, float],
        date: datetime,
        tolerance_meters: float,
        tolerance_days: int
    ) -> Optional[GroundTruthPoint]:
        """Find ground truth point matching location and date."""
        for gt in self.ground_truth_data:
            # Check spatial proximity
            distance = self._calculate_distance(location, gt.location)
            if distance > tolerance_meters:
                continue
            
            # Check temporal proximity
            time_diff = abs((date - gt.observation_date).days)
            if time_diff > tolerance_days:
                continue
            
            return gt
        
        return None
    
    def _calculate_distance(self, point1: Tuple[float, float], point2: Tuple[float, float]) -> float:
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
    
    def _analyze_confidence_correlation(self) -> Dict[str, Any]:
        """Analyze correlation between prediction confidence and accuracy."""
        if not self.validation_results:
            return {}
        
        # Group by confidence bins
        confidence_bins = [0, 0.25, 0.5, 0.75, 1.0]
        bin_accuracy = {}
        
        for i in range(len(confidence_bins) - 1):
            bin_min = confidence_bins[i]
            bin_max = confidence_bins[i + 1]
            
            bin_results = [
                r for r in self.validation_results
                if bin_min <= r.prediction_confidence < bin_max
            ]
            
            if bin_results:
                correct = sum(1 for r in bin_results if r.ground_truth == r.predicted)
                accuracy = correct / len(bin_results)
                bin_accuracy[f"{bin_min}-{bin_max}"] = {
                    'accuracy': round(accuracy, 3),
                    'count': len(bin_results)
                }
        
        return bin_accuracy
    
    def _analyze_spatial_accuracy(self) -> Dict[str, Any]:
        """Analyze accuracy by spatial distance from ground truth."""
        distances = []
        
        for result in self.validation_results:
            if 'spatial_distance_m' in result.metadata:
                distances.append({
                    'distance': result.metadata['spatial_distance_m'],
                    'correct': result.ground_truth == result.predicted
                })
        
        if not distances:
            return {}
        
        # Calculate accuracy by distance bins
        distance_bins = [0, 25, 50, 75, 100]
        bin_accuracy = {}
        
        for i in range(len(distance_bins) - 1):
            bin_min = distance_bins[i]
            bin_max = distance_bins[i + 1]
            
            bin_results = [
                d for d in distances
                if bin_min <= d['distance'] < bin_max
            ]
            
            if bin_results:
                accuracy = sum(1 for d in bin_results if d['correct']) / len(bin_results)
                bin_accuracy[f"{bin_min}-{bin_max}m"] = round(accuracy, 3)
        
        return bin_accuracy
    
    def _analyze_temporal_accuracy(self) -> Dict[str, Any]:
        """Analyze accuracy by season."""
        seasonal_results = {
            'spring': [],
            'summer': [],
            'fall': [],
            'winter': []
        }
        
        for result in self.validation_results:
            month = result.detection_date.month
            if 3 <= month <= 5:
                season = 'spring'
            elif 6 <= month <= 8:
                season = 'summer'
            elif 9 <= month <= 11:
                season = 'fall'
            else:
                season = 'winter'
            
            seasonal_results[season].append(result.ground_truth == result.predicted)
        
        seasonal_accuracy = {}
        for season, results in seasonal_results.items():
            if results:
                seasonal_accuracy[season] = round(sum(results) / len(results), 3)
        
        return seasonal_accuracy
    
    def _get_species_distribution(self) -> Dict[str, int]:
        """Get distribution of species in ground truth data."""
        species_count = {}
        
        for gt in self.ground_truth_data:
            if gt.invasive_present and gt.species:
                species_count[gt.species] = species_count.get(gt.species, 0) + 1
        
        return species_count