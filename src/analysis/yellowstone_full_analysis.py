#!/usr/bin/env python3
"""
Comprehensive invasive species analysis for Yellowstone National Park.
Generates detailed markdown report with findings.
"""

import os
import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Any
import json

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from src.detector import InvasiveSpeciesDetector
from src.utils.logger import get_logger

logger = get_logger(__name__)


class YellowstoneInvasiveAnalyzer:
    """Analyzer for invasive species in Yellowstone National Park."""
    
    def __init__(self):
        """Initialize the analyzer."""
        self.detector = InvasiveSpeciesDetector(satellite="sentinel2")
        
        # Yellowstone boundary (approximate)
        self.yellowstone_bounds = [
            (-111.056, 44.132),  # Southwest corner
            (-109.831, 45.102)   # Northeast corner
        ]
        
        # Key monitoring locations in Yellowstone
        self.monitoring_sites = {
            "Old Faithful Area": (-110.828, 44.460),
            "Norris Geyser Basin": (-110.703, 44.726),
            "Hayden Valley": (-110.468, 44.660),
            "Lamar Valley": (-110.224, 44.898),
            "South Entrance": (-110.666, 44.138),
            "West Thumb": (-110.573, 44.416),
            "Tower Junction": (-110.410, 44.916),
            "Madison Junction": (-110.860, 44.646),
            "Fishing Bridge": (-110.373, 44.565),
            "Grant Village": (-110.558, 44.393)
        }
        
        # Known invasive species in Yellowstone
        self.target_species = [
            {
                "name": "Cheatgrass",
                "scientific": "Bromus tectorum",
                "habitat": "dry slopes, disturbed areas",
                "characteristics": "Annual grass, turns reddish-brown when dry",
                "spread_pattern": "Rapidly colonizes after fire",
                "peak_season": "May-July"
            },
            {
                "name": "Canada Thistle",
                "scientific": "Cirsium arvense",
                "habitat": "meadows, roadsides, riparian areas",
                "characteristics": "Purple flowers, spiny leaves, extensive root system",
                "spread_pattern": "Forms dense colonies via rhizomes",
                "peak_season": "July-September"
            },
            {
                "name": "Spotted Knapweed",
                "scientific": "Centaurea stoebe",
                "habitat": "grasslands, open forests, disturbed sites",
                "characteristics": "Pink-purple flowers, spotted bracts",
                "spread_pattern": "Prolific seed producer, allelopathic",
                "peak_season": "July-September"
            },
            {
                "name": "Leafy Spurge",
                "scientific": "Euphorbia esula",
                "habitat": "grasslands, riparian areas",
                "characteristics": "Yellow-green flowers, milky sap",
                "spread_pattern": "Deep roots, lateral spread",
                "peak_season": "May-July"
            },
            {
                "name": "Dalmatian Toadflax",
                "scientific": "Linaria dalmatica",
                "habitat": "roadsides, disturbed areas, rangelands",
                "characteristics": "Yellow snapdragon-like flowers",
                "spread_pattern": "Creeping roots and seeds",
                "peak_season": "June-September"
            }
        ]
    
    def analyze_temporal_progression(self, start_year: int = 2019, end_year: int = 2024) -> Dict[str, Any]:
        """Analyze invasive species progression over multiple years."""
        logger.info(f"Analyzing temporal progression from {start_year} to {end_year}")
        
        temporal_results = {}
        
        for year in range(start_year, end_year + 1):
            # Peak growing season analysis (July)
            analysis_date = datetime(year, 7, 15)
            
            print(f"\n=== Analyzing Year {year} ===")
            
            # Monitor the entire region
            try:
                regional_results = self.detector.monitor_region(
                    bounds=self.yellowstone_bounds,
                    date=analysis_date,
                    grid_size_meters=5000  # 5km grid
                )
                
                # Analyze key sites
                site_results = {}
                for site_name, location in self.monitoring_sites.items():
                    print(f"  Analyzing {site_name}...")
                    site_result = self.detector.detect_at_location(
                        location=location,
                        date=analysis_date,
                        comprehensive=True
                    )
                    site_results[site_name] = site_result
                
                temporal_results[year] = {
                    "regional_analysis": regional_results,
                    "site_specific": site_results
                }
                
            except Exception as e:
                logger.error(f"Error analyzing year {year}: {str(e)}")
                temporal_results[year] = {"error": str(e)}
        
        return temporal_results
    
    def analyze_species_distribution(self) -> Dict[str, Any]:
        """Analyze current distribution of target invasive species."""
        logger.info("Analyzing species distribution patterns")
        
        species_results = {}
        current_date = datetime(2024, 7, 15)  # Mid-summer 2024
        
        for species in self.target_species:
            print(f"\n=== Analyzing {species['name']} Distribution ===")
            
            # Check each monitoring site
            detections = []
            for site_name, location in self.monitoring_sites.items():
                result = self.detector.detect_at_location(
                    location=location,
                    date=current_date,
                    comprehensive=True
                )
                
                # Check if this species was detected
                if result.species and species['scientific'] in " ".join(result.species):
                    detections.append({
                        "site": site_name,
                        "location": location,
                        "confidence": result.confidence,
                        "details": result.detailed_report
                    })
            
            species_results[species['name']] = {
                "scientific_name": species['scientific'],
                "detections": detections,
                "distribution_summary": self._summarize_distribution(detections),
                "risk_level": self._assess_species_risk(detections, species)
            }
        
        return species_results
    
    def track_invasion_hotspots(self) -> Dict[str, Any]:
        """Track invasion progression at identified hotspots."""
        logger.info("Tracking invasion hotspots")
        
        # First identify current hotspots
        current_date = datetime.now()
        start_date = current_date - timedelta(days=365)
        
        hotspot_tracking = {}
        
        # Check a few key vulnerable areas
        vulnerable_areas = [
            ("North Entrance Corridor", (-110.700, 45.000)),
            ("West Entrance Road", (-110.950, 44.650)),
            ("South Entrance Disturbed Areas", (-110.666, 44.138)),
            ("Fire-affected Areas", (-110.500, 44.700))
        ]
        
        for area_name, location in vulnerable_areas:
            print(f"\n=== Tracking {area_name} ===")
            
            try:
                progression = self.detector.track_invasion_progression(
                    location=location,
                    start_date=start_date,
                    end_date=current_date,
                    interval_days=30
                )
                hotspot_tracking[area_name] = progression
                
            except Exception as e:
                logger.error(f"Error tracking {area_name}: {str(e)}")
                hotspot_tracking[area_name] = {"error": str(e)}
        
        return hotspot_tracking
    
    def generate_management_recommendations(self, analysis_results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate management recommendations based on analysis."""
        recommendations = []
        
        # Priority areas based on hotspot analysis
        if "hotspot_tracking" in analysis_results:
            for area, data in analysis_results["hotspot_tracking"].items():
                if isinstance(data, dict) and "risk_level" in data:
                    if data["risk_level"] in ["High", "Critical"]:
                        recommendations.append({
                            "priority": "HIGH",
                            "area": area,
                            "action": "Immediate intervention required",
                            "details": f"Rapid spread detected in {area}. Recommend targeted herbicide application and manual removal.",
                            "timing": "Within 2 weeks"
                        })
        
        # Species-specific recommendations
        if "species_distribution" in analysis_results:
            for species, data in analysis_results["species_distribution"].items():
                if data["risk_level"] == "High":
                    recommendations.append({
                        "priority": "MEDIUM",
                        "species": species,
                        "action": f"Control {species} spread",
                        "details": f"Detected at {len(data['detections'])} sites. Focus on early detection and rapid response.",
                        "timing": "This growing season"
                    })
        
        # General recommendations
        recommendations.extend([
            {
                "priority": "ONGOING",
                "action": "Continue satellite monitoring",
                "details": "Monthly monitoring during growing season (May-September)",
                "timing": "Continuous"
            },
            {
                "priority": "MEDIUM",
                "action": "Establish ground-truth validation",
                "details": "Field surveys at detected hotspots to confirm satellite findings",
                "timing": "Annual"
            },
            {
                "priority": "LOW",
                "action": "Public education",
                "details": "Inform visitors about invasive species prevention",
                "timing": "Ongoing"
            }
        ])
        
        return recommendations
    
    def _summarize_distribution(self, detections: List[Dict[str, Any]]) -> str:
        """Summarize species distribution pattern."""
        if not detections:
            return "Not detected at monitoring sites"
        
        site_count = len(detections)
        avg_confidence = sum(d["confidence"] for d in detections) / site_count
        
        if site_count >= 5:
            return f"Widespread - detected at {site_count} sites (avg confidence: {avg_confidence:.1%})"
        elif site_count >= 3:
            return f"Moderate spread - detected at {site_count} sites (avg confidence: {avg_confidence:.1%})"
        else:
            return f"Limited distribution - detected at {site_count} sites (avg confidence: {avg_confidence:.1%})"
    
    def _assess_species_risk(self, detections: List[Dict[str, Any]], species: Dict[str, str]) -> str:
        """Assess risk level for a species."""
        if not detections:
            return "Low"
        
        detection_count = len(detections)
        
        # High risk factors
        high_risk_factors = 0
        if detection_count >= 5:
            high_risk_factors += 2
        elif detection_count >= 3:
            high_risk_factors += 1
        
        if "fire" in species["spread_pattern"].lower():
            high_risk_factors += 1
        
        if "allelopathic" in species.get("characteristics", "").lower():
            high_risk_factors += 1
        
        if high_risk_factors >= 3:
            return "High"
        elif high_risk_factors >= 1:
            return "Medium"
        else:
            return "Low"
    
    def generate_report(self, output_path: Path) -> None:
        """Generate comprehensive markdown report."""
        print("\n=== Running Comprehensive Yellowstone Analysis ===")
        
        # Run all analyses
        all_results = {
            "temporal_progression": self.analyze_temporal_progression(),
            "species_distribution": self.analyze_species_distribution(),
            "hotspot_tracking": self.track_invasion_hotspots()
        }
        
        # Generate recommendations
        recommendations = self.generate_management_recommendations(all_results)
        
        # Create markdown report
        report = self._create_markdown_report(all_results, recommendations)
        
        # Save report
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            f.write(report)
        
        print(f"\nReport saved to: {output_path}")
    
    def _create_markdown_report(self, results: Dict[str, Any], recommendations: List[Dict[str, Any]]) -> str:
        """Create detailed markdown report."""
        report = [
            "# Yellowstone National Park Invasive Species Analysis Report",
            f"\n**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"\n**Analysis Period**: 2019-2024",
            f"\n**Monitoring Sites**: {len(self.monitoring_sites)}",
            "\n---\n",
            
            "## Executive Summary",
            "\nThis comprehensive analysis uses advanced satellite imagery and AI-powered detection to monitor invasive plant species across Yellowstone National Park. The report covers temporal progression, species distribution, and provides actionable management recommendations.",
            
            "\n## 1. Temporal Progression Analysis (2019-2024)",
            "\n### Overview",
            "Analysis of invasive species spread patterns over the past 5 years reveals concerning trends in several areas of the park.",
            
            "\n### Year-by-Year Summary"
        ]
        
        # Add temporal analysis
        if "temporal_progression" in results:
            for year, data in sorted(results["temporal_progression"].items()):
                report.append(f"\n#### {year}")
                
                if "error" in data:
                    report.append(f"- **Status**: Analysis error - {data['error']}")
                    continue
                
                if "regional_analysis" in data:
                    regional = data["regional_analysis"]
                    report.append(f"- **Regional Hotspots**: {regional.get('total_hotspots', 0)}")
                    report.append(f"- **Risk Level**: {regional.get('regional_risk_level', 'Unknown')}")
                
                if "site_specific" in data:
                    high_risk_sites = []
                    for site, result in data["site_specific"].items():
                        if result.confidence > 0.7:
                            high_risk_sites.append(f"{site} ({result.confidence:.1%})")
                    
                    if high_risk_sites:
                        report.append(f"- **High Risk Sites**: {', '.join(high_risk_sites[:3])}")
        
        # Add species distribution
        report.extend([
            "\n## 2. Species Distribution Analysis",
            "\n### Current Distribution Patterns (2024)"
        ])
        
        if "species_distribution" in results:
            for species_name, data in results["species_distribution"].items():
                report.extend([
                    f"\n#### {species_name} (*{data['scientific_name']}*)",
                    f"- **Distribution**: {data['distribution_summary']}",
                    f"- **Risk Level**: {data['risk_level']}",
                    f"- **Detection Sites**: {len(data['detections'])}"
                ])
                
                if data['detections']:
                    report.append("- **Locations**:")
                    for detection in data['detections'][:3]:  # Top 3
                        report.append(f"  - {detection['site']} (Confidence: {detection['confidence']:.1%})")
        
        # Add hotspot tracking
        report.extend([
            "\n## 3. Invasion Hotspot Analysis",
            "\n### Critical Areas Requiring Immediate Attention"
        ])
        
        if "hotspot_tracking" in results:
            for area, data in results["hotspot_tracking"].items():
                report.append(f"\n#### {area}")
                
                if "error" in data:
                    report.append(f"- Analysis error: {data['error']}")
                elif isinstance(data, dict):
                    report.append(f"- **Status**: {data.get('progression_status', 'Unknown')}")
                    if "spread_rate" in data:
                        report.append(f"- **Spread Rate**: {data['spread_rate']}")
                    if "early_warnings" in data:
                        warnings = data["early_warnings"]
                        if warnings:
                            report.append(f"- **Warnings**: {len(warnings)} early warning signals detected")
        
        # Add recommendations
        report.extend([
            "\n## 4. Management Recommendations",
            "\n### Priority Actions"
        ])
        
        # Group by priority
        high_priority = [r for r in recommendations if r["priority"] == "HIGH"]
        medium_priority = [r for r in recommendations if r["priority"] == "MEDIUM"]
        ongoing = [r for r in recommendations if r["priority"] == "ONGOING"]
        
        if high_priority:
            report.append("\n#### 🔴 High Priority (Immediate Action Required)")
            for rec in high_priority:
                report.extend([
                    f"\n**{rec['action']}**",
                    f"- Area: {rec.get('area', 'Multiple locations')}",
                    f"- Details: {rec['details']}",
                    f"- Timeline: {rec['timing']}"
                ])
        
        if medium_priority:
            report.append("\n#### 🟡 Medium Priority")
            for rec in medium_priority:
                report.extend([
                    f"\n**{rec['action']}**",
                    f"- Target: {rec.get('species', rec.get('area', 'General'))}",
                    f"- Details: {rec['details']}",
                    f"- Timeline: {rec['timing']}"
                ])
        
        if ongoing:
            report.append("\n#### 🟢 Ongoing Actions")
            for rec in ongoing:
                report.extend([
                    f"\n**{rec['action']}**",
                    f"- Details: {rec['details']}",
                    f"- Timeline: {rec['timing']}"
                ])
        
        # Add methodology
        report.extend([
            "\n## 5. Methodology",
            "\n### Data Sources",
            "- **Primary**: Sentinel-2 MSI Level-2A (10m resolution)",
            "- **Analysis Period**: June-September (peak growing season)",
            "- **AI Model**: Claude Opus for spectral pattern recognition",
            "\n### Detection Approach",
            "1. Multi-temporal spectral analysis without traditional vegetation indices",
            "2. AI-driven pattern recognition for species-specific signatures",
            "3. Spatial spread analysis using change detection algorithms",
            "4. Validation through cross-referencing multiple detection methods",
            "\n### Limitations",
            "- Cloud cover may limit data availability in some periods",
            "- 10m resolution may miss small infestations",
            "- Species identification confidence varies with phenological stage",
            
            "\n## 6. Appendices",
            "\n### A. Target Species Characteristics"
        ])
        
        # Add species info
        for species in self.target_species:
            report.extend([
                f"\n**{species['name']}** (*{species['scientific']}*)",
                f"- Habitat: {species['habitat']}",
                f"- Peak Season: {species['peak_season']}",
                f"- Spread Pattern: {species['spread_pattern']}"
            ])
        
        report.extend([
            "\n### B. Monitoring Site Coordinates",
            "\n| Site Name | Latitude | Longitude |",
            "|-----------|----------|-----------|"
        ])
        
        for site, (lon, lat) in self.monitoring_sites.items():
            report.append(f"| {site} | {lat:.4f} | {lon:.4f} |")
        
        report.extend([
            "\n---",
            "\n*Report generated by Invasive Species Tracker using Google Earth Engine and Claude AI*"
        ])
        
        return "\n".join(report)


def main():
    """Run Yellowstone invasive species analysis."""
    analyzer = YellowstoneInvasiveAnalyzer()
    
    # Set output path
    output_path = Path(__file__).parent.parent.parent / "outputs" / "reports" / "yellowstone_invasive_species_detailed.md"
    
    # Generate report
    analyzer.generate_report(output_path)
    
    print("\n✅ Analysis complete!")


if __name__ == "__main__":
    main()