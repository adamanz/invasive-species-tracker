#!/usr/bin/env python3
"""Generate Yellowstone satellite images for invasive species analysis."""

import ee
import os
from datetime import datetime
from pathlib import Path
import requests
from urllib.parse import urlencode

# Initialize Earth Engine
try:
    ee.Initialize()
    print("✅ Earth Engine initialized successfully")
except Exception as e:
    print(f"❌ Earth Engine initialization failed: {e}")
    print("Please run 'ee.Authenticate()' first")
    exit(1)

# Yellowstone National Park boundaries
YELLOWSTONE_AOI = ee.Geometry.Rectangle([-111.2, 44.1, -109.8, 45.1])

# Output directory
OUTPUT_DIR = Path("outputs/satellite_images")
OUTPUT_DIR.mkdir(exist_ok=True)

def mask_s2_clouds(image):
    """Mask clouds in Sentinel-2 imagery."""
    qa = image.select('QA60')
    cloud_bit_mask = 1 << 10
    cirrus_bit_mask = 1 << 11
    mask = (qa.bitwiseAnd(cloud_bit_mask).eq(0)
           .And(qa.bitwiseAnd(cirrus_bit_mask).eq(0)))
    return image.updateMask(mask).divide(10000)

def create_yellowstone_composite(year, season="summer"):
    """Create a Yellowstone composite for a specific year."""
    print(f"Creating {year} {season} composite...")
    
    # Define date ranges based on season
    if season == "summer":
        start_date = f'{year}-06-01'
        end_date = f'{year}-09-30'
    else:
        start_date = f'{year}-01-01'
        end_date = f'{year}-12-31'
    
    # Get Sentinel-2 collection
    collection = (ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
                  .filterBounds(YELLOWSTONE_AOI)
                  .filterDate(start_date, end_date)
                  .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 20))
                  .map(mask_s2_clouds))
    
    # Create median composite
    composite = collection.median()
    
    return composite

def export_image_to_drive(image, description, folder="yellowstone_analysis"):
    """Export image to Google Drive."""
    task = ee.batch.Export.image.toDrive(
        image=image,
        description=description,
        folder=folder,
        region=YELLOWSTONE_AOI,
        scale=10,
        maxPixels=1e9,
        fileFormat='GeoTIFF'
    )
    task.start()
    print(f"  ✅ Export started: {description}")
    return task

def get_image_url(image, vis_params, region):
    """Get a URL for visualizing the image."""
    try:
        # Get the image URL
        url = image.getThumbURL({
            'region': region,
            'dimensions': 512,
            'format': 'png',
            **vis_params
        })
        return url
    except Exception as e:
        print(f"  ❌ Failed to get image URL: {e}")
        return None

def download_image(url, output_path):
    """Download image from URL."""
    try:
        response = requests.get(url)
        if response.status_code == 200:
            with open(output_path, 'wb') as f:
                f.write(response.content)
            print(f"  ✅ Downloaded: {output_path}")
            return True
        else:
            print(f"  ❌ Download failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"  ❌ Download error: {e}")
        return False

def create_visualization_image(image, description, bands=['B4', 'B3', 'B2'], 
                             min_val=0, max_val=0.3):
    """Create a visualization image and save locally."""
    
    # Visualization parameters
    vis_params = {
        'bands': bands,
        'min': min_val,
        'max': max_val,
        'gamma': 1.4
    }
    
    # Get image URL
    url = get_image_url(image, vis_params, YELLOWSTONE_AOI)
    
    if url:
        # Save as PNG
        output_path = OUTPUT_DIR / f"{description.lower().replace(' ', '_')}.png"
        
        if download_image(url, output_path):
            return str(output_path)
    
    return None

def generate_yellowstone_imagery():
    """Generate all Yellowstone satellite imagery."""
    print("🛰️ Generating Yellowstone Satellite Imagery")
    print("="*50)
    
    # Create composite images for key years
    years = [2019, 2022, 2024]
    
    for year in years:
        print(f"\n📅 Processing {year}...")
        
        try:
            # Create composite
            composite = create_yellowstone_composite(year)
            
            # True color visualization
            desc_rgb = f"yellowstone_sentinel2_{year}_composite_rgb"
            create_visualization_image(
                composite, 
                desc_rgb,
                bands=['B4', 'B3', 'B2'],
                min_val=0,
                max_val=0.3
            )
            
            # False color (vegetation) visualization  
            desc_nir = f"yellowstone_sentinel2_{year}_composite_nir"
            create_visualization_image(
                composite,
                desc_nir, 
                bands=['B8', 'B4', 'B3'],
                min_val=0,
                max_val=0.4
            )
            
            # Export full resolution to Drive
            export_image_to_drive(composite, f"yellowstone_sentinel2_{year}_composite")
            
        except Exception as e:
            print(f"  ❌ Failed to process {year}: {e}")
    
    # Create specific site images
    print(f"\n📍 Generating site-specific imagery...")
    
    # Define key monitoring sites
    sites = {
        "Lamar_Valley": ee.Geometry.Point([-110.2240, 44.8980]).buffer(1000),
        "Hayden_Valley": ee.Geometry.Point([-110.4680, 44.6600]).buffer(1000),
        "South_Entrance": ee.Geometry.Point([-110.6660, 44.1380]).buffer(1000)
    }
    
    # Get 2024 composite for site imagery
    composite_2024 = create_yellowstone_composite(2024)
    
    for site_name, site_geom in sites.items():
        print(f"  Processing {site_name}...")
        
        try:
            # Clip to site
            site_image = composite_2024.clip(site_geom)
            
            # Create visualization
            desc_site = f"yellowstone_site_{site_name}_2024"
            create_visualization_image(
                site_image,
                desc_site,
                bands=['B8', 'B4', 'B3'],  # False color for vegetation
                min_val=0,
                max_val=0.4
            )
            
        except Exception as e:
            print(f"  ❌ Failed to process {site_name}: {e}")
    
    print("\n✅ Image generation complete!")
    print(f"📁 Check outputs in: {OUTPUT_DIR}")
    print("📥 Full resolution images will be available in Google Drive")

if __name__ == "__main__":
    generate_yellowstone_imagery()