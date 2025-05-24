#!/usr/bin/env python3
"""Test Sacramento Delta shoreline areas for aquatic invasive species."""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

from datetime import datetime
from src.gee.satellite_data import Sentinel2Extractor
from src.analysis.spectral_analyzer import ClaudeSpectralAnalyzer
import json

print("🌊 Sacramento Delta Aquatic Invasive Species Detection")
print("="*60)

# Shoreline and marsh locations more likely to have invasive aquatic plants
SHORELINE_LOCATIONS = {
    "Discovery Bay Marina Edge": (-121.5969, 37.9089),  # Marina shoreline
    "Holland Tract Wetland": (-121.5875, 38.0292),     # Wetland area
    "Mildred Island": (-121.5678, 37.9475),            # Known problem area
    "Clifton Court Forebay": (-121.5556, 37.8292),     # Water intake area
    "Old River Mouth": (-121.5783, 37.9231),           # River confluence
}

sentinel2 = Sentinel2Extractor()
analyzer = ClaudeSpectralAnalyzer()

# Test each location
results = []
for name, coords in SHORELINE_LOCATIONS.items():
    print(f"\n📍 Testing: {name}")
    print(f"   Location: {coords[1]:.4f}°N, {coords[0]:.4f}°W")
    
    # Use late summer for peak growth
    date = datetime(2023, 8, 20)
    
    # Extract with larger buffer to capture vegetation edges
    signature = sentinel2.extract_spectral_signature(coords, date, buffer_meters=100)
    
    if signature:
        print(f"   ✅ Image date: {signature.acquisition_date.strftime('%Y-%m-%d')}")
        
        # Quick vegetation check
        if signature.band_values.get('B8') and signature.band_values.get('B4'):
            ndvi = (signature.band_values['B8'] - signature.band_values['B4']) / \
                   (signature.band_values['B8'] + signature.band_values['B4'])
            print(f"   🌱 NDVI: {ndvi:.3f} ({'Vegetation' if ndvi > 0.3 else 'Low/No vegetation'})")
        
        # Analyze for aquatic invasives
        analysis = analyzer.analyze_single_signature(
            signature,
            species_of_interest=[
                "Water Hyacinth (Eichhornia crassipes) - floating aquatic plant",
                "Brazilian Waterweed (Egeria densa) - submerged aquatic plant",
                "Water Primrose (Ludwigia spp.) - emergent aquatic plant",
                "Giant Salvinia (Salvinia molesta) - floating fern"
            ]
        )
        
        confidence = analysis.get('detection_confidence', 0)
        print(f"   🎯 Detection confidence: {confidence}%")
        
        if confidence > 50:
            print(f"   ⚠️ HIGH RISK - Likely invasive species present")
            if analysis.get('possible_species'):
                species_list = analysis['possible_species']
                if isinstance(species_list, list) and len(species_list) > 0:
                    # Handle case where species might be strings or dicts
                    species_names = []
                    for s in species_list[:2]:
                        if isinstance(s, str):
                            species_names.append(s)
                        elif isinstance(s, dict):
                            species_names.append(str(s))
                    if species_names:
                        print(f"   🌿 Species: {', '.join(species_names)}")
        
        results.append({
            'location': name,
            'coordinates': coords,
            'confidence': confidence,
            'analysis': analysis
        })
    else:
        print(f"   ❌ No clear imagery available")

# Summary
print("\n" + "="*60)
print("SUMMARY - Invasive Species Risk Assessment")
print("="*60)

high_risk = [r for r in results if r['confidence'] > 50]
moderate_risk = [r for r in results if 20 < r['confidence'] <= 50]

if high_risk:
    print(f"\n🚨 HIGH RISK AREAS ({len(high_risk)}):")
    for r in high_risk:
        print(f"  • {r['location']}: {r['confidence']}% confidence")
        analysis = r['analysis']
        if analysis.get('anomalies'):
            print(f"    Indicators: {', '.join(analysis['anomalies'][:2])}")

if moderate_risk:
    print(f"\n⚠️ MODERATE RISK AREAS ({len(moderate_risk)}):")
    for r in moderate_risk:
        print(f"  • {r['location']}: {r['confidence']}% confidence")

print("\n📋 Recommendations:")
print("1. Prioritize field surveys at high-risk locations")
print("2. Monitor moderate-risk areas monthly during growing season")
print("3. Consider drone surveys for detailed mapping")
print("4. Coordinate with CA Dept of Boating and Waterways")