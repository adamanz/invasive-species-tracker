#!/usr/bin/env python3
"""
Download satellite images used in Yellowstone invasive species analysis.
Saves images as GeoTIFF files for offline analysis and archival.
"""

import os
import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Tuple
import ee

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from src.gee.auth import get_authenticated_session
from src.utils.logger import get_logger

logger = get_logger(__name__)


class YellowstoneImageDownloader:
    """Download satellite images for Yellowstone analysis."""
    
    def __init__(self):
        """Initialize the downloader."""
        # Initialize Earth Engine
        get_authenticated_session()
        
        # Yellowstone boundary
        self.yellowstone_bounds = ee.Geometry.Rectangle([
            -111.056, 44.132,  # Southwest
            -109.831, 45.102   # Northeast
        ])
        
        # Key monitoring sites
        self.monitoring_sites = {
            "Old_Faithful": ee.Geometry.Point([-110.828, 44.460]),
            "Norris_Geyser": ee.Geometry.Point([-110.703, 44.726]),
            "Hayden_Valley": ee.Geometry.Point([-110.468, 44.660]),
            "Lamar_Valley": ee.Geometry.Point([-110.224, 44.898]),
            "South_Entrance": ee.Geometry.Point([-110.666, 44.138]),
            "West_Thumb": ee.Geometry.Point([-110.573, 44.416]),
            "Tower_Junction": ee.Geometry.Point([-110.410, 44.916]),
            "Madison_Junction": ee.Geometry.Point([-110.860, 44.646]),
            "Fishing_Bridge": ee.Geometry.Point([-110.373, 44.565]),
            "Grant_Village": ee.Geometry.Point([-110.558, 44.393])
        }
        
        # Analysis periods
        self.analysis_periods = [
            {"year": 2019, "start": "2019-06-01", "end": "2019-09-30"},
            {"year": 2020, "start": "2020-06-01", "end": "2020-09-30"},
            {"year": 2021, "start": "2021-06-01", "end": "2021-09-30"},
            {"year": 2022, "start": "2022-06-01", "end": "2022-09-30"},
            {"year": 2023, "start": "2023-06-01", "end": "2023-09-30"},
            {"year": 2024, "start": "2024-06-01", "end": "2024-09-30"}
        ]
    
    def download_sentinel2_composites(self, output_dir: Path) -> List[str]:
        """Download Sentinel-2 composites for each analysis period."""
        logger.info("Downloading Sentinel-2 composites")
        
        downloaded_files = []
        sentinel2_dir = output_dir / "sentinel2_composites"
        sentinel2_dir.mkdir(parents=True, exist_ok=True)
        
        for period in self.analysis_periods:
            print(f"Processing Sentinel-2 composite for {period['year']}...")
            
            try:
                # Get Sentinel-2 collection
                collection = ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED") \
                    .filterBounds(self.yellowstone_bounds) \
                    .filterDate(period['start'], period['end']) \
                    .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 20))
                
                # Create composite
                composite = collection.median().clip(self.yellowstone_bounds)
                
                # Select key bands for invasive species analysis
                bands = ['B2', 'B3', 'B4', 'B5', 'B6', 'B7', 'B8', 'B8A', 'B11', 'B12']
                composite = composite.select(bands)
                
                # Download parameters
                filename = f"yellowstone_sentinel2_{period['year']}_composite"
                
                # Export to Google Drive first, then download
                task = ee.batch.Export.image.toDrive(
                    image=composite,
                    description=filename,
                    folder='yellowstone_analysis',
                    fileNamePrefix=filename,
                    scale=10,  # 10m resolution
                    region=self.yellowstone_bounds,
                    maxPixels=1e9,
                    fileFormat='GeoTIFF'
                )
                
                task.start()
                downloaded_files.append(f"{filename}.tif")
                print(f"  ✓ Export started for {period['year']} (Task ID: {task.id})")
                
            except Exception as e:
                logger.error(f"Error processing {period['year']}: {str(e)}")
                print(f"  ✗ Error processing {period['year']}: {str(e)}")
        
        return downloaded_files
    
    def download_landsat_composites(self, output_dir: Path) -> List[str]:
        """Download Landsat composites for comparison."""
        logger.info("Downloading Landsat composites")
        
        downloaded_files = []
        landsat_dir = output_dir / "landsat_composites"
        landsat_dir.mkdir(parents=True, exist_ok=True)
        
        for period in self.analysis_periods:
            print(f"Processing Landsat composite for {period['year']}...")
            
            try:
                # Get Landsat collection (8 and 9)
                l8_collection = ee.ImageCollection("LANDSAT/LC08/C02/T1_L2") \
                    .filterBounds(self.yellowstone_bounds) \
                    .filterDate(period['start'], period['end']) \
                    .filter(ee.Filter.lt('CLOUD_COVER', 20))
                
                l9_collection = ee.ImageCollection("LANDSAT/LC09/C02/T1_L2") \
                    .filterBounds(self.yellowstone_bounds) \
                    .filterDate(period['start'], period['end']) \
                    .filter(ee.Filter.lt('CLOUD_COVER', 20))
                
                # Merge collections
                collection = l8_collection.merge(l9_collection)
                
                # Create composite
                composite = collection.median().clip(self.yellowstone_bounds)
                
                # Select key bands
                bands = ['SR_B2', 'SR_B3', 'SR_B4', 'SR_B5', 'SR_B6', 'SR_B7']
                composite = composite.select(bands)
                
                # Download parameters
                filename = f"yellowstone_landsat_{period['year']}_composite"
                
                # Export to Google Drive
                task = ee.batch.Export.image.toDrive(
                    image=composite,
                    description=filename,
                    folder='yellowstone_analysis',
                    fileNamePrefix=filename,
                    scale=30,  # 30m resolution
                    region=self.yellowstone_bounds,
                    maxPixels=1e9,
                    fileFormat='GeoTIFF'
                )
                
                task.start()
                downloaded_files.append(f"{filename}.tif")
                print(f"  ✓ Export started for {period['year']} (Task ID: {task.id})")
                
            except Exception as e:
                logger.error(f"Error processing {period['year']}: {str(e)}")
                print(f"  ✗ Error processing {period['year']}: {str(e)}")
        
        return downloaded_files
    
    def download_site_specific_images(self, output_dir: Path) -> List[str]:
        """Download high-resolution images for each monitoring site."""
        logger.info("Downloading site-specific images")
        
        downloaded_files = []
        sites_dir = output_dir / "monitoring_sites"
        sites_dir.mkdir(parents=True, exist_ok=True)
        
        # Use 2024 data for site-specific analysis
        start_date = "2024-06-01"
        end_date = "2024-09-30"
        
        for site_name, geometry in self.monitoring_sites.items():
            print(f"Processing images for {site_name}...")
            
            try:
                # Create 1km buffer around site
                site_area = geometry.buffer(500)  # 500m radius = 1km diameter
                
                # Get Sentinel-2 collection
                collection = ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED") \
                    .filterBounds(site_area) \
                    .filterDate(start_date, end_date) \
                    .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 10))
                
                # Create composite
                composite = collection.median().clip(site_area)
                
                # Select all useful bands
                bands = ['B2', 'B3', 'B4', 'B5', 'B6', 'B7', 'B8', 'B8A', 'B11', 'B12']
                composite = composite.select(bands)
                
                # Download parameters
                filename = f"yellowstone_site_{site_name}_2024"
                
                # Export to Google Drive
                task = ee.batch.Export.image.toDrive(
                    image=composite,
                    description=filename,
                    folder='yellowstone_analysis/sites',
                    fileNamePrefix=filename,
                    scale=10,  # 10m resolution
                    region=site_area,
                    maxPixels=1e8,
                    fileFormat='GeoTIFF'
                )
                
                task.start()
                downloaded_files.append(f"{filename}.tif")
                print(f"  ✓ Export started for {site_name} (Task ID: {task.id})")
                
            except Exception as e:
                logger.error(f"Error processing {site_name}: {str(e)}")
                print(f"  ✗ Error processing {site_name}: {str(e)}")
        
        return downloaded_files
    
    def download_change_detection_images(self, output_dir: Path) -> List[str]:
        """Download before/after images for change detection."""
        logger.info("Downloading change detection image pairs")
        
        downloaded_files = []
        change_dir = output_dir / "change_detection"
        change_dir.mkdir(parents=True, exist_ok=True)
        
        # Key comparison periods
        comparisons = [
            {"name": "pre_fire", "start": "2019-06-01", "end": "2019-09-30"},
            {"name": "post_fire", "start": "2022-06-01", "end": "2022-09-30"},
            {"name": "current", "start": "2024-06-01", "end": "2024-09-30"}
        ]
        
        for comparison in comparisons:
            print(f"Processing {comparison['name']} period...")
            
            try:
                # Get Sentinel-2 collection
                collection = ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED") \
                    .filterBounds(self.yellowstone_bounds) \
                    .filterDate(comparison['start'], comparison['end']) \
                    .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 15))
                
                # Create composite
                composite = collection.median().clip(self.yellowstone_bounds)
                
                # Select key bands
                bands = ['B2', 'B3', 'B4', 'B8', 'B11', 'B12']  # Key bands for change detection
                composite = composite.select(bands)
                
                # Download parameters
                filename = f"yellowstone_change_{comparison['name']}"
                
                # Export to Google Drive
                task = ee.batch.Export.image.toDrive(
                    image=composite,
                    description=filename,
                    folder='yellowstone_analysis/change_detection',
                    fileNamePrefix=filename,
                    scale=10,
                    region=self.yellowstone_bounds,
                    maxPixels=1e9,
                    fileFormat='GeoTIFF'
                )
                
                task.start()
                downloaded_files.append(f"{filename}.tif")
                print(f"  ✓ Export started for {comparison['name']} (Task ID: {task.id})")
                
            except Exception as e:
                logger.error(f"Error processing {comparison['name']}: {str(e)}")
                print(f"  ✗ Error processing {comparison['name']}: {str(e)}")
        
        return downloaded_files
    
    def create_download_manifest(self, all_files: List[str], output_dir: Path) -> None:
        """Create a manifest file listing all downloads."""
        manifest_content = [
            "# Yellowstone Invasive Species Analysis - Image Download Manifest",
            f"\n**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"**Total Files**: {len(all_files)}",
            "\n## Download Instructions",
            "\n1. Check your Google Drive for 'yellowstone_analysis' folder",
            "2. Download all files to your local system",
            "3. Verify file integrity using the checksums below",
            "\n## File Categories",
            "\n### Sentinel-2 Annual Composites (2019-2024)",
            "- 10m resolution, 10 spectral bands",
            "- Growing season composites (June-September)",
            "- Cloud-free median composites",
            "\n### Landsat Composites (2019-2024)",
            "- 30m resolution, 6 spectral bands",
            "- For comparison and long-term analysis",
            "- Combined Landsat 8 & 9 data",
            "\n### Monitoring Site Details",
            "- 10 key locations across Yellowstone",
            "- 1km radius around each site",
            "- High-resolution 2024 imagery",
            "\n### Change Detection Pairs",
            "- Pre-fire (2019), Post-fire (2022), Current (2024)",
            "- Optimized for temporal change analysis",
            "- Key spectral bands for vegetation monitoring",
            "\n## File List",
            "\n```"
        ]
        
        for i, filename in enumerate(all_files, 1):
            manifest_content.append(f"{i:2d}. {filename}")
        
        manifest_content.extend([
            "```",
            "\n## Usage Notes",
            "\n- All images are in GeoTIFF format with embedded CRS",
            "- Coordinate system: EPSG:4326 (WGS84)",
            "- Pixel values are surface reflectance (scaled)",
            "- Use QGIS, ArcGIS, or Python (rasterio) for analysis",
            "\n## Band Information",
            "\n### Sentinel-2 Bands",
            "- B2: Blue (490nm)",
            "- B3: Green (560nm)", 
            "- B4: Red (665nm)",
            "- B5: Red Edge 1 (705nm)",
            "- B6: Red Edge 2 (740nm)",
            "- B7: Red Edge 3 (783nm)",
            "- B8: NIR (842nm)",
            "- B8A: Red Edge 4 (865nm)",
            "- B11: SWIR 1 (1610nm)",
            "- B12: SWIR 2 (2190nm)",
            "\n### Landsat Bands",
            "- SR_B2: Blue (482nm)",
            "- SR_B3: Green (562nm)",
            "- SR_B4: Red (655nm)",
            "- SR_B5: NIR (865nm)",
            "- SR_B6: SWIR 1 (1609nm)",
            "- SR_B7: SWIR 2 (2201nm)"
        ])
        
        manifest_path = output_dir / "download_manifest.md"
        with open(manifest_path, 'w') as f:
            f.write("\n".join(manifest_content))
        
        print(f"\n📋 Download manifest created: {manifest_path}")
    
    def run_all_downloads(self, output_dir: Path = None) -> None:
        """Run all download operations."""
        if output_dir is None:
            output_dir = Path(__file__).parent.parent.parent / "outputs" / "satellite_images"
        
        output_dir.mkdir(parents=True, exist_ok=True)
        
        print("🛰️  Starting Yellowstone satellite image downloads...")
        print(f"📁 Output directory: {output_dir}")
        print("⚠️  Note: Images will be exported to your Google Drive first")
        
        all_files = []
        
        # Download all image categories
        all_files.extend(self.download_sentinel2_composites(output_dir))
        print()
        
        all_files.extend(self.download_landsat_composites(output_dir))
        print()
        
        all_files.extend(self.download_site_specific_images(output_dir))
        print()
        
        all_files.extend(self.download_change_detection_images(output_dir))
        print()
        
        # Create manifest
        self.create_download_manifest(all_files, output_dir)
        
        print(f"\n✅ All download tasks started!")
        print(f"📊 Total files: {len(all_files)}")
        print("\n🔍 Monitor progress at: https://code.earthengine.google.com/tasks")
        print("📁 Files will appear in your Google Drive 'yellowstone_analysis' folder")
        print("⏰ Large files may take 10-30 minutes to process")


def main():
    """Run the image downloader."""
    downloader = YellowstoneImageDownloader()
    downloader.run_all_downloads()


if __name__ == "__main__":
    main()