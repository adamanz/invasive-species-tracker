#!/usr/bin/env python3
"""Quick test to check Sentinel-2 imagery availability in Sacramento Delta."""

import ee
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

# Initialize Earth Engine
ee.Initialize(project=os.getenv('GOOGLE_CLOUD_PROJECT'))

# Test location in Sacramento Delta
point = ee.Geometry.Point([-121.6003, 37.9057])  # Discovery Bay

# Check Sentinel-2 availability
collection = ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED') \
    .filterBounds(point) \
    .filterDate('2023-07-01', '2023-09-30') \
    .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 50))

count = collection.size()
print(f"Found {count.getInfo()} Sentinel-2 images for Sacramento Delta (Jul-Sep 2023)")

# Get first image info
first = collection.first()
if first.getInfo():
    props = first.getInfo()['properties']
    print(f"\nFirst image properties:")
    print(f"  Date: {datetime.fromtimestamp(props.get('system:time_start', 0)/1000)}")
    print(f"  Cloud %: {props.get('CLOUDY_PIXEL_PERCENTAGE', 'N/A')}")
    print(f"  Index: {props.get('system:index', 'N/A')}")
    
    # Test band extraction
    values = first.select(['B4', 'B8']).reduceRegion(
        reducer=ee.Reducer.mean(),
        geometry=point.buffer(30),
        scale=10
    ).getInfo()
    print(f"  B4 (Red): {values.get('B4', 'N/A')}")
    print(f"  B8 (NIR): {values.get('B8', 'N/A')}")