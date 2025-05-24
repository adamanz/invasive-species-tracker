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

# Sample species data for UI
SPECIES_DATA = {
    "yellowstone": [
        {
            "name": "Whitebark pine",
            "scientific_name": "Pinus albicaulis",
            "threats": ["Temperature stress", "Mountain pine beetle", "Blister rust"],
            "timeline": "50% mortality by 2050; functional extinction possible by 2100",
            "impacts": "Clark's nutcracker decline; grizzly bear food loss; watershed function",
            "risk_level": "critical"
        },
        {
            "name": "Yellowstone cutthroat trout",
            "scientific_name": "Oncorhynchus clarkii bouvieri",
            "threats": ["Thermal barriers", "Non-native competition", "Disease"],
            "timeline": "70% habitat loss by 2050",
            "impacts": "Aquatic food web collapse; terrestrial predator impacts",
            "risk_level": "critical"
        },
        {
            "name": "American pika",
            "scientific_name": "Ochotona princeps",
            "threats": ["Heat stress", "Habitat compression", "Limited dispersal"],
            "timeline": "Local extirpations ongoing; accelerating losses post-2030",
            "impacts": "Alpine ecosystem engineering loss",
            "risk_level": "critical"
        },
        {
            "name": "Native pollinators",
            "scientific_name": "Multiple species",
            "threats": ["Phenological mismatches", "Habitat loss", "Competition"],
            "timeline": "Network simplification detectable now; collapse risk by 2040",
            "impacts": "Plant reproduction failure; ecosystem service loss",
            "risk_level": "critical"
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

# Temporal data for visualization
TEMPORAL_DATA = {
    "yellowstone": {
        "years": [2019, 2020, 2021, 2022, 2023, 2024],
        "series": {
            "whitebark_pine": [100, 95, 88, 82, 75, 68],
            "cutthroat_trout": [100, 98, 92, 85, 78, 70],
            "american_pika": [100, 97, 93, 88, 82, 75],
            "pollinators": [100, 96, 90, 83, 75, 65]
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