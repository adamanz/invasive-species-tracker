#!/usr/bin/env python3
"""
Yellowstone National Park Invasive Species Analysis
Analyzes multiple invasive species across Yellowstone from 2019-2024
"""

import ee
import os
import sys
from datetime import datetime
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from src.detector import InvasiveSpeciesDetector

# Initialize Earth Engine
try:
    ee.Initialize(project=os.getenv('GOOGLE_CLOUD_PROJECT'))
except Exception as e:
    print(f"Error initializing Earth Engine: {e}")
    print("Please run 'earthengine authenticate' first")
    sys.exit(1)

def create_yellowstone_boundary():
    """
    Create Yellowstone National Park boundary geometry
    Using approximate coordinates for the park boundary
    """
    # Yellowstone approximate bounding box
    # Northwest: 45.110°N, 111.167°W
    # Northeast: 45.110°N, 109.817°W  
    # Southeast: 44.137°N, 109.817°W
    # Southwest: 44.137°N, 111.167°W
    
    coords = [
        [-111.167, 45.110],  # NW
        [-109.817, 45.110],  # NE
        [-109.817, 44.137],  # SE
        [-111.167, 44.137],  # SW
        [-111.167, 45.110]   # Close polygon
    ]
    
    return ee.Geometry.Polygon(coords)

def analyze_yellowstone_invasives():
    """
    Run comprehensive invasive species analysis for Yellowstone
    """
    print("=== Yellowstone National Park Invasive Species Analysis ===")
    print(f"Analysis Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # Create detector instance
    detector = InvasiveSpeciesDetector()
    
    # Define Yellowstone boundary
    yellowstone_aoi = create_yellowstone_boundary()
    
    # Define time periods for analysis
    time_periods = [
        {'year': 2019, 'start': '2019-06-01', 'end': '2019-09-30'},
        {'year': 2020, 'start': '2020-06-01', 'end': '2020-09-30'},
        {'year': 2021, 'start': '2021-06-01', 'end': '2021-09-30'},
        {'year': 2022, 'start': '2022-06-01', 'end': '2022-09-30'},
        {'year': 2023, 'start': '2023-06-01', 'end': '2023-09-30'},
        {'year': 2024, 'start': '2024-06-01', 'end': '2024-09-30'}
    ]
    
    # Target invasive species for Yellowstone
    target_species = [
        {
            'name': 'Cheatgrass',
            'scientific': 'Bromus tectorum',
            'habitat': 'dry grasslands, disturbed areas',
            'season': 'early summer growth, brown by July'
        },
        {
            'name': 'Canada thistle',
            'scientific': 'Cirsium arvense',
            'habitat': 'meadows, roadsides, riparian areas',
            'season': 'purple flowers June-September'
        },
        {
            'name': 'Spotted knapweed',
            'scientific': 'Centaurea stoebe',
            'habitat': 'dry grasslands, roadsides',
            'season': 'pink-purple flowers July-September'
        },
        {
            'name': 'Leafy spurge',
            'scientific': 'Euphorbia esula',
            'habitat': 'grasslands, riparian areas',
            'season': 'yellow-green flowers May-July'
        },
        {
            'name': 'Dalmatian toadflax',
            'scientific': 'Linaria dalmatica',
            'habitat': 'disturbed sites, roadsides',
            'season': 'yellow flowers June-September'
        }
    ]
    
    # Store all results
    all_results = {
        'metadata': {
            'park': 'Yellowstone National Park',
            'analysis_date': datetime.now().isoformat(),
            'area_km2': yellowstone_aoi.area().divide(1e6).getInfo(),
            'time_periods': time_periods,
            'target_species': target_species
        },
        'temporal_analysis': {},
        'species_detections': {},
        'risk_assessments': {}
    }
    
    # Analyze each time period
    print("Analyzing temporal patterns...")
    for period in time_periods:
        print(f"\nProcessing {period['year']} ({period['start']} to {period['end']})...")
        
        try:
            # Run detection for this period
            results = detector.detect(
                aoi=yellowstone_aoi,
                start_date=period['start'],
                end_date=period['end']
            )
            
            # Store results
            all_results['temporal_analysis'][period['year']] = results
            
            # Extract key metrics
            if 'ai_analysis' in results and 'invasive_likelihood' in results['ai_analysis']:
                likelihood = results['ai_analysis']['invasive_likelihood']
                print(f"  - Invasive species likelihood: {likelihood}")
            
            if 'change_metrics' in results:
                metrics = results['change_metrics']
                print(f"  - Vegetation change: {metrics.get('ndvi_change', 'N/A')}")
                print(f"  - Anomaly areas: {metrics.get('anomaly_pixel_count', 0)} pixels")
            
        except Exception as e:
            print(f"  - Error processing {period['year']}: {str(e)}")
            all_results['temporal_analysis'][period['year']] = {'error': str(e)}
    
    # Analyze specific species patterns
    print("\n\nAnalyzing species-specific patterns...")
    for species in target_species:
        print(f"\nAnalyzing {species['name']} ({species['scientific']})...")
        
        # Use most recent complete year (2023) for detailed species analysis
        species_results = detector.detect(
            aoi=yellowstone_aoi,
            start_date='2023-06-01',
            end_date='2023-09-30',
            species_context={
                'target_species': species['scientific'],
                'habitat': species['habitat'],
                'phenology': species['season']
            }
        )
        
        all_results['species_detections'][species['name']] = species_results
    
    # Generate risk assessments
    print("\n\nGenerating risk assessments...")
    all_results['risk_assessments'] = generate_risk_assessments(all_results)
    
    # Generate and save report
    print("\n\nGenerating comprehensive report...")
    report_content = generate_markdown_report(all_results)
    
    # Save report
    report_path = Path(__file__).parent.parent.parent / 'outputs' / 'reports' / 'yellowstone_invasive_species_report.md'
    report_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(report_path, 'w') as f:
        f.write(report_content)
    
    print(f"\nReport saved to: {report_path}")
    
    # Generate summary statistics
    print("\n=== Summary Statistics ===")
    print_summary_stats(all_results)
    
    return all_results

def generate_risk_assessments(results):
    """
    Generate risk assessments based on detection results
    """
    assessments = {}
    
    # Analyze temporal trends
    years = sorted(results['temporal_analysis'].keys())
    if len(years) >= 2:
        # Check for increasing trends
        likelihood_trend = []
        for year in years:
            year_data = results['temporal_analysis'][year]
            if 'ai_analysis' in year_data and 'invasive_likelihood' in year_data['ai_analysis']:
                likelihood = year_data['ai_analysis']['invasive_likelihood']
                if isinstance(likelihood, str) and likelihood in ['High', 'Medium', 'Low']:
                    likelihood_score = {'High': 3, 'Medium': 2, 'Low': 1}[likelihood]
                    likelihood_trend.append((year, likelihood_score))
        
        if len(likelihood_trend) >= 2:
            # Simple trend analysis
            trend_direction = "increasing" if likelihood_trend[-1][1] > likelihood_trend[0][1] else "stable"
            assessments['overall_trend'] = trend_direction
    
    # Species-specific risks
    species_risks = {}
    for species_name, detection in results['species_detections'].items():
        if 'ai_analysis' in detection:
            risk_level = detection['ai_analysis'].get('invasive_likelihood', 'Unknown')
            confidence = detection['ai_analysis'].get('confidence_score', 0)
            species_risks[species_name] = {
                'risk_level': risk_level,
                'confidence': confidence
            }
    
    assessments['species_risks'] = species_risks
    
    # Management priority areas
    assessments['management_priorities'] = [
        "Focus on early detection in high-traffic areas near roads and trails",
        "Monitor riparian zones for Canada thistle and leafy spurge",
        "Implement rapid response for new cheatgrass infestations",
        "Continue surveillance in previously treated areas",
        "Engage visitors in early detection reporting"
    ]
    
    return assessments

def generate_markdown_report(results):
    """
    Generate comprehensive markdown report
    """
    report = f"""# Yellowstone National Park Invasive Species Analysis Report

**Generated:** {results['metadata']['analysis_date']}  
**Analysis Area:** {results['metadata']['area_km2']:.2f} km²

## Executive Summary

This report presents a comprehensive analysis of invasive plant species in Yellowstone National Park from 2019 to 2024. The analysis uses satellite imagery and AI-powered detection to identify potential invasive species infestations and track their spread over time.

## Target Species

The following invasive species were analyzed:

"""
    
    # Add species list
    for species in results['metadata']['target_species']:
        report += f"- **{species['name']}** (*{species['scientific']}*)\n"
        report += f"  - Habitat: {species['habitat']}\n"
        report += f"  - Active Season: {species['season']}\n\n"
    
    # Temporal analysis section
    report += "\n## Temporal Analysis (2019-2024)\n\n"
    report += "### Annual Detection Results\n\n"
    
    for year in sorted(results['temporal_analysis'].keys()):
        year_data = results['temporal_analysis'][year]
        report += f"#### {year}\n"
        
        if 'error' in year_data:
            report += f"- Analysis Error: {year_data['error']}\n\n"
            continue
        
        if 'ai_analysis' in year_data:
            ai = year_data['ai_analysis']
            report += f"- **Invasive Likelihood:** {ai.get('invasive_likelihood', 'N/A')}\n"
            report += f"- **Confidence:** {ai.get('confidence_score', 'N/A')}\n"
            
            if 'detected_patterns' in ai:
                report += f"- **Key Patterns:** {', '.join(ai['detected_patterns'])}\n"
        
        if 'change_metrics' in year_data:
            metrics = year_data['change_metrics']
            report += f"- **Vegetation Change:** {metrics.get('ndvi_change', 'N/A')}\n"
            report += f"- **Anomaly Areas:** {metrics.get('anomaly_pixel_count', 0)} pixels\n"
        
        report += "\n"
    
    # Species-specific detections
    report += "\n## Species-Specific Detection Results (2023)\n\n"
    
    for species_name, detection in results['species_detections'].items():
        report += f"### {species_name}\n"
        
        if 'ai_analysis' in detection:
            ai = detection['ai_analysis']
            report += f"- **Detection Confidence:** {ai.get('invasive_likelihood', 'N/A')}\n"
            report += f"- **Confidence Score:** {ai.get('confidence_score', 'N/A')}\n"
            
            if 'analysis_text' in ai:
                report += f"\n**AI Analysis:**\n{ai['analysis_text']}\n"
        
        report += "\n"
    
    # Risk assessments
    report += "\n## Risk Assessments and Management Recommendations\n\n"
    
    if 'risk_assessments' in results:
        risk = results['risk_assessments']
        
        if 'overall_trend' in risk:
            report += f"### Overall Trend: {risk['overall_trend'].title()}\n\n"
        
        if 'species_risks' in risk:
            report += "### Species Risk Levels\n\n"
            for species, risk_data in risk['species_risks'].items():
                report += f"- **{species}**: {risk_data['risk_level']} risk (confidence: {risk_data['confidence']})\n"
            report += "\n"
        
        if 'management_priorities' in risk:
            report += "### Management Priorities\n\n"
            for priority in risk['management_priorities']:
                report += f"1. {priority}\n"
    
    # Methodology
    report += """
## Methodology

This analysis uses:
- **Sentinel-2 satellite imagery** (10m resolution)
- **Vegetation indices** (NDVI, EVI, SAVI)
- **AI-powered pattern recognition** using Claude Opus
- **Temporal change detection** algorithms
- **Species-specific spectral signatures**

## Data Sources

- Satellite Imagery: Copernicus Sentinel-2 Level-2A
- Analysis Period: June-September (peak growing season)
- Cloud Cover Threshold: <20%
- Spatial Resolution: 10-20 meters

## Limitations

- Cloud cover may limit data availability in some periods
- Spectral similarity between native and invasive species
- Early-stage infestations may be below detection threshold
- Ground truthing recommended for high-priority areas

## Recommendations

1. **Immediate Actions**
   - Ground survey high-risk areas identified in this report
   - Implement early detection rapid response (EDRR) protocols
   - Focus on gateway areas (roads, trails, campgrounds)

2. **Long-term Monitoring**
   - Continue annual satellite-based surveillance
   - Establish permanent monitoring plots
   - Integrate citizen science observations

3. **Management Strategies**
   - Prioritize treatment of small, isolated populations
   - Prevent spread along transportation corridors
   - Coordinate with adjacent land managers

---

*Report generated by Invasive Species Tracker using Google Earth Engine and Claude AI*
"""
    
    return report

def print_summary_stats(results):
    """
    Print summary statistics to console
    """
    # Count high risk detections
    high_risk_years = 0
    for year, data in results['temporal_analysis'].items():
        if 'ai_analysis' in data and data['ai_analysis'].get('invasive_likelihood') == 'High':
            high_risk_years += 1
    
    print(f"High risk years: {high_risk_years}/{len(results['temporal_analysis'])}")
    
    # Species with highest risk
    if 'risk_assessments' in results and 'species_risks' in results['risk_assessments']:
        high_risk_species = [
            species for species, risk in results['risk_assessments']['species_risks'].items()
            if risk['risk_level'] == 'High'
        ]
        if high_risk_species:
            print(f"High risk species: {', '.join(high_risk_species)}")
    
    print(f"Analysis complete for {len(results['metadata']['time_periods'])} time periods")
    print(f"Analyzed {len(results['metadata']['target_species'])} target species")

if __name__ == "__main__":
    try:
        results = analyze_yellowstone_invasives()
        print("\n=== Analysis Complete ===")
    except Exception as e:
        print(f"\nError during analysis: {str(e)}")
        import traceback
        traceback.print_exc()