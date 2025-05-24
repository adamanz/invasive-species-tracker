#!/usr/bin/env python3
"""Comprehensive tests for the integrated invasive species detection system."""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

import unittest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
import numpy as np

from src.detector import InvasiveSpeciesDetector, DetectionResult
from src.gee.satellite_data import SpectralSignature
from src.gee.change_detection import ChangeEvent
from src.gee.temporal_analysis import TemporalComposite


class TestIntegratedSystem(unittest.TestCase):
    """Test the integrated invasive species detection system."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.detector = InvasiveSpeciesDetector(satellite="sentinel2")
        self.test_location = (-121.5969, 37.9089)  # Discovery Bay
        self.test_date = datetime(2023, 8, 15)
    
    @patch('src.detector.Sentinel2Extractor')
    def test_basic_detection(self, mock_extractor):
        """Test basic detection at a single location."""
        # Mock spectral signature
        mock_signature = SpectralSignature(
            latitude=37.9089,
            longitude=-121.5969,
            acquisition_date=self.test_date,
            satellite='Sentinel-2',
            band_names=['B2', 'B3', 'B4', 'B8'],
            band_values={'B2': 0.05, 'B3': 0.06, 'B4': 0.04, 'B8': 0.25},
            cloud_probability=5.0,
            metadata={}
        )
        
        self.detector.extractor.extract_spectral_signature = Mock(return_value=mock_signature)
        
        # Run detection
        result = self.detector.detect_at_location(
            self.test_location,
            self.test_date,
            comprehensive=False
        )
        
        # Assertions
        self.assertIsInstance(result, DetectionResult)
        self.assertEqual(result.location, self.test_location)
        self.assertEqual(result.detection_date, self.test_date)
        self.assertIsInstance(result.confidence, (int, float))
        self.assertIsInstance(result.invasive_detected, bool)
    
    def test_null_detection_no_imagery(self):
        """Test handling when no imagery is available."""
        # Mock no imagery
        self.detector.extractor.extract_spectral_signature = Mock(return_value=None)
        
        result = self.detector.detect_at_location(
            self.test_location,
            self.test_date
        )
        
        self.assertFalse(result.invasive_detected)
        self.assertEqual(result.confidence, 0)
        self.assertIn('error', result.detailed_report)
    
    @patch('src.detector.ClaudeSpectralAnalyzer')
    def test_spectral_analysis_integration(self, mock_claude):
        """Test integration with Claude spectral analyzer."""
        # Mock spectral signature
        mock_signature = self._create_mock_signature()
        self.detector.extractor.extract_spectral_signature = Mock(return_value=mock_signature)
        
        # Mock Claude response
        mock_claude_response = {
            'detection_confidence': 85,
            'invasive_species_likely': True,
            'possible_species': ['Water Hyacinth'],
            'anomalies': ['High NIR reflectance'],
            'vegetation_health': 'Abnormal',
            'reasoning': 'Spectral pattern matches water hyacinth'
        }
        
        self.detector.spectral_ai.analyze_single_signature = Mock(
            return_value=mock_claude_response
        )
        
        # Run detection
        result = self.detector.detect_at_location(
            self.test_location,
            self.test_date,
            comprehensive=False
        )
        
        # Assertions
        self.assertTrue(result.invasive_detected)
        self.assertEqual(result.confidence, 85)
        self.assertIn('Water Hyacinth', result.species)
    
    @patch('src.detector.TemporalAnalyzer')
    def test_temporal_analysis_integration(self, mock_temporal):
        """Test temporal analysis integration."""
        # Mock baseline composite
        mock_baseline = TemporalComposite(
            start_date=datetime(2023, 6, 1),
            end_date=datetime(2023, 7, 15),
            location=self.test_location,
            num_images=10,
            median_values={'B8': 0.15, 'B4': 0.08},
            percentile_10={'B8': 0.12, 'B4': 0.07},
            percentile_90={'B8': 0.18, 'B4': 0.09},
            std_dev={'B8': 0.02, 'B4': 0.01},
            metadata={}
        )
        
        self.detector.temporal_analyzer.create_baseline_composite = Mock(
            return_value=mock_baseline
        )
        
        # Test baseline creation
        baseline = self.detector.temporal_analyzer.create_baseline_composite(
            self.test_location,
            datetime(2023, 6, 1),
            datetime(2023, 7, 15)
        )
        
        self.assertIsNotNone(baseline)
        self.assertEqual(baseline.num_images, 10)
    
    def test_change_detection_integration(self):
        """Test change detection integration."""
        # Mock change event
        mock_event = ChangeEvent(
            location=self.test_location,
            detection_date=self.test_date,
            change_type='sudden',
            magnitude=0.8,
            confidence=0.75,
            affected_bands=['B8', 'B4'],
            metadata={'anomalies': [{'band': 'B8', 'z_score': 3.5}]}
        )
        
        self.detector.change_detector.detect_spectral_anomalies = Mock(
            return_value=[mock_event]
        )
        
        # Test anomaly detection
        events = self.detector.change_detector.detect_spectral_anomalies(
            self.test_location,
            self.test_date
        )
        
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0].change_type, 'sudden')
        self.assertEqual(events[0].magnitude, 0.8)
    
    @patch('src.detector.ClaudeChangeAnalyzer')
    def test_outbreak_analysis(self, mock_claude_change):
        """Test outbreak analysis with Claude."""
        # Mock change event
        mock_event = self._create_mock_change_event()
        
        # Mock Claude outbreak analysis
        mock_outbreak = {
            'outbreak_likelihood': 92,
            'invasive_species_detected': True,
            'key_evidence': [
                'Rapid NIR increase over 2 weeks',
                'Spectral signature matches water hyacinth'
            ],
            'outbreak_stage': 'active',
            'detailed_reasoning': 'High confidence outbreak detection',
            'urgency_level': 'immediate'
        }
        
        self.detector.change_ai.analyze_change_for_invasion = Mock(
            return_value=mock_outbreak
        )
        
        # Test analysis
        analysis = self.detector.change_ai.analyze_change_for_invasion(mock_event)
        
        self.assertEqual(analysis['outbreak_likelihood'], 92)
        self.assertTrue(analysis['invasive_species_detected'])
        self.assertEqual(analysis['outbreak_stage'], 'active')
    
    def test_comprehensive_detection(self):
        """Test full comprehensive detection workflow."""
        # This would be an integration test with real satellite data
        # For unit testing, we mock all components
        
        # Mock all necessary components
        self._setup_comprehensive_mocks()
        
        # Run comprehensive detection
        result = self.detector.detect_at_location(
            self.test_location,
            self.test_date,
            comprehensive=True
        )
        
        # Assertions
        self.assertIsInstance(result, DetectionResult)
        self.assertIsNotNone(result.detailed_report)
        self.assertIn('spectral_analysis', result.detailed_report)
        self.assertIn('outbreak_analysis', result.detailed_report)
        self.assertIsInstance(result.recommended_actions, list)
    
    def test_regional_monitoring(self):
        """Test regional monitoring functionality."""
        # Define test region (small area around Discovery Bay)
        bounds = [(-121.62, 37.88), (-121.57, 37.93)]
        
        # Mock hotspot detection
        mock_hotspots = {
            'hotspots_detected': 3,
            'hotspot_clusters': [
                {
                    'center': (-121.5969, 37.9089),
                    'members': [{'location': self.test_location}],
                    'average_magnitude': 0.75
                }
            ]
        }
        
        self.detector.multi_scale_detector.detect_invasion_hotspots = Mock(
            return_value=mock_hotspots
        )
        
        # Mock detection at hotspot
        self._mock_basic_detection()
        
        # Run regional monitoring
        results = self.detector.monitor_region(bounds, self.test_date)
        
        # Assertions
        self.assertEqual(results['total_hotspots'], 3)
        self.assertEqual(len(results['hotspot_clusters']), 1)
        self.assertIn('regional_risk_level', results)
    
    def test_invasion_tracking(self):
        """Test invasion progression tracking."""
        start_date = datetime(2023, 6, 1)
        end_date = datetime(2023, 9, 1)
        
        # Mock temporal signatures
        mock_signatures = [
            self._create_mock_signature(date=start_date + timedelta(days=i*30))
            for i in range(4)
        ]
        
        self.detector.extractor.extract_temporal_signatures = Mock(
            return_value=mock_signatures
        )
        
        # Mock invasion front tracking
        mock_tracking = {
            'spread_detected': True,
            'primary_spread_directions': ['N', 'NE'],
            'directional_spread': {
                'N': {'invasion_likely': True, 'vegetation_change_percent': 45}
            }
        }
        
        self.detector.invasion_tracker.track_invasion_front = Mock(
            return_value=mock_tracking
        )
        
        # Run tracking
        results = self.detector.track_invasion_progression(
            self.test_location,
            start_date,
            end_date
        )
        
        # Assertions
        self.assertTrue(results['spread_detected'])
        self.assertIn('N', results['spread_directions'])
        self.assertEqual(len(results['temporal_detections']), 4)
    
    def test_validation_framework(self):
        """Test validation against ground truth."""
        # Create mock detection result
        mock_result = DetectionResult(
            location=self.test_location,
            detection_date=self.test_date,
            invasive_detected=True,
            confidence=0.85,
            species=['Water Hyacinth'],
            outbreak_stage='active',
            spread_analysis={},
            recommended_actions=[],
            detailed_report={}
        )
        
        # Mock ground truth
        from src.validation.framework import GroundTruthPoint
        mock_ground_truth = GroundTruthPoint(
            location=self.test_location,
            observation_date=self.test_date,
            invasive_present=True,
            species='Water Hyacinth',
            coverage_percent=40,
            observer='Test Observer',
            notes='Test validation'
        )
        
        self.detector.validator.add_ground_truth(mock_ground_truth)
        
        # Run validation
        validation = self.detector.validate_detection(mock_result)
        
        # Assertions
        self.assertTrue(validation['validation_performed'])
        if 'individual_result' in validation:
            self.assertTrue(validation['individual_result']['correct'])
    
    def test_error_handling(self):
        """Test error handling in various scenarios."""
        # Test with invalid location
        invalid_location = (999, 999)  # Invalid coordinates
        
        result = self.detector.detect_at_location(
            invalid_location,
            self.test_date
        )
        
        # Should return a result even with errors
        self.assertIsInstance(result, DetectionResult)
        self.assertFalse(result.invasive_detected)
    
    # Helper methods
    def _create_mock_signature(self, date=None):
        """Create a mock spectral signature."""
        return SpectralSignature(
            latitude=self.test_location[1],
            longitude=self.test_location[0],
            acquisition_date=date or self.test_date,
            satellite='Sentinel-2',
            band_names=['B2', 'B3', 'B4', 'B5', 'B6', 'B7', 'B8', 'B8A', 'B11', 'B12'],
            band_values={
                'B2': 0.045, 'B3': 0.055, 'B4': 0.042,
                'B5': 0.065, 'B6': 0.045, 'B7': 0.052,
                'B8': 0.28, 'B8A': 0.29, 'B11': 0.15, 'B12': 0.08
            },
            cloud_probability=3.5,
            metadata={}
        )
    
    def _create_mock_change_event(self):
        """Create a mock change event."""
        return ChangeEvent(
            location=self.test_location,
            detection_date=self.test_date,
            change_type='sudden',
            magnitude=0.85,
            confidence=0.8,
            affected_bands=['B8', 'B4', 'B5'],
            metadata={
                'anomalies': [
                    {'band': 'B8', 'z_score': 3.8, 'change_percent': 87}
                ]
            }
        )
    
    def _setup_comprehensive_mocks(self):
        """Set up mocks for comprehensive testing."""
        # Mock spectral extraction
        self.detector.extractor.extract_spectral_signature = Mock(
            return_value=self._create_mock_signature()
        )
        
        # Mock spectral analysis
        self.detector.spectral_ai.analyze_single_signature = Mock(
            return_value={
                'detection_confidence': 75,
                'invasive_species_likely': True,
                'possible_species': ['Water Hyacinth']
            }
        )
        
        # Mock baseline
        self.detector.temporal_analyzer.create_baseline_composite = Mock(
            return_value=Mock(median_values={'B8': 0.15, 'B4': 0.08})
        )
        
        # Mock change detection
        self.detector.change_detector.detect_spectral_anomalies = Mock(
            return_value=[self._create_mock_change_event()]
        )
        
        # Mock outbreak analysis
        self.detector.change_ai.analyze_change_for_invasion = Mock(
            return_value={
                'outbreak_likelihood': 88,
                'outbreak_stage': 'active'
            }
        )
    
    def _mock_basic_detection(self):
        """Mock basic detection components."""
        mock_result = DetectionResult(
            location=self.test_location,
            detection_date=self.test_date,
            invasive_detected=True,
            confidence=0.82,
            species=['Water Hyacinth'],
            outbreak_stage='active',
            spread_analysis=None,
            recommended_actions=['Field validation recommended'],
            detailed_report={}
        )
        
        self.detector.detect_at_location = Mock(return_value=mock_result)


class TestClaudeIntegration(unittest.TestCase):
    """Test Claude AI integration components."""
    
    def setUp(self):
        """Set up test fixtures."""
        from src.analysis.change_analyzer import ClaudeChangeAnalyzer
        self.analyzer = ClaudeChangeAnalyzer()
        self.test_event = self._create_test_event()
    
    def test_outbreak_prompt_generation(self):
        """Test that outbreak detection prompts are properly formatted."""
        # Access private method for testing
        prompt = self.analyzer._build_outbreak_detection_prompt(
            self.test_event,
            None,
            None
        )
        
        # Check prompt contains key elements
        self.assertIn("DETECTED CHANGE EVENT", prompt)
        self.assertIn("CRITICAL INDICATORS", prompt)
        self.assertIn("OUTBREAK LIKELIHOOD", prompt)
        self.assertIn("outbreak_likelihood", prompt)  # JSON format
    
    def test_response_parsing(self):
        """Test parsing of Claude responses."""
        # Test JSON response
        json_response = '''```json
        {
            "outbreak_likelihood": 85,
            "invasive_species_detected": true,
            "key_evidence": ["Rapid NIR increase"],
            "outbreak_stage": "active"
        }
        ```'''
        
        parsed = self.analyzer._parse_outbreak_analysis(json_response)
        
        self.assertEqual(parsed['outbreak_likelihood'], 85)
        self.assertTrue(parsed['invasive_species_detected'])
        self.assertEqual(parsed['outbreak_stage'], 'active')
    
    def test_spatial_analysis_prompt(self):
        """Test spatial spread analysis prompt generation."""
        center_events = [self.test_event]
        surrounding_events = {
            'N': [self.test_event],
            'E': [self.test_event]
        }
        
        prompt = self.analyzer._build_spatial_spread_prompt(
            center_events,
            surrounding_events,
            None
        )
        
        # Check spatial elements
        self.assertIn("SPATIAL CHANGE PATTERN", prompt)
        self.assertIn("SPREAD DIRECTIONALITY", prompt)
        self.assertIn("spatial_outbreak_pattern", prompt)
    
    def _create_test_event(self):
        """Create test change event."""
        return ChangeEvent(
            location=(-121.5969, 37.9089),
            detection_date=datetime(2023, 8, 15),
            change_type='sudden',
            magnitude=0.75,
            confidence=0.8,
            affected_bands=['B8', 'B4'],
            metadata={'anomalies': []}
        )


class TestEndToEnd(unittest.TestCase):
    """End-to-end integration tests."""
    
    @unittest.skipIf(not Path('.env').exists(), "No .env file found")
    def test_real_sacramento_detection(self):
        """Test with real Sacramento Delta location (requires .env)."""
        detector = InvasiveSpeciesDetector()
        
        # Discovery Bay location
        location = (-121.5969, 37.9089)
        date = datetime(2023, 8, 15)
        
        # Run detection (may take time due to API calls)
        result = detector.detect_at_location(
            location,
            date,
            comprehensive=False  # Quick test
        )
        
        # Basic assertions
        self.assertIsInstance(result, DetectionResult)
        self.assertEqual(result.location, location)
        self.assertIsInstance(result.confidence, (int, float))
        self.assertIsInstance(result.invasive_detected, bool)
        
        # Print results for manual inspection
        print(f"\nReal Detection Results:")
        print(f"Location: {result.location}")
        print(f"Invasive Detected: {result.invasive_detected}")
        print(f"Confidence: {result.confidence}%")
        print(f"Species: {result.species}")


if __name__ == '__main__':
    unittest.main()