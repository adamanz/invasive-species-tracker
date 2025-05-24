# Yellowstone Invasive Species Analysis - Image Download Manifest

**Generated**: 2025-05-24 18:24:12
**Total Files**: 25

## Download Instructions

1. Check your Google Drive for 'yellowstone_analysis' folder
2. Download all files to your local system
3. Verify file integrity using the checksums below

## File Categories

### Sentinel-2 Annual Composites (2019-2024)
- 10m resolution, 10 spectral bands
- Growing season composites (June-September)
- Cloud-free median composites

### Landsat Composites (2019-2024)
- 30m resolution, 6 spectral bands
- For comparison and long-term analysis
- Combined Landsat 8 & 9 data

### Monitoring Site Details
- 10 key locations across Yellowstone
- 1km radius around each site
- High-resolution 2024 imagery

### Change Detection Pairs
- Pre-fire (2019), Post-fire (2022), Current (2024)
- Optimized for temporal change analysis
- Key spectral bands for vegetation monitoring

## File List

```
 1. yellowstone_sentinel2_2019_composite.tif
 2. yellowstone_sentinel2_2020_composite.tif
 3. yellowstone_sentinel2_2021_composite.tif
 4. yellowstone_sentinel2_2022_composite.tif
 5. yellowstone_sentinel2_2023_composite.tif
 6. yellowstone_sentinel2_2024_composite.tif
 7. yellowstone_landsat_2019_composite.tif
 8. yellowstone_landsat_2020_composite.tif
 9. yellowstone_landsat_2021_composite.tif
10. yellowstone_landsat_2022_composite.tif
11. yellowstone_landsat_2023_composite.tif
12. yellowstone_landsat_2024_composite.tif
13. yellowstone_site_Old_Faithful_2024.tif
14. yellowstone_site_Norris_Geyser_2024.tif
15. yellowstone_site_Hayden_Valley_2024.tif
16. yellowstone_site_Lamar_Valley_2024.tif
17. yellowstone_site_South_Entrance_2024.tif
18. yellowstone_site_West_Thumb_2024.tif
19. yellowstone_site_Tower_Junction_2024.tif
20. yellowstone_site_Madison_Junction_2024.tif
21. yellowstone_site_Fishing_Bridge_2024.tif
22. yellowstone_site_Grant_Village_2024.tif
23. yellowstone_change_pre_fire.tif
24. yellowstone_change_post_fire.tif
25. yellowstone_change_current.tif
```

## Usage Notes

- All images are in GeoTIFF format with embedded CRS
- Coordinate system: EPSG:4326 (WGS84)
- Pixel values are surface reflectance (scaled)
- Use QGIS, ArcGIS, or Python (rasterio) for analysis

## Band Information

### Sentinel-2 Bands
- B2: Blue (490nm)
- B3: Green (560nm)
- B4: Red (665nm)
- B5: Red Edge 1 (705nm)
- B6: Red Edge 2 (740nm)
- B7: Red Edge 3 (783nm)
- B8: NIR (842nm)
- B8A: Red Edge 4 (865nm)
- B11: SWIR 1 (1610nm)
- B12: SWIR 2 (2190nm)

### Landsat Bands
- SR_B2: Blue (482nm)
- SR_B3: Green (562nm)
- SR_B4: Red (655nm)
- SR_B5: NIR (865nm)
- SR_B6: SWIR 1 (1609nm)
- SR_B7: SWIR 2 (2201nm)