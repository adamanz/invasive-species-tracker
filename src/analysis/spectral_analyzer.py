"""Claude-based spectral analysis for invasive species detection."""

import json
from typing import List, Dict, Any, Optional
from datetime import datetime
from anthropic import Anthropic
import os
from src.utils.logger import get_logger
from src.gee.satellite_data import SpectralSignature

logger = get_logger(__name__)


class ClaudeSpectralAnalyzer:
    """Analyzes spectral signatures using Claude AI."""
    
    MODEL = "claude-opus-4-20250514"
    
    def __init__(self):
        """Initialize the Claude spectral analyzer."""
        self.client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        logger.info("Claude spectral analyzer initialized")
    
    def analyze_single_signature(
        self,
        signature: SpectralSignature,
        species_of_interest: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Analyze a single spectral signature for invasive species.
        
        Args:
            signature: SpectralSignature object
            species_of_interest: Optional list of specific species to look for
            
        Returns:
            Analysis results including detection confidence and insights
        """
        prompt = self._build_single_signature_prompt(signature, species_of_interest)
        
        try:
            response = self.client.messages.create(
                model=self.MODEL,
                max_tokens=1000,
                messages=[{"role": "user", "content": prompt}]
            )
            
            # Parse the response
            analysis = self._parse_analysis_response(response.content[0].text)
            analysis['signature_metadata'] = {
                'location': (signature.longitude, signature.latitude),
                'date': signature.acquisition_date.isoformat(),
                'satellite': signature.satellite
            }
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error in spectral analysis: {str(e)}")
            return {
                'error': str(e),
                'detection_confidence': 0,
                'invasive_species_likely': False
            }
    
    def analyze_temporal_sequence(
        self,
        signatures: List[SpectralSignature],
        species_of_interest: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Analyze temporal sequence of spectral signatures.
        
        Args:
            signatures: List of SpectralSignature objects over time
            species_of_interest: Optional list of specific species to look for
            
        Returns:
            Temporal analysis results including spread patterns
        """
        if not signatures:
            return {'error': 'No signatures provided'}
        
        prompt = self._build_temporal_prompt(signatures, species_of_interest)
        
        try:
            response = self.client.messages.create(
                model=self.MODEL,
                max_tokens=2000,
                messages=[{"role": "user", "content": prompt}]
            )
            
            analysis = self._parse_temporal_analysis(response.content[0].text)
            analysis['temporal_metadata'] = {
                'start_date': signatures[0].acquisition_date.isoformat(),
                'end_date': signatures[-1].acquisition_date.isoformat(),
                'num_observations': len(signatures)
            }
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error in temporal analysis: {str(e)}")
            return {'error': str(e)}
    
    def analyze_spatial_context(
        self,
        center_signatures: List[SpectralSignature],
        surrounding_signatures: List[SpectralSignature],
        species_of_interest: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Analyze spatial context for invasive species spread.
        
        Args:
            center_signatures: Spectral signatures at the center point
            surrounding_signatures: Spectral signatures from surrounding area
            species_of_interest: Optional list of specific species to look for
            
        Returns:
            Spatial analysis results including spread direction
        """
        prompt = self._build_spatial_prompt(
            center_signatures, 
            surrounding_signatures,
            species_of_interest
        )
        
        try:
            response = self.client.messages.create(
                model=self.MODEL,
                max_tokens=1500,
                messages=[{"role": "user", "content": prompt}]
            )
            
            return self._parse_spatial_analysis(response.content[0].text)
            
        except Exception as e:
            logger.error(f"Error in spatial analysis: {str(e)}")
            return {'error': str(e)}
    
    def _build_single_signature_prompt(
        self,
        signature: SpectralSignature,
        species_of_interest: Optional[List[str]] = None
    ) -> str:
        """Build prompt for single signature analysis."""
        band_str = json.dumps(signature.band_values, indent=2)
        
        species_context = ""
        if species_of_interest:
            species_context = f"\nSpecies of particular interest: {', '.join(species_of_interest)}"
        
        prompt = f"""Analyze this spectral signature for potential invasive plant species:

Location: {signature.latitude}°N, {signature.longitude}°E
Date: {signature.acquisition_date.strftime('%Y-%m-%d')}
Satellite: {signature.satellite}
Cloud Coverage: {signature.cloud_probability}%

Spectral Band Values (Surface Reflectance):
{band_str}

Band Information:
- B2: Blue (490 nm)
- B3: Green (560 nm)
- B4: Red (665 nm)
- B5: Red Edge 1 (705 nm) [Sentinel-2 only]
- B6: Red Edge 2 (740 nm) [Sentinel-2 only]
- B7: Red Edge 3 (783 nm) [Sentinel-2 only]
- B8: NIR (842 nm)
- B8A: NIR Narrow (865 nm) [Sentinel-2 only]
- B11: SWIR 1 (1610 nm)
- B12: SWIR 2 (2190 nm)
{species_context}

Please analyze these spectral values and provide:
1. Detection confidence (0-100%): Is this likely an invasive species?
2. Spectral anomalies: What unusual patterns do you see?
3. Vegetation health indicators based on the spectral response
4. Possible species identification based on spectral signature
5. Reasoning for your assessment

Format your response as JSON with keys: detection_confidence, invasive_species_likely (boolean), anomalies, vegetation_health, possible_species, reasoning."""
        
        return prompt
    
    def _build_temporal_prompt(
        self,
        signatures: List[SpectralSignature],
        species_of_interest: Optional[List[str]] = None
    ) -> str:
        """Build prompt for temporal analysis."""
        temporal_data = []
        for sig in signatures:
            temporal_data.append({
                'date': sig.acquisition_date.strftime('%Y-%m-%d'),
                'bands': sig.band_values
            })
        
        species_context = ""
        if species_of_interest:
            species_context = f"\nSpecies of particular interest: {', '.join(species_of_interest)}"
        
        prompt = f"""Analyze this temporal sequence of spectral signatures for invasive species spread:

Location: {signatures[0].latitude}°N, {signatures[0].longitude}°E
Time Period: {signatures[0].acquisition_date.strftime('%Y-%m-%d')} to {signatures[-1].acquisition_date.strftime('%Y-%m-%d')}
Number of Observations: {len(signatures)}
{species_context}

Temporal Spectral Data:
{json.dumps(temporal_data, indent=2)}

Please analyze the temporal patterns and provide:
1. Change detection: Are there sudden or gradual changes in spectral signature?
2. Phenological patterns: Do the changes match invasive species growth cycles?
3. Spread indicators: Is there evidence of vegetation replacement?
4. Growth rate: If invasive species detected, estimate spread rate
5. Confidence in temporal pattern (0-100%)

Format your response as JSON with keys: change_detected, phenological_match, spread_indicators, growth_rate, temporal_confidence, temporal_insights."""
        
        return prompt
    
    def _build_spatial_prompt(
        self,
        center_signatures: List[SpectralSignature],
        surrounding_signatures: List[SpectralSignature],
        species_of_interest: Optional[List[str]] = None
    ) -> str:
        """Build prompt for spatial context analysis."""
        center_data = {
            'location': (center_signatures[0].longitude, center_signatures[0].latitude),
            'band_values': center_signatures[0].band_values
        }
        
        surrounding_data = []
        for sig in surrounding_signatures:
            surrounding_data.append({
                'location': (sig.longitude, sig.latitude),
                'band_values': sig.band_values
            })
        
        species_context = ""
        if species_of_interest:
            species_context = f"\nSpecies of particular interest: {', '.join(species_of_interest)}"
        
        prompt = f"""Analyze the spatial context of these spectral signatures for invasive species spread patterns:

Center Point:
{json.dumps(center_data, indent=2)}

Surrounding Points (arranged in circle):
{json.dumps(surrounding_data, indent=2)}
{species_context}

Please analyze the spatial patterns and provide:
1. Spatial heterogeneity: How different is the center from surroundings?
2. Spread direction: If invasive species present, which direction is it spreading?
3. Edge effects: Are there clear boundaries or gradual transitions?
4. Invasion stage: Early detection, established, or spreading?
5. Spatial confidence (0-100%)

Format your response as JSON with keys: spatial_heterogeneity, spread_direction, edge_effects, invasion_stage, spatial_confidence, spatial_insights."""
        
        return prompt
    
    def _parse_analysis_response(self, response_text: str) -> Dict[str, Any]:
        """Parse Claude's analysis response."""
        try:
            # Check if response contains JSON code block
            if '```json' in response_text:
                # Extract JSON from code block
                json_start = response_text.find('```json') + 7
                json_end = response_text.find('```', json_start)
                json_str = response_text[json_start:json_end].strip()
                return json.loads(json_str)
            else:
                # Try to parse as direct JSON
                return json.loads(response_text)
        except json.JSONDecodeError:
            # If not valid JSON, extract key information
            logger.warning("Response not in JSON format, extracting manually")
            
            # Basic extraction logic
            result = {
                'detection_confidence': 0,
                'invasive_species_likely': False,
                'anomalies': [],
                'vegetation_health': 'unknown',
                'possible_species': [],
                'reasoning': response_text
            }
            
            # Try to extract confidence value
            if 'confidence' in response_text.lower():
                import re
                matches = re.findall(r'(\d+)%', response_text)
                if matches:
                    result['detection_confidence'] = int(matches[0])
            
            # Check for invasive species mentions
            if any(word in response_text.lower() for word in ['invasive', 'detected', 'likely']):
                result['invasive_species_likely'] = True
            
            return result
    
    def _parse_temporal_analysis(self, response_text: str) -> Dict[str, Any]:
        """Parse temporal analysis response."""
        try:
            return json.loads(response_text)
        except json.JSONDecodeError:
            logger.warning("Temporal response not in JSON format")
            return {
                'change_detected': True,
                'phenological_match': False,
                'spread_indicators': [],
                'growth_rate': 'unknown',
                'temporal_confidence': 0,
                'temporal_insights': response_text
            }
    
    def _parse_spatial_analysis(self, response_text: str) -> Dict[str, Any]:
        """Parse spatial analysis response."""
        try:
            return json.loads(response_text)
        except json.JSONDecodeError:
            logger.warning("Spatial response not in JSON format")
            return {
                'spatial_heterogeneity': 'unknown',
                'spread_direction': 'unknown',
                'edge_effects': 'unknown',
                'invasion_stage': 'unknown',
                'spatial_confidence': 0,
                'spatial_insights': response_text
            }