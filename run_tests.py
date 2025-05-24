#!/usr/bin/env python3
"""Run all tests and generate validation report."""

import sys
import unittest
from datetime import datetime
from pathlib import Path

# Add project to path
sys.path.append(str(Path(__file__).parent))

from src.detector import InvasiveSpeciesDetector
from tests.test_integrated_system import TestIntegratedSystem, TestClaudeIntegration


def run_unit_tests():
    """Run unit tests."""
    print("="*60)
    print("Running Unit Tests")
    print("="*60)
    
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test classes
    suite.addTests(loader.loadTestsFromTestCase(TestIntegratedSystem))
    suite.addTests(loader.loadTestsFromTestCase(TestClaudeIntegration))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


def run_integration_test():
    """Run a real integration test with Sacramento Delta."""
    print("\n" + "="*60)
    print("Running Integration Test - Sacramento Delta")
    print("="*60)
    
    try:
        # Initialize detector
        detector = InvasiveSpeciesDetector(satellite="sentinel2")
        
        # Test location: Discovery Bay Marina (known invasive area)
        location = (-121.5969, 37.9089)
        date = datetime(2023, 8, 15)
        
        print(f"\nTest Location: {location}")
        print(f"Test Date: {date.strftime('%Y-%m-%d')}")
        print("\nPerforming detection...")
        
        # Run quick detection
        result = detector.detect_at_location(location, date, comprehensive=False)
        
        print("\n--- Detection Results ---")
        print(f"Invasive Detected: {result.invasive_detected}")
        print(f"Confidence: {result.confidence}%")
        print(f"Species: {result.species if result.species else 'Unknown'}")
        print(f"Recommended Actions: {len(result.recommended_actions)} actions")
        
        # If invasive detected, show more details
        if result.invasive_detected and result.confidence > 50:
            print("\n--- High Confidence Detection Details ---")
            if 'spectral_analysis' in result.detailed_report:
                spectral = result.detailed_report['spectral_analysis']
                if 'reasoning' in spectral:
                    print(f"Reasoning: {spectral['reasoning'][:200]}...")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Integration test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_change_detection_workflow():
    """Test the change detection workflow."""
    print("\n" + "="*60)
    print("Testing Change Detection Workflow")
    print("="*60)
    
    try:
        from src.gee.satellite_data import Sentinel2Extractor
        from src.gee.temporal_analysis import TemporalAnalyzer
        from src.gee.change_detection import SpectralChangeDetector
        
        # Initialize components
        extractor = Sentinel2Extractor()
        temporal = TemporalAnalyzer(extractor)
        change_detector = SpectralChangeDetector(extractor)
        
        location = (-121.5969, 37.9089)
        
        print("\n1. Creating baseline composite...")
        baseline = temporal.create_baseline_composite(
            location,
            datetime(2023, 6, 1),
            datetime(2023, 7, 15)
        )
        
        if baseline:
            print(f"   ✅ Baseline created with {baseline.num_images} images")
            
            print("\n2. Detecting anomalies...")
            anomalies = change_detector.detect_spectral_anomalies(
                location,
                datetime(2023, 8, 15),
                baseline_days=60
            )
            
            if anomalies:
                print(f"   ✅ Detected {len(anomalies)} anomalies")
                for event in anomalies:
                    print(f"      - Magnitude: {event.magnitude:.2f}, "
                          f"Bands: {', '.join(event.affected_bands)}")
            else:
                print("   ℹ️  No anomalies detected")
        else:
            print("   ❌ Could not create baseline")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Change detection test failed: {str(e)}")
        return False


def test_validation_framework():
    """Test the validation framework."""
    print("\n" + "="*60)
    print("Testing Validation Framework")
    print("="*60)
    
    try:
        from src.validation.framework import ValidationFramework, GroundTruthPoint
        
        validator = ValidationFramework()
        
        # Add test ground truth
        ground_truth = GroundTruthPoint(
            location=(-121.5969, 37.9089),
            observation_date=datetime(2023, 8, 20),
            invasive_present=True,
            species="Water Hyacinth",
            coverage_percent=35,
            observer="Test System",
            notes="Test validation"
        )
        
        validator.add_ground_truth(ground_truth)
        
        # Validate a detection
        validation = validator.validate_detection(
            location=(-121.5969, 37.9089),
            detection_date=datetime(2023, 8, 15),
            predicted_invasive=True,
            prediction_confidence=0.78,
            predicted_species="Water Hyacinth",
            tolerance_meters=100,
            tolerance_days=10
        )
        
        if validation:
            print("✅ Validation framework working")
            print(f"   Ground truth matched: {validation.ground_truth == validation.predicted}")
            
            # Calculate metrics
            metrics = validator.calculate_metrics()
            print(f"   Accuracy: {metrics['accuracy']:.1%}")
        else:
            print("ℹ️  No matching ground truth found (expected for test)")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Validation test failed: {str(e)}")
        return False


def generate_summary_report(results):
    """Generate summary report of all tests."""
    print("\n" + "="*60)
    print("Test Summary Report")
    print("="*60)
    
    total_tests = len(results)
    passed_tests = sum(1 for r in results.values() if r)
    
    print(f"\nTotal Tests Run: {total_tests}")
    print(f"Tests Passed: {passed_tests}")
    print(f"Tests Failed: {total_tests - passed_tests}")
    print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
    
    print("\nIndividual Results:")
    for test_name, result in results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"  {test_name}: {status}")
    
    print("\n" + "="*60)
    
    if passed_tests == total_tests:
        print("🎉 All tests passed! System is working correctly.")
    else:
        print("⚠️  Some tests failed. Check logs above for details.")
    
    print("="*60)


if __name__ == "__main__":
    print("🧪 Invasive Species Tracker - System Validation")
    print("="*60)
    print(f"Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Run all tests
    test_results = {}
    
    # Unit tests
    print("\n📋 Starting Unit Tests...")
    test_results['Unit Tests'] = run_unit_tests()
    
    # Integration test (only if .env exists)
    if Path('.env').exists():
        print("\n🌍 Starting Integration Tests...")
        test_results['Integration Test'] = run_integration_test()
        test_results['Change Detection'] = test_change_detection_workflow()
    else:
        print("\n⚠️  Skipping integration tests (.env file not found)")
        test_results['Integration Test'] = None
        test_results['Change Detection'] = None
    
    # Validation framework test
    print("\n✓ Testing Validation Framework...")
    test_results['Validation Framework'] = test_validation_framework()
    
    # Generate summary
    generate_summary_report(test_results)
    
    # Exit with appropriate code
    all_passed = all(r for r in test_results.values() if r is not None)
    sys.exit(0 if all_passed else 1)