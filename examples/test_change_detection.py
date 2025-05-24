#!/usr/bin/env python3
"""Test change detection and validation framework."""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from datetime import datetime, timedelta
from src.gee.satellite_data import Sentinel2Extractor
from src.gee.temporal_analysis import TemporalAnalyzer, InvasionTracker
from src.gee.change_detection import SpectralChangeDetector, EarlyWarningSystem
from src.validation.framework import ValidationFramework, GroundTruthPoint
import json

print("🔍 Invasive Species Change Detection Test")
print("="*60)

# Initialize components
sentinel2 = Sentinel2Extractor()
temporal_analyzer = TemporalAnalyzer(sentinel2)
change_detector = SpectralChangeDetector(sentinel2)
early_warning = EarlyWarningSystem(sentinel2)
invasion_tracker = InvasionTracker(temporal_analyzer)

# Test location: Discovery Bay Marina (known water hyacinth area)
test_location = (-121.5969, 37.9089)


def test_baseline_creation():
    """Test creating a baseline composite."""
    print("\n1. Creating Baseline Composite")
    print("-"*40)
    
    # Create baseline for early summer 2023
    baseline = temporal_analyzer.create_baseline_composite(
        test_location,
        datetime(2023, 6, 1),
        datetime(2023, 7, 15),
        buffer_meters=100
    )
    
    if baseline:
        print(f"✅ Baseline created with {baseline.num_images} images")
        print(f"   Period: {baseline.start_date.date()} to {baseline.end_date.date()}")
        print(f"   Median NIR (B8): {baseline.median_values.get('B8', 0):.4f}")
        print(f"   Median Red (B4): {baseline.median_values.get('B4', 0):.4f}")
        ndvi = (baseline.median_values['B8'] - baseline.median_values['B4']) / \
               (baseline.median_values['B8'] + baseline.median_values['B4'])
        print(f"   Baseline NDVI: {ndvi:.3f}")
        return baseline
    else:
        print("❌ Failed to create baseline")
        return None


def test_change_detection(baseline):
    """Test detecting changes from baseline."""
    print("\n2. Detecting Changes from Baseline")
    print("-"*40)
    
    # Get late summer observation
    current_date = datetime(2023, 8, 20)
    current_sig = sentinel2.extract_spectral_signature(test_location, current_date)
    
    if current_sig and baseline:
        # Detect changes
        changes = temporal_analyzer.detect_changes(baseline, current_sig, threshold_std=2.0)
        
        print(f"✅ Change detection completed")
        print(f"   Bands with changes: {len(changes['bands_changed'])}")
        print(f"   Significant change: {changes['significant_change']}")
        
        if changes['anomalies']:
            print("\n   Detected anomalies:")
            for anomaly in changes['anomalies'][:3]:  # Show top 3
                print(f"   - {anomaly['band']}: {anomaly['change_percent']:.1f}% change "
                      f"(z-score: {anomaly['z_score']:.2f})")
        
        return changes
    else:
        print("❌ Could not perform change detection")
        return None


def test_anomaly_detection():
    """Test spectral anomaly detection."""
    print("\n3. Spectral Anomaly Detection")
    print("-"*40)
    
    # Check for anomalies in late summer
    events = change_detector.detect_spectral_anomalies(
        test_location,
        datetime(2023, 8, 20),
        baseline_days=60,
        sensitivity=2.0
    )
    
    if events:
        print(f"✅ Detected {len(events)} anomaly events")
        for event in events:
            print(f"   - Date: {event.detection_date.date()}")
            print(f"     Type: {event.change_type}")
            print(f"     Magnitude: {event.magnitude:.2f}")
            print(f"     Confidence: {event.confidence:.2f}")
            print(f"     Affected bands: {', '.join(event.affected_bands)}")
    else:
        print("❌ No anomalies detected")
    
    return events


def test_gradual_changes():
    """Test gradual change tracking."""
    print("\n4. Gradual Change Tracking")
    print("-"*40)
    
    # Track changes over summer 2023
    gradual_events = change_detector.track_gradual_changes(
        test_location,
        datetime(2023, 6, 1),
        datetime(2023, 9, 30),
        window_days=30,
        step_days=15
    )
    
    if gradual_events:
        print(f"✅ Detected {len(gradual_events)} gradual change events")
        for event in gradual_events:
            print(f"   - Date: {event.detection_date.date()}")
            print(f"     Trend slope: {event.metadata.get('trend_slope', 0):.4f}")
            print(f"     Magnitude: {event.magnitude:.2f}")
    else:
        print("ℹ️  No significant gradual changes detected")
    
    return gradual_events


def test_early_warning():
    """Test early warning system."""
    print("\n5. Early Warning System")
    print("-"*40)
    
    # Monitor current status
    report = early_warning.monitor_location(
        test_location,
        datetime(2023, 8, 20),
        alert_thresholds={
            'sudden_change': 0.5,
            'gradual_change': 0.4,
            'phenological_anomaly': 0.7
        }
    )
    
    print(f"📊 Monitoring Report:")
    print(f"   Location: {report['location']}")
    print(f"   Risk Level: {report['risk_level'].upper()}")
    print(f"   Alerts: {len(report['alerts'])}")
    
    if report['alerts']:
        print("\n   Alert Details:")
        for alert in report['alerts']:
            print(f"   - Type: {alert['type']}")
            print(f"     Severity: {alert['severity']}")
            print(f"     Magnitude: {alert['magnitude']:.2f}")
    
    return report


def test_invasion_tracking():
    """Test invasion front tracking."""
    print("\n6. Invasion Front Tracking")
    print("-"*40)
    
    # Track invasion spread
    tracking = invasion_tracker.track_invasion_front(
        test_location,
        datetime(2023, 6, 1),
        datetime(2023, 9, 1),
        radius_meters=500,
        sample_points=8
    )
    
    print(f"🎯 Invasion Tracking Results:")
    print(f"   Center: {tracking['center_point']}")
    print(f"   Period: {tracking['period']}")
    print(f"   Spread detected: {tracking['spread_detected']}")
    
    if tracking['spread_detected']:
        print(f"   Primary spread directions: {', '.join(tracking['primary_spread_directions'])}")
        
        print("\n   Directional analysis:")
        for direction, data in tracking['directional_spread'].items():
            if data['invasion_likely']:
                print(f"   - {direction}: {data['vegetation_change_percent']:.1f}% increase")
    
    return tracking


def test_validation_framework():
    """Test validation framework with simulated ground truth."""
    print("\n7. Validation Framework")
    print("-"*40)
    
    # Create validation framework
    validator = ValidationFramework()
    
    # Add simulated ground truth data
    ground_truth_points = [
        GroundTruthPoint(
            location=test_location,
            observation_date=datetime(2023, 8, 25),
            invasive_present=True,
            species="Water Hyacinth",
            coverage_percent=40,
            observer="Field Team A",
            notes="Dense patches near marina"
        ),
        GroundTruthPoint(
            location=(-121.5950, 37.9100),
            observation_date=datetime(2023, 8, 25),
            invasive_present=False,
            species=None,
            coverage_percent=0,
            observer="Field Team A",
            notes="Clear water, no invasives"
        )
    ]
    
    for gt in ground_truth_points:
        validator.add_ground_truth(gt)
    
    # Validate our detection
    validation = validator.validate_detection(
        location=test_location,
        detection_date=datetime(2023, 8, 20),
        predicted_invasive=True,
        prediction_confidence=0.78,
        predicted_species="Water Hyacinth",
        tolerance_meters=100,
        tolerance_days=10
    )
    
    if validation:
        print("✅ Validation completed")
        print(f"   Ground truth: {'Invasive Present' if validation.ground_truth else 'No Invasive'}")
        print(f"   Predicted: {'Invasive Present' if validation.predicted else 'No Invasive'}")
        print(f"   Correct: {'Yes' if validation.ground_truth == validation.predicted else 'No'}")
        
        # Calculate metrics
        metrics = validator.calculate_metrics()
        print(f"\n   Validation Metrics:")
        print(f"   - Accuracy: {metrics['accuracy']:.1%}")
        print(f"   - Precision: {metrics['precision']:.1%}")
        print(f"   - Recall: {metrics['recall']:.1%}")
    else:
        print("❌ No matching ground truth found")
    
    return validator


if __name__ == "__main__":
    try:
        # Run all tests
        baseline = test_baseline_creation()
        
        if baseline:
            changes = test_change_detection(baseline)
        
        anomalies = test_anomaly_detection()
        gradual_changes = test_gradual_changes()
        early_warning_report = test_early_warning()
        invasion_tracking = test_invasion_tracking()
        validator = test_validation_framework()
        
        print("\n" + "="*60)
        print("✅ Phase 3 Change Detection Tests Complete!")
        print("="*60)
        
        print("\nKey Capabilities Demonstrated:")
        print("- Baseline creation and statistical analysis")
        print("- Change detection with anomaly thresholds")
        print("- Gradual change tracking over time")
        print("- Early warning system with risk levels")
        print("- Invasion front tracking in multiple directions")
        print("- Validation framework for accuracy assessment")
        
        print("\nNote: Claude AI integration will be added in Phase 4")
        print("for enhanced change analysis and detailed reporting.")
        
    except Exception as e:
        print(f"\n❌ Error during testing: {str(e)}")
        import traceback
        traceback.print_exc()