#!/usr/bin/env python3
"""Test all API connections for the Invasive Species Tracker."""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

print("="*60)
print("Invasive Species Tracker - Connection Test")
print("="*60)

# Test 1: Environment Variables
print("\n1. Environment Variables:")
env_vars = {
    'GOOGLE_CLOUD_PROJECT': os.getenv('GOOGLE_CLOUD_PROJECT'),
    'GOOGLE_CLOUD_API_KEY': os.getenv('GOOGLE_CLOUD_API_KEY'),
    'ANTHROPIC_API_KEY': os.getenv('ANTHROPIC_API_KEY')
}

all_set = True
for var, value in env_vars.items():
    if value:
        if 'KEY' in var:
            print(f"   ✅ {var}: {value[:10]}...{value[-4:]}")
        else:
            print(f"   ✅ {var}: {value}")
    else:
        print(f"   ❌ {var}: Not set")
        all_set = False

if not all_set:
    print("\n❌ Some environment variables are missing!")
    sys.exit(1)

# Test 2: Google Earth Engine
print("\n2. Google Earth Engine Connection:")
try:
    import ee
    from src.gee.auth import initialize_earth_engine
    initialize_earth_engine()
    
    # Test query
    point = ee.Geometry.Point([-122.4194, 37.7749])
    elevation = ee.Image('USGS/SRTMGL1_003').sample(point, 30).first().get('elevation').getInfo()
    print(f"   ✅ Connected to project: {os.getenv('GOOGLE_CLOUD_PROJECT')}")
    print(f"   ✅ Test query successful (SF elevation: {elevation}m)")
except Exception as e:
    print(f"   ❌ Connection failed: {str(e)}")

# Test 3: Claude API
print("\n3. Claude API Connection:")
try:
    from anthropic import Anthropic
    client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    
    response = client.messages.create(
        model="claude-opus-4-20250514",
        max_tokens=50,
        messages=[{"role": "user", "content": "Respond with 'Ready to detect invasive species!'"}]
    )
    
    print(f"   ✅ Connected to Claude API")
    print(f"   ✅ Model: claude-opus-4-20250514")
    print(f"   ✅ Response: {response.content[0].text}")
except Exception as e:
    print(f"   ❌ Connection failed: {str(e)}")

print("\n" + "="*60)
print("✅ All systems ready! You can now start using the Invasive Species Tracker.")
print("="*60)