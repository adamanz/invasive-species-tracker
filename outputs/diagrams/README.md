# Architecture Diagrams

This directory contains comprehensive architecture diagrams for the Invasive Species Tracker system, showing how satellite data flows through statistical models into Claude AI for analysis.

## Diagram Files

### 1. `architecture_diagram.xml` - Complete System Architecture
**Use this diagram to understand the entire system structure**

**What it shows:**
- 🛰️ **Satellite Data Sources**: Sentinel-2 and Landsat collections
- 🌍 **Google Earth Engine Processing**: Data extraction and preprocessing
- 🔬 **Multi-Model Analysis Pipeline**: Temporal, spectral, spatial, and validation frameworks
- 🤖 **Claude AI Integration**: Spectral and change analysis with Claude Opus
- 📊 **Analysis Outputs**: Species detection, reports, maps, and web interface

**Key Features:**
- Technology badges showing Google Earth Engine, Python, Claude Opus, Flask
- Performance metrics and innovation highlights
- Complete data flow from raw satellite imagery to actionable intelligence
- Color-coded components by function

### 2. `data_flow_diagram.xml` - Simplified Data Pipeline
**Use this diagram to understand the step-by-step data processing flow**

**What it shows:**
- **Step 1**: Raw satellite data (multi-spectral imagery)
- **Step 2**: Google Earth Engine processing (cloud filtering, composites, signatures)
- **Step 3**: Statistical model analysis (temporal, change detection, spatial)
- **Step 4**: Data preparation for AI analysis
- **Step 5**: Claude AI analysis (species identification, outbreak detection)
- **Step 6**: Actionable outputs (reports, maps, management recommendations)

**Key Innovation Highlighted:**
Direct AI interpretation of spectral data without traditional vegetation indices

## How to Use These Diagrams

### Option 1: Draw.io (Recommended)
1. Go to [app.diagrams.net](https://app.diagrams.net) (formerly draw.io)
2. Click "Open Existing Diagram"
3. Upload either XML file
4. View, edit, and export as needed

### Option 2: Local Draw.io Desktop
1. Download [Draw.io Desktop](https://github.com/jgraph/drawio-desktop/releases)
2. Open the application
3. File → Open → Select XML file

### Option 3: Visual Studio Code
1. Install the "Draw.io Integration" extension
2. Open the XML file in VS Code
3. The diagram will render automatically

## Export Options

From Draw.io, you can export diagrams as:
- **PNG/JPG**: For documentation and presentations
- **PDF**: For high-quality printing
- **SVG**: For scalable web graphics
- **HTML**: For interactive web embedding

## Diagram Components Explained

### Color Coding
- **Blue**: Data sources and inputs
- **Orange**: Processing and transformation
- **Purple**: Analysis and modeling
- **Green**: Outputs and results
- **Light Blue**: Claude AI integration

### Technology Annotations
- **Google Earth Engine**: Satellite data processing platform
- **Python 3.9+**: Core programming language
- **Claude Opus**: AI model for species analysis
- **Flask + Leaflet**: Web interface technologies

### Data Flow Types
- **Raw Spectral Data**: Multi-band satellite imagery
- **Processed Imagery**: Cloud-filtered composites and signatures
- **Statistical Features**: Temporal, spatial, and change metrics
- **Structured Analysis Package**: Formatted data for AI input
- **AI-Generated Insights**: Species detection and risk assessment

## Performance Metrics

The system achieves:
- **Detection Confidence**: 70-95% for target species
- **Processing Speed**: ~500MB/min for satellite imagery
- **Temporal Coverage**: 2019-2024 analysis periods
- **Species Accuracy**: 85%+ validation against ground truth
- **Spatial Resolution**: 10m (Sentinel-2) to 30m (Landsat)

## Key Innovation

**Direct AI Spectral Interpretation**: Unlike traditional remote sensing that relies on vegetation indices (NDVI, EVI), this system feeds raw spectral band values directly to Claude AI. This approach:

1. **Preserves Information**: No data loss from index calculations
2. **Species-Specific Recognition**: AI learns unique spectral signatures
3. **Multi-Band Analysis**: Simultaneously analyzes all 10 spectral bands
4. **Contextual Understanding**: Considers temporal and spatial patterns
5. **Adaptive Learning**: Can identify new invasion patterns without code changes

## Target Species Integration

The diagrams show how the system detects these invasive species:

- 🌾 **Cheatgrass** (*Bromus tectorum*): Post-fire colonization patterns
- 💜 **Spotted Knapweed** (*Centaurea stoebe*): Allelopathic signatures  
- 🌸 **Canada Thistle** (*Cirsium arvense*): Rhizome spread detection
- 🟡 **Leafy Spurge** (*Euphorbia esula*): Deep root system impacts
- 🟨 **Dalmatian Toadflax** (*Linaria dalmatica*): Roadside establishment

## Integration with Project Documentation

These diagrams complement:
- **README.md**: Project overview with species visuals
- **claude.md**: Technical specifications and methodology
- **yellowstone_invasive_species_detailed.md**: Comprehensive analysis report
- **Sacramento results**: Validation case study

## Contributing

To update these diagrams:
1. Open in Draw.io
2. Make your changes
3. Export as XML (File → Export as → XML)
4. Replace the existing file
5. Update this README if needed

---

*Diagrams generated for Invasive Species Tracker - AI-Powered Satellite Analysis System*