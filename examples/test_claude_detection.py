#!/usr/bin/env python3
"""Test script for Claude-based invasive species detection."""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from datetime import datetime, timedelta
from src.gee.satellite_data import Sentinel2Extractor, LandsatExtractor
from src.analysis.spectral_analyzer import ClaudeSpectralAnalyzer
from src.utils.logger import get_logger
import json

logger = get_logger(__name__)


def test_single_point_analysis():
    """Test invasive species detection at a single point."""
    print("\n" + "="*60)
    print("Test 1: Single Point Analysis")
    print("="*60)
    
    # Initialize extractors
    sentinel2 = Sentinel2Extractor()
    analyzer = ClaudeSpectralAnalyzer()
    
    # Test location (example: area with known invasive species)
    # You can change this to any location
    test_point = (-122.4194, 37.7749)  # San Francisco area
    test_date = datetime(2023, 7, 15)
    
    print(f"\nExtracting spectral signature at {test_point}")
    print(f"Date: {test_date.strftime('%Y-%m-%d')}")
    
    # Extract spectral signature
    signature = sentinel2.extract_spectral_signature(test_point, test_date)
    
    if signature:
        print(f"\n✅ Spectral data extracted successfully")
        print(f"Satellite: {signature.satellite}")
        print(f"Actual date: {signature.acquisition_date}")
        print(f"Cloud coverage: {signature.cloud_probability}%")
        
        # Analyze with Claude
        print("\n🤖 Analyzing with Claude...")
        analysis = analyzer.analyze_single_signature(
            signature,
            species_of_interest=["Japanese Knotweed", "Purple Loosestrife", "Kudzu"]
        )
        
        print("\n📊 Analysis Results:")
        print(json.dumps(analysis, indent=2))
    else:
        print("❌ No imagery found for the specified location and date")


def test_temporal_analysis():
    """Test temporal change detection."""
    print("\n" + "="*60)
    print("Test 2: Temporal Analysis (Change Detection)")
    print("="*60)
    
    sentinel2 = Sentinel2Extractor()
    analyzer = ClaudeSpectralAnalyzer()
    
    # Test location and time period
    test_point = (-122.4194, 37.7749)
    start_date = datetime(2023, 5, 1)
    end_date = datetime(2023, 9, 30)
    
    print(f"\nExtracting temporal signatures at {test_point}")
    print(f"Period: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
    
    # Extract temporal signatures
    signatures = sentinel2.extract_temporal_signatures(
        test_point, 
        start_date, 
        end_date,
        interval_days=15  # Every 2 weeks
    )
    
    print(f"\n✅ Extracted {len(signatures)} temporal signatures")
    
    if len(signatures) >= 3:
        # Analyze temporal patterns
        print("\n🤖 Analyzing temporal patterns...")
        temporal_analysis = analyzer.analyze_temporal_sequence(
            signatures,
            species_of_interest=["Japanese Knotweed", "Kudzu"]
        )
        
        print("\n📊 Temporal Analysis Results:")
        print(json.dumps(temporal_analysis, indent=2))
    else:
        print("❌ Not enough temporal data for analysis")


def test_spatial_context():
    """Test spatial context analysis."""
    print("\n" + "="*60)
    print("Test 3: Spatial Context Analysis")
    print("="*60)
    
    sentinel2 = Sentinel2Extractor()
    analyzer = ClaudeSpectralAnalyzer()
    
    # Test location
    test_point = (-122.4194, 37.7749)
    test_date = datetime(2023, 7, 15)
    
    print(f"\nExtracting spatial context at {test_point}")
    print(f"Date: {test_date.strftime('%Y-%m-%d')}")
    
    # Extract spatial context
    context = sentinel2.extract_spatial_context(
        test_point,
        test_date,
        radius_meters=200,
        sample_points=8
    )
    
    print(f"\n✅ Extracted spatial context:")
    print(f"  - Center points: {len(context['center'])}")
    print(f"  - Surrounding points: {len(context['surrounding'])}")
    
    if context['center'] and len(context['surrounding']) >= 4:
        # Analyze spatial patterns
        print("\n🤖 Analyzing spatial patterns...")
        spatial_analysis = analyzer.analyze_spatial_context(
            context['center'],
            context['surrounding'],
            species_of_interest=["Japanese Knotweed"]
        )
        
        print("\n📊 Spatial Analysis Results:")
        print(json.dumps(spatial_analysis, indent=2))
    else:
        print("❌ Not enough spatial data for analysis")


def test_combined_analysis():
    """Test combined multi-source analysis."""
    print("\n" + "="*60)
    print("Test 4: Multi-Source Analysis (Sentinel-2 + Landsat)")
    print("="*60)
    
    sentinel2 = Sentinel2Extractor()
    landsat = LandsatExtractor()
    analyzer = ClaudeSpectralAnalyzer()
    
    test_point = (-122.4194, 37.7749)
    test_date = datetime(2023, 7, 15)
    
    print(f"\nExtracting from multiple satellites at {test_point}")
    
    # Extract from both satellites
    s2_signature = sentinel2.extract_spectral_signature(test_point, test_date)
    l8_signature = landsat.extract_spectral_signature(test_point, test_date)
    
    results = []
    
    if s2_signature:
        print("\n✅ Sentinel-2 data available")
        s2_analysis = analyzer.analyze_single_signature(s2_signature)
        results.append(("Sentinel-2", s2_analysis))
    
    if l8_signature:
        print("✅ Landsat data available")
        l8_analysis = analyzer.analyze_single_signature(l8_signature)
        results.append(("Landsat", l8_analysis))
    
    if results:
        print("\n📊 Comparative Analysis:")
        for satellite, analysis in results:
            print(f"\n{satellite} Results:")
            print(f"  - Detection Confidence: {analysis.get('detection_confidence', 0)}%")
            print(f"  - Invasive Species Likely: {analysis.get('invasive_species_likely', False)}")
            if 'possible_species' in analysis:
                print(f"  - Possible Species: {', '.join(analysis['possible_species'])}")


if __name__ == "__main__":
    print("🌱 Invasive Species Tracker - Claude-Based Detection Test")
    print("="*60)
    
    try:
        # Run all tests
        test_single_point_analysis()
        test_temporal_analysis()
        test_spatial_context()
        test_combined_analysis()
        
        print("\n✅ All tests completed!")
        
    except Exception as e:
        logger.error(f"Test failed: {str(e)}")
        print(f"\n❌ Test failed: {str(e)}")