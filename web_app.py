"""Flask web application for Invasive Species Tracker UI."""

from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
from datetime import datetime
import json
import os
from pathlib import Path

# Add project to path
import sys
sys.path.append(str(Path(__file__).parent))

from src.detector import InvasiveSpeciesDetector

app = Flask(__name__)
CORS(app)

# Initialize detector
detector = InvasiveSpeciesDetector(satellite="sentinel2")

# Invasive species data for UI
SPECIES_DATA = {
    "yellowstone": [
        {
            "name": "Cheatgrass",
            "scientific_name": "Bromus tectorum",
            "threats": ["Post-fire colonization", "Rapid growth", "Fire cycle acceleration"],
            "timeline": "95.2% confidence in fire-affected areas; 25-30% annual expansion",
            "impacts": "Fire risk increase 300-400%; native grass displacement; ecosystem conversion",
            "risk_level": "critical",
            "confidence": 95.2,
            "detection_sites": 8,
            "spread_rate": "25-30% annually"
        },
        {
            "name": "Spotted Knapweed",
            "scientific_name": "Centaurea stoebe",
            "threats": ["Allelopathic compounds", "Prolific seed production", "Soil degradation"],
            "timeline": "Detected at 7 sites with 82.4% avg confidence; widespread distribution",
            "impacts": "Biodiversity reduction; soil erosion; forage quality loss; bare patch creation",
            "risk_level": "high",
            "confidence": 88.7,
            "detection_sites": 7,
            "spread_rate": "15-20% annually"
        },
        {
            "name": "Canada Thistle",
            "scientific_name": "Cirsium arvense",
            "threats": ["Rhizome spread", "Dense colonies", "Competitive advantage"],
            "timeline": "Moderate spread at 5 sites; 78.6% avg confidence; riparian focus",
            "impacts": "Native vegetation displacement; reduced forage quality; recreation impediment",
            "risk_level": "medium",
            "confidence": 84.3,
            "detection_sites": 5,
            "spread_rate": "10-15% annually"
        },
        {
            "name": "Leafy Spurge",
            "scientific_name": "Euphorbia esula",
            "threats": ["Deep root system", "Toxic latex", "Livestock avoidance"],
            "timeline": "Limited distribution at 2 sites; 71.2% avg confidence; toxicity concerns",
            "impacts": "Grazing land loss; livestock poisoning; human skin irritation; erosion",
            "risk_level": "medium",
            "confidence": 73.4,
            "detection_sites": 2,
            "spread_rate": "8-12% annually"
        },
        {
            "name": "Dalmatian Toadflax",
            "scientific_name": "Linaria dalmatica",
            "threats": ["Roadside establishment", "Seed dispersal", "Root spread"],
            "timeline": "Detected at 4 sites; 75.8% avg confidence; entrance corridor focus",
            "impacts": "Range degradation; native plant competition; aesthetic degradation",
            "risk_level": "medium",
            "confidence": 81.2,
            "detection_sites": 4,
            "spread_rate": "8-12% annually"
        }
    ],
    "sacramento_delta": [
        {
            "name": "Water Hyacinth",
            "scientific_name": "Eichhornia crassipes",
            "threats": ["Rapid reproduction", "No natural predators", "Warm temperatures"],
            "timeline": "Can double coverage in 2 weeks during summer",
            "impacts": "Navigation blockage; oxygen depletion; native species displacement",
            "risk_level": "critical"
        },
        {
            "name": "Brazilian Waterweed", 
            "scientific_name": "Egeria densa",
            "threats": ["Fragment dispersal", "Nutrient pollution", "Altered flow"],
            "timeline": "Year-round growth; peak expansion May-October",
            "impacts": "Irrigation canal blockage; recreation impediment; fish habitat alteration",
            "risk_level": "high"
        },
        {
            "name": "Water Primrose",
            "scientific_name": "Ludwigia spp.",
            "threats": ["Emergent growth", "Bank stabilization", "Flooding"],
            "timeline": "Expanding range northward; 30% increase annually",
            "impacts": "Channel capacity reduction; flood risk increase; wetland conversion",
            "risk_level": "high"
        }
    ]
}

# Temporal invasion progression data
TEMPORAL_DATA = {
    "yellowstone": {
        "years": [2019, 2020, 2021, 2022, 2023, 2024],
        "series": {
            "cheatgrass": [12, 18, 24, 31, 38, 45],  # Hotspot count increase
            "spotted_knapweed": [15, 18, 21, 25, 28, 32],  # Detection sites
            "canada_thistle": [8, 10, 12, 15, 18, 22],  # Spread progression
            "leafy_spurge": [3, 4, 5, 6, 8, 10],  # Limited but growing
            "dalmatian_toadflax": [5, 7, 9, 12, 15, 18]  # Roadside expansion
        },
        "confidence": {
            "cheatgrass": [75, 78, 82, 87, 92, 95],  # Increasing detection confidence
            "spotted_knapweed": [70, 73, 76, 80, 85, 88],
            "canada_thistle": [68, 71, 74, 78, 81, 84],
            "leafy_spurge": [65, 67, 69, 71, 72, 73],
            "dalmatian_toadflax": [70, 72, 75, 78, 80, 81]
        }
    },
    "sacramento_delta": {
        "years": [2019, 2020, 2021, 2022, 2023, 2024],
        "series": {
            "water_hyacinth": [45, 52, 65, 78, 85, 92],
            "brazilian_waterweed": [60, 63, 68, 72, 76, 80],
            "water_primrose": [40, 45, 52, 60, 68, 75]
        }
    }
}


@app.route('/')
def index():
    """Render main UI."""
    return render_template('index.html')


@app.route('/api/species/<location>')
def get_species_data(location):
    """Get species vulnerability data for a location."""
    location_key = location.lower().replace(' ', '_')
    
    # Get species data
    species = SPECIES_DATA.get(location_key, SPECIES_DATA['yellowstone'])
    
    # Get temporal data
    temporal = TEMPORAL_DATA.get(location_key, TEMPORAL_DATA['yellowstone'])
    
    return jsonify({
        'location': location,
        'species': species,
        'temporal': temporal
    })


@app.route('/api/detect', methods=['POST'])
def detect_invasive_species():
    """Run invasive species detection for given parameters."""
    data = request.json
    
    try:
        # Extract parameters
        lat = float(data.get('latitude'))
        lon = float(data.get('longitude'))
        year = int(data.get('year', 2023))
        
        # Create date from year (use summer for peak vegetation)
        date = datetime(year, 8, 15)
        
        # Run detection
        result = detector.detect_at_location(
            location=(lon, lat),
            date=date,
            comprehensive=False  # Quick detection for UI
        )
        
        # Format response
        response = {
            'detected': result.invasive_detected,
            'confidence': result.confidence,
            'species': result.species if result.species else [],
            'stage': result.outbreak_stage,
            'recommendations': result.recommended_actions[:3] if result.recommended_actions else []
        }
        
        return jsonify(response)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@app.route('/api/locations')
def get_locations():
    """Get list of available locations."""
    locations = [
        {
            'name': 'Yellowstone National Park',
            'coordinates': [-110.5885, 44.4280],
            'type': 'terrestrial'
        },
        {
            'name': 'Sacramento Delta',
            'coordinates': [-121.5969, 37.9089],
            'type': 'aquatic'
        }
    ]
    return jsonify(locations)


if __name__ == '__main__':
    # Create templates directory if it doesn't exist
    os.makedirs('templates', exist_ok=True)
    os.makedirs('static', exist_ok=True)
    
    app.run(debug=True, port=5000)