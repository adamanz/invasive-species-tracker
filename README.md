# Invasive Species Tracker

An AI-powered system for detecting and monitoring invasive plant species using Google Earth Engine satellite imagery and Claude AI analysis.

## Features

- 🛰️ Satellite imagery analysis using Google Earth Engine
- 🤖 AI-powered change detection with Claude Opus
- 📊 Vegetation index calculations (NDVI, EVI, NDWI)
- 🗺️ Interactive mapping and visualization
- 📈 Temporal analysis and trend detection
- 📄 Automated report generation

## Quick Start

### Prerequisites

- Python 3.9 or higher
- Google Cloud account with Earth Engine API enabled
- Anthropic API key for Claude

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/yourusername/invasive-species-tracker.git
cd invasive-species-tracker
```

2. **Create a virtual environment**
```bash
python -m venv venv

# On macOS/Linux:
source venv/bin/activate

# On Windows:
venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Set up environment variables**
```bash
cp .env.template .env
```

Edit `.env` with your credentials:
- `GOOGLE_CLOUD_PROJECT`: Your Google Cloud project ID
- `GOOGLE_CLOUD_API_KEY`: Your Google Cloud API key with Earth Engine enabled
- `ANTHROPIC_API_KEY`: Your Claude API key

5. **Verify Earth Engine connection**
```bash
python -m src.gee.auth
```

## Project Structure

```
invasive-species-tracker/
├── src/
│   ├── gee/              # Earth Engine modules
│   ├── analysis/         # Claude AI analysis
│   ├── visualization/    # Mapping and charts
│   └── utils/           # Helper functions
├── data/
│   ├── aois/            # Areas of interest
│   └── species/         # Species signatures
├── outputs/             # Generated reports and maps
├── tests/               # Unit tests
└── logs/               # Application logs
```

## Usage

### Basic Example

```python
from src.gee.auth import initialize_earth_engine
from src.gee.imagery import get_sentinel2_composite
from src.analysis.detector import InvasiveSpeciesDetector

# Initialize Earth Engine
initialize_earth_engine()

# Define area of interest
aoi = {
    'type': 'Rectangle',
    'coordinates': [-122.5, 37.5, -122.0, 38.0]
}

# Create detector
detector = InvasiveSpeciesDetector()

# Run analysis
results = detector.analyze_area(
    aoi=aoi,
    start_date='2023-01-01',
    end_date='2023-12-31',
    species='japanese_knotweed'
)

# Generate report
report = detector.generate_report(results)
print(report)
```

### Command Line Interface (Coming Soon)

```bash
# Analyze a specific area
python -m invasive_tracker analyze --aoi path/to/area.geojson --species kudzu

# Monitor changes over time
python -m invasive_tracker monitor --aoi path/to/area.geojson --interval monthly

# Generate report
python -m invasive_tracker report --results path/to/results.json
```

## Configuration

See `claude.md` for detailed project specifications and configuration options.

## Development

### Running Tests
```bash
pytest tests/
```

### Code Formatting
```bash
black src/
flake8 src/
```

### Type Checking
```bash
mypy src/
```

## Troubleshooting

### Earth Engine Authentication Issues

If you encounter authentication errors:

1. Ensure your Google Cloud API key has Earth Engine API enabled
2. Check that your project ID is correct
3. Verify API key permissions in Google Cloud Console

### Memory Issues with Large Areas

For large area analysis:
- Use smaller time windows
- Increase the `tileScale` parameter
- Export results to Google Cloud Storage

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Google Earth Engine for satellite data access
- Anthropic for Claude AI capabilities
- The geospatial Python community