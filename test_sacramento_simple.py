#!/usr/bin/env python3
"""Simple test of Sacramento Delta invasive species detection."""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

from datetime import datetime
from src.gee.satellite_data import Sentinel2Extractor
from src.analysis.spectral_analyzer import ClaudeSpectralAnalyzer
import json

print("🌊 Testing Sacramento Delta - Discovery Bay")
print("Known location for Water Hyacinth")
print("="*50)

# Initialize
sentinel2 = Sentinel2Extractor()
analyzer = ClaudeSpectralAnalyzer()

# Discovery Bay coordinates
location = (-121.6003, 37.9057)
date = datetime(2023, 8, 15)  # Peak growing season

print(f"\n📍 Location: {location[1]:.4f}°N, {location[0]:.4f}°W")
print(f"📅 Target date: {date.strftime('%Y-%m-%d')}")

# Extract spectral signature
print("\n🛰️ Extracting Sentinel-2 data...")
signature = sentinel2.extract_spectral_signature(location, date, buffer_meters=50)

if signature:
    print(f"✅ Image found: {signature.acquisition_date.strftime('%Y-%m-%d')}")
    print(f"☁️ Cloud coverage: {signature.cloud_probability:.1f}%")
    print(f"🔢 Band values extracted: {len([v for v in signature.band_values.values() if v is not None])}/{len(signature.band_names)}")
    
    # Show spectral values
    print("\n📊 Spectral Signature:")
    for band, value in signature.band_values.items():
        if value is not None:
            print(f"  {band}: {value:.4f}")
    
    # Analyze with Claude
    print("\n🤖 Sending to Claude for analysis...")
    print("Looking for: Water Hyacinth, Brazilian Waterweed")
    
    analysis = analyzer.analyze_single_signature(
        signature,
        species_of_interest=[
            "Water Hyacinth (Eichhornia crassipes)",
            "Brazilian Waterweed (Egeria densa)"
        ]
    )
    
    print("\n🎯 Analysis Results:")
    print(f"Detection confidence: {analysis.get('detection_confidence', 0)}%")
    print(f"Invasive species likely: {analysis.get('invasive_species_likely', False)}")
    
    if analysis.get('possible_species'):
        print(f"Possible species: {', '.join(analysis['possible_species'])}")
    
    if analysis.get('vegetation_health'):
        print(f"Vegetation health: {analysis['vegetation_health']}")
    
    if analysis.get('reasoning'):
        print(f"\nReasoning: {analysis['reasoning'][:200]}...")
        
else:
    print("❌ No imagery found for this location and date")

print("\n" + "="*50)
print("Test complete!")