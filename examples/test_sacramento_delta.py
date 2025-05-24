#!/usr/bin/env python3
"""Test invasive species detection in Sacramento-San Joaquin Delta."""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from datetime import datetime, timedelta
from src.gee.satellite_data import Sentinel2Extractor, LandsatExtractor
from src.analysis.spectral_analyzer import ClaudeSpectralAnalyzer
from src.utils.logger import get_logger
import json

logger = get_logger(__name__)


# Known invasive species in Sacramento Delta
DELTA_INVASIVE_SPECIES = [
    "Water Hyacinth (Eichhornia crassipes)",
    "Brazilian Waterweed (Egeria densa)", 
    "Water Primrose (Ludwigia spp.)",
    "Giant Salvinia (Salvinia molesta)",
    "Hydrilla (Hydrilla verticillata)",
    "Purple Loosestrife (Lythrum salicaria)",
    "Arundo (Arundo donax)"
]

# Test locations in Sacramento Delta
TEST_LOCATIONS = {
    "Discovery Bay": (-121.6003, 37.9057),  # Known water hyacinth area
    "Franks Tract": (-121.5942, 38.0472),   # State Recreation Area with aquatic weeds
    "Big Break": (-121.7272, 38.0194),      # Regional shoreline with invasives
    "Sherman Island": (-121.7611, 38.0411),  # Agricultural area with levees
    "Bethel Island": (-121.6403, 38.0139)   # Residential area with waterways
}


def test_sacramento_location(location_name: str, coordinates: tuple):
    """Test a specific location in Sacramento Delta."""
    print(f"\n📍 Testing: {location_name}")
    print(f"   Coordinates: {coordinates[1]:.4f}°N, {coordinates[0]:.4f}°W")
    
    sentinel2 = Sentinel2Extractor()
    analyzer = ClaudeSpectralAnalyzer()
    
    # Use summer date for peak vegetation
    test_date = datetime(2023, 8, 15)
    
    # Extract spectral signature
    signature = sentinel2.extract_spectral_signature(coordinates, test_date)
    
    if signature:
        print(f"   ✅ Imagery found: {signature.acquisition_date.strftime('%Y-%m-%d')}")
        print(f"   ☁️ Cloud coverage: {signature.cloud_probability:.1f}%")
        
        # Analyze with Claude
        analysis = analyzer.analyze_single_signature(
            signature,
            species_of_interest=DELTA_INVASIVE_SPECIES
        )
        
        print(f"   🔍 Detection confidence: {analysis.get('detection_confidence', 0)}%")
        print(f"   🌱 Invasive likely: {analysis.get('invasive_species_likely', False)}")
        
        if analysis.get('possible_species'):
            print(f"   🎯 Possible species: {', '.join(analysis['possible_species'])}")
        
        if analysis.get('anomalies'):
            print(f"   ⚠️ Anomalies: {', '.join(analysis['anomalies'])}")
        
        return analysis
    else:
        print("   ❌ No clear imagery available")
        return None


def test_temporal_spread():
    """Test temporal spread at Discovery Bay (known hotspot)."""
    print("\n" + "="*60)
    print("Temporal Analysis: Discovery Bay Water Hyacinth Monitoring")
    print("="*60)
    
    sentinel2 = Sentinel2Extractor()
    analyzer = ClaudeSpectralAnalyzer()
    
    location = TEST_LOCATIONS["Discovery Bay"]
    
    # Monitor growing season (May to October)
    start_date = datetime(2023, 5, 1)
    end_date = datetime(2023, 10, 31)
    
    print(f"\nExtracting temporal data for {location}")
    print(f"Period: {start_date.strftime('%B %Y')} to {end_date.strftime('%B %Y')}")
    
    signatures = sentinel2.extract_temporal_signatures(
        location,
        start_date,
        end_date,
        interval_days=14  # Bi-weekly monitoring
    )
    
    print(f"\n✅ Found {len(signatures)} clear images")
    
    if len(signatures) >= 4:
        # Show acquisition dates
        print("\nAcquisition dates:")
        for i, sig in enumerate(signatures):
            print(f"  {i+1}. {sig.acquisition_date.strftime('%Y-%m-%d')}")
        
        # Analyze temporal patterns
        print("\n🤖 Analyzing growth patterns...")
        temporal_analysis = analyzer.analyze_temporal_sequence(
            signatures,
            species_of_interest=["Water Hyacinth", "Brazilian Waterweed"]
        )
        
        print("\n📊 Temporal Analysis Results:")
        if temporal_analysis.get('change_detected'):
            print("  ✅ Vegetation changes detected")
        if temporal_analysis.get('phenological_match'):
            print("  ✅ Patterns match invasive species phenology")
        if temporal_analysis.get('growth_rate'):
            print(f"  📈 Growth rate: {temporal_analysis['growth_rate']}")
        if temporal_analysis.get('temporal_confidence'):
            print(f"  🎯 Confidence: {temporal_analysis['temporal_confidence']}%")
        
        return temporal_analysis
    else:
        print("❌ Insufficient temporal data")
        return None


def test_spatial_spread():
    """Test spatial spread patterns around Franks Tract."""
    print("\n" + "="*60)
    print("Spatial Analysis: Franks Tract Invasion Patterns")
    print("="*60)
    
    sentinel2 = Sentinel2Extractor()
    analyzer = ClaudeSpectralAnalyzer()
    
    center_point = TEST_LOCATIONS["Franks Tract"]
    test_date = datetime(2023, 8, 15)
    
    print(f"\nAnalyzing spatial patterns around Franks Tract")
    print(f"Center: {center_point[1]:.4f}°N, {center_point[0]:.4f}°W")
    
    # Extract spatial context (500m radius)
    context = sentinel2.extract_spatial_context(
        center_point,
        test_date,
        radius_meters=500,
        sample_points=12  # Sample every 30 degrees
    )
    
    print(f"\n✅ Spatial data extracted:")
    print(f"  - Center samples: {len(context['center'])}")
    print(f"  - Surrounding samples: {len(context['surrounding'])}")
    
    if context['center'] and len(context['surrounding']) >= 6:
        # Analyze spatial patterns
        print("\n🤖 Analyzing invasion patterns...")
        spatial_analysis = analyzer.analyze_spatial_context(
            context['center'],
            context['surrounding'],
            species_of_interest=["Water Hyacinth", "Brazilian Waterweed", "Water Primrose"]
        )
        
        print("\n📊 Spatial Analysis Results:")
        if spatial_analysis.get('spatial_heterogeneity'):
            print(f"  🔀 Heterogeneity: {spatial_analysis['spatial_heterogeneity']}")
        if spatial_analysis.get('spread_direction'):
            print(f"  ➡️ Spread direction: {spatial_analysis['spread_direction']}")
        if spatial_analysis.get('invasion_stage'):
            print(f"  📍 Invasion stage: {spatial_analysis['invasion_stage']}")
        if spatial_analysis.get('edge_effects'):
            print(f"  🔲 Edge effects: {spatial_analysis['edge_effects']}")
        
        return spatial_analysis
    else:
        print("❌ Insufficient spatial data")
        return None


def generate_summary_report(results: dict):
    """Generate a summary report of all analyses."""
    print("\n" + "="*60)
    print("Sacramento Delta Invasive Species Detection Summary")
    print("="*60)
    
    # Count detections
    high_risk_locations = []
    moderate_risk_locations = []
    
    for location, analysis in results.items():
        if analysis and analysis.get('detection_confidence', 0) > 70:
            high_risk_locations.append(location)
        elif analysis and analysis.get('detection_confidence', 0) > 40:
            moderate_risk_locations.append(location)
    
    print(f"\n🚨 High Risk Locations ({len(high_risk_locations)}):")
    for loc in high_risk_locations:
        confidence = results[loc].get('detection_confidence', 0)
        species = results[loc].get('possible_species', [])
        print(f"  - {loc}: {confidence}% confidence")
        if species:
            print(f"    Likely species: {', '.join(species[:2])}")
    
    print(f"\n⚠️ Moderate Risk Locations ({len(moderate_risk_locations)}):")
    for loc in moderate_risk_locations:
        confidence = results[loc].get('detection_confidence', 0)
        print(f"  - {loc}: {confidence}% confidence")
    
    print("\n📋 Recommendations:")
    print("  1. Priority monitoring: Focus on high-risk locations")
    print("  2. Field validation: Ground-truth the detected areas")
    print("  3. Treatment planning: Prepare for mechanical/chemical control")
    print("  4. Prevention: Monitor waterways connecting to clean areas")


if __name__ == "__main__":
    print("🌊 Sacramento-San Joaquin Delta Invasive Species Detection")
    print("="*60)
    print("Target species: Water Hyacinth, Brazilian Waterweed, Water Primrose")
    print("Analysis date: Summer 2023 (peak growing season)")
    
    try:
        # Test all locations
        print("\n" + "="*60)
        print("Location-by-Location Analysis")
        print("="*60)
        
        location_results = {}
        for name, coords in TEST_LOCATIONS.items():
            result = test_sacramento_location(name, coords)
            location_results[name] = result
        
        # Temporal analysis
        temporal_result = test_temporal_spread()
        
        # Spatial analysis
        spatial_result = test_spatial_spread()
        
        # Generate summary
        generate_summary_report(location_results)
        
        print("\n✅ Sacramento Delta analysis complete!")
        
    except Exception as e:
        logger.error(f"Analysis failed: {str(e)}")
        print(f"\n❌ Analysis failed: {str(e)}")