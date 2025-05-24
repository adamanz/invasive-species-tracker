"""Claude-based change analysis for invasive species outbreak detection."""

import json
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from anthropic import Anthropic
import os
from src.utils.logger import get_logger
from src.gee.temporal_analysis import TemporalComposite
from src.gee.change_detection import ChangeEvent
from src.gee.satellite_data import SpectralSignature

logger = get_logger(__name__)


class ClaudeChangeAnalyzer:
    """Analyzes detected changes to identify invasive species outbreaks."""
    
    MODEL = "claude-opus-4-20250514"
    
    def __init__(self):
        """Initialize Claude change analyzer."""
        self.client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        logger.info("Claude change analyzer initialized")
    
    def analyze_change_for_invasion(
        self,
        change_event: ChangeEvent,
        baseline_composite: Optional[TemporalComposite] = None,
        historical_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Analyze a detected change event for invasive species outbreak.
        
        Args:
            change_event: Detected change event
            baseline_composite: Baseline data for comparison
            historical_context: Historical patterns at location
            
        Returns:
            Detailed analysis of invasion likelihood
        """
        prompt = self._build_outbreak_detection_prompt(
            change_event, baseline_composite, historical_context
        )
        
        try:
            response = self.client.messages.create(
                model=self.MODEL,
                max_tokens=2000,
                messages=[{"role": "user", "content": prompt}]
            )
            
            analysis = self._parse_outbreak_analysis(response.content[0].text)
            analysis['change_event_metadata'] = {
                'location': change_event.location,
                'detection_date': change_event.detection_date.isoformat(),
                'change_type': change_event.change_type,
                'magnitude': change_event.magnitude
            }
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error in outbreak analysis: {str(e)}")
            return {
                'error': str(e),
                'outbreak_likelihood': 0,
                'invasive_species_detected': False
            }
    
    def analyze_temporal_progression(
        self,
        change_events: List[ChangeEvent],
        location_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyze temporal progression of changes for invasion patterns.
        
        Args:
            change_events: List of change events over time
            location_context: Environmental context of location
            
        Returns:
            Temporal invasion analysis
        """
        prompt = self._build_temporal_invasion_prompt(change_events, location_context)
        
        try:
            response = self.client.messages.create(
                model=self.MODEL,
                max_tokens=2500,
                messages=[{"role": "user", "content": prompt}]
            )
            
            return self._parse_temporal_analysis(response.content[0].text)
            
        except Exception as e:
            logger.error(f"Error in temporal analysis: {str(e)}")
            return {'error': str(e)}
    
    def analyze_spatial_spread_pattern(
        self,
        center_changes: List[ChangeEvent],
        surrounding_changes: Dict[str, List[ChangeEvent]],
        environmental_factors: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Analyze spatial spread patterns for invasion characteristics.
        
        Args:
            center_changes: Changes at center location
            surrounding_changes: Changes in surrounding areas by direction
            environmental_factors: Wind, water flow, terrain data
            
        Returns:
            Spatial invasion spread analysis
        """
        prompt = self._build_spatial_spread_prompt(
            center_changes, surrounding_changes, environmental_factors
        )
        
        try:
            response = self.client.messages.create(
                model=self.MODEL,
                max_tokens=2000,
                messages=[{"role": "user", "content": prompt}]
            )
            
            return self._parse_spatial_analysis(response.content[0].text)
            
        except Exception as e:
            logger.error(f"Error in spatial analysis: {str(e)}")
            return {'error': str(e)}
    
    def generate_outbreak_alert(
        self,
        location: Tuple[float, float],
        analysis_results: Dict[str, Any],
        severity_threshold: float = 0.7
    ) -> Dict[str, Any]:
        """Generate detailed outbreak alert based on analysis.
        
        Args:
            location: Location coordinates
            analysis_results: Combined analysis results
            severity_threshold: Threshold for high-severity alerts
            
        Returns:
            Detailed outbreak alert
        """
        prompt = self._build_alert_generation_prompt(location, analysis_results)
        
        try:
            response = self.client.messages.create(
                model=self.MODEL,
                max_tokens=1500,
                messages=[{"role": "user", "content": prompt}]
            )
            
            alert = self._parse_alert_response(response.content[0].text)
            
            # Add severity classification
            if alert.get('outbreak_confidence', 0) > severity_threshold:
                alert['severity'] = 'HIGH'
                alert['immediate_action_required'] = True
            else:
                alert['severity'] = 'MODERATE'
                alert['immediate_action_required'] = False
            
            return alert
            
        except Exception as e:
            logger.error(f"Error generating alert: {str(e)}")
            return {'error': str(e)}
    
    def _build_outbreak_detection_prompt(
        self,
        change_event: ChangeEvent,
        baseline: Optional[TemporalComposite],
        historical: Optional[Dict[str, Any]]
    ) -> str:
        """Build detailed prompt for outbreak detection."""
        
        # Format change details
        change_details = {
            'date': change_event.detection_date.strftime('%Y-%m-%d'),
            'type': change_event.change_type,
            'magnitude': change_event.magnitude,
            'confidence': change_event.confidence,
            'affected_bands': change_event.affected_bands,
            'anomalies': change_event.metadata.get('anomalies', [])
        }
        
        # Format baseline if available
        baseline_info = ""
        if baseline:
            baseline_info = f"""
Baseline Period: {baseline.start_date.strftime('%Y-%m-%d')} to {baseline.end_date.strftime('%Y-%m-%d')}
Number of baseline images: {baseline.num_images}
Baseline statistics:
{json.dumps(baseline.median_values, indent=2)}
"""
        
        prompt = f"""You are an expert in invasive species detection using satellite imagery analysis. 
Analyze the following detected change event and determine if it indicates an invasive species outbreak.

DETECTED CHANGE EVENT:
{json.dumps(change_details, indent=2)}

Location: {change_event.location[1]}°N, {change_event.location[0]}°E
{baseline_info}

CRITICAL INDICATORS TO ANALYZE:

1. SPECTRAL ANOMALY PATTERNS:
   - Sudden increases in NIR (B8) coupled with changes in red edge bands
   - Unusual green reflectance indicating non-native vegetation
   - Changes that don't match typical seasonal patterns

2. TEMPORAL CHARACTERISTICS:
   - Speed of change (rapid changes often indicate invasive spread)
   - Timing relative to growing season
   - Persistence of changes over multiple observations

3. MAGNITUDE AND EXTENT:
   - Scale of spectral changes
   - Number of bands affected
   - Consistency across wavelengths

4. INVASION-SPECIFIC SIGNATURES:
   - Water hyacinth: High NIR, low red, rapid expansion in summer
   - Kudzu: Progressive canopy coverage, high vegetation indices
   - Purple loosestrife: Distinctive flowering spectral signature
   - General invasives: Homogeneous spectral response, rapid spread

Please provide a DETAILED analysis including:

1. OUTBREAK LIKELIHOOD (0-100%): Your confidence this represents an invasive species outbreak

2. KEY EVIDENCE: List specific spectral/temporal evidence supporting your assessment
   - What exact patterns suggest invasion?
   - Which spectral bands show the most concerning changes?
   - How do the changes differ from normal vegetation dynamics?

3. SPECIES IDENTIFICATION: If patterns match known invasive species, identify them

4. OUTBREAK STAGE:
   - Early detection (small patches beginning to establish)
   - Active spread (rapid expansion phase)
   - Established invasion (large area coverage)

5. DETAILED REASONING: Explain step-by-step why you believe this is/isn't an outbreak
   - Connect specific data points to invasion characteristics
   - Rule out alternative explanations (seasonal change, agriculture, etc.)

6. CONFIDENCE FACTORS: What increases or decreases your confidence?

7. RECOMMENDED ACTIONS: Based on the analysis

Format your response as JSON with the following structure:
{{
  "outbreak_likelihood": <0-100>,
  "invasive_species_detected": <boolean>,
  "key_evidence": [list of specific evidence points],
  "possible_species": [list of likely species with confidence],
  "outbreak_stage": "early|active|established|none",
  "detailed_reasoning": "comprehensive explanation",
  "confidence_factors": {{
    "increasing_confidence": [factors],
    "decreasing_confidence": [factors]
  }},
  "alternative_explanations": [other possible causes],
  "recommended_actions": [specific recommendations],
  "urgency_level": "immediate|high|moderate|low"
}}"""
        
        return prompt
    
    def _build_temporal_invasion_prompt(
        self,
        events: List[ChangeEvent],
        context: Dict[str, Any]
    ) -> str:
        """Build prompt for temporal invasion analysis."""
        
        # Format temporal sequence
        temporal_data = []
        for event in sorted(events, key=lambda x: x.detection_date):
            temporal_data.append({
                'date': event.detection_date.strftime('%Y-%m-%d'),
                'magnitude': event.magnitude,
                'type': event.change_type,
                'affected_bands': event.affected_bands
            })
        
        prompt = f"""Analyze this temporal sequence of changes for invasive species outbreak patterns.

TEMPORAL CHANGE SEQUENCE:
{json.dumps(temporal_data, indent=2)}

LOCATION CONTEXT:
{json.dumps(context, indent=2)}

Analyze for:

1. INVASION PROGRESSION PATTERNS:
   - Is the rate of change accelerating (exponential growth)?
   - Do changes follow known invasive species phenology?
   - Are there sudden jumps indicating rapid colonization?

2. SEASONAL ALIGNMENT:
   - Do changes align with invasive species growing seasons?
   - Are changes occurring outside normal vegetation cycles?

3. SPREAD DYNAMICS:
   - Linear vs exponential growth patterns
   - Pulsed expansion (sudden bursts of growth)
   - Continuous steady spread

4. CRITICAL THRESHOLDS:
   - Have changes crossed thresholds indicating establishment?
   - Is there evidence of reproductive maturity (spectral signatures of flowering)?

Provide detailed analysis as JSON:
{{
  "invasion_progression_detected": <boolean>,
  "growth_pattern": "exponential|linear|pulsed|stable",
  "invasion_phase": "colonization|establishment|spread|saturation",
  "phenological_match": {{
    "matches_invasive_patterns": <boolean>,
    "specific_patterns": [list],
    "confidence": <0-100>
  }},
  "spread_rate_analysis": {{
    "rate_classification": "rapid|moderate|slow",
    "doubling_time_days": <number or null>,
    "acceleration_detected": <boolean>
  }},
  "critical_events": [
    {{
      "date": "YYYY-MM-DD",
      "event_type": "description",
      "significance": "explanation"
    }}
  ],
  "detailed_temporal_reasoning": "comprehensive explanation",
  "outbreak_timeline": {{
    "likely_start_date": "YYYY-MM-DD",
    "current_phase": "description",
    "projected_progression": "prediction"
  }}
}}"""
        
        return prompt
    
    def _build_spatial_spread_prompt(
        self,
        center: List[ChangeEvent],
        surrounding: Dict[str, List[ChangeEvent]],
        environmental: Optional[Dict[str, Any]]
    ) -> str:
        """Build prompt for spatial spread analysis."""
        
        # Format spatial data
        spatial_summary = {
            'center': len(center),
            'directional_changes': {}
        }
        
        for direction, events in surrounding.items():
            if events:
                spatial_summary['directional_changes'][direction] = {
                    'num_events': len(events),
                    'max_magnitude': max(e.magnitude for e in events),
                    'dates': [e.detection_date.strftime('%Y-%m-%d') for e in events]
                }
        
        env_context = json.dumps(environmental, indent=2) if environmental else "Not provided"
        
        prompt = f"""Analyze spatial spread patterns to identify invasive species outbreak characteristics.

SPATIAL CHANGE PATTERN:
Center location changes: {len(center)} events
Surrounding changes by direction:
{json.dumps(spatial_summary, indent=2)}

ENVIRONMENTAL CONTEXT:
{env_context}

Analyze for:

1. SPREAD DIRECTIONALITY:
   - Is spread uniform or directional?
   - Do patterns suggest wind/water dispersal?
   - Are there barriers to spread in certain directions?

2. INVASION FRONT CHARACTERISTICS:
   - Sharp boundaries (aggressive invader)?
   - Diffuse spread (multiple establishment points)?
   - Jump dispersal (long-distance colonization)?

3. SPREAD MECHANISMS:
   - Natural dispersal patterns
   - Human-mediated spread indicators
   - Waterway-following patterns

4. OUTBREAK EPICENTER:
   - Is the center the origin point?
   - Multiple introduction sites?
   - Source-sink dynamics?

Provide detailed spatial analysis as JSON:
{{
  "spatial_outbreak_pattern": "uniform|directional|patchy|jumping",
  "primary_spread_directions": [list of directions],
  "spread_mechanism": {{
    "likely_mechanism": "wind|water|animal|human|mixed",
    "evidence": [specific observations],
    "confidence": <0-100>
  }},
  "invasion_front_analysis": {{
    "front_type": "advancing|stable|retreating",
    "expansion_rate_m_per_month": <number or null>,
    "boundary_characteristics": "sharp|diffuse|irregular"
  }},
  "epicenter_analysis": {{
    "center_is_origin": <boolean>,
    "multiple_introductions": <boolean>,
    "reasoning": "explanation"
  }},
  "barriers_and_corridors": {{
    "spread_barriers": [identified barriers],
    "spread_corridors": [identified pathways]
  }},
  "detailed_spatial_reasoning": "comprehensive explanation",
  "management_implications": [specific recommendations based on spread pattern]
}}"""
        
        return prompt
    
    def _build_alert_generation_prompt(
        self,
        location: Tuple[float, float],
        analysis: Dict[str, Any]
    ) -> str:
        """Build prompt for generating detailed outbreak alert."""
        
        prompt = f"""Generate a detailed invasive species outbreak alert based on the following analysis.

LOCATION: {location[1]}°N, {location[0]}°E
ANALYSIS RESULTS:
{json.dumps(analysis, indent=2)}

Create a comprehensive alert that:

1. CLEARLY STATES THE THREAT LEVEL
2. EXPLAINS THE EVIDENCE IN NON-TECHNICAL TERMS
3. PROVIDES SPECIFIC ACTIONABLE RECOMMENDATIONS
4. INCLUDES URGENCY TIMELINE

Format as JSON:
{{
  "alert_title": "concise title",
  "outbreak_confidence": <0-100>,
  "threat_summary": "2-3 sentence summary for decision makers",
  "key_findings": [
    "finding 1 with evidence",
    "finding 2 with evidence"
  ],
  "species_identification": {{
    "most_likely": "species name or unknown",
    "confidence": <0-100>,
    "identifying_features": [list]
  }},
  "spread_assessment": {{
    "current_extent_hectares": <number or estimate>,
    "spread_rate": "description",
    "direction": "primary directions"
  }},
  "recommended_actions": [
    {{
      "action": "specific action",
      "timeline": "when to complete",
      "priority": "immediate|high|medium"
    }}
  ],
  "technical_details": "paragraph with specific evidence",
  "monitoring_recommendations": [specific monitoring steps]
}}"""
        
        return prompt
    
    def _parse_outbreak_analysis(self, response: str) -> Dict[str, Any]:
        """Parse outbreak detection response."""
        try:
            if '```json' in response:
                json_start = response.find('```json') + 7
                json_end = response.find('```', json_start)
                json_str = response[json_start:json_end].strip()
                return json.loads(json_str)
            return json.loads(response)
        except:
            logger.warning("Failed to parse JSON response")
            return {
                'outbreak_likelihood': 0,
                'invasive_species_detected': False,
                'detailed_reasoning': response,
                'parse_error': True
            }
    
    def _parse_temporal_analysis(self, response: str) -> Dict[str, Any]:
        """Parse temporal analysis response."""
        try:
            if '```json' in response:
                json_start = response.find('```json') + 7
                json_end = response.find('```', json_start)
                json_str = response[json_start:json_end].strip()
                return json.loads(json_str)
            return json.loads(response)
        except:
            return {'temporal_analysis': response, 'parse_error': True}
    
    def _parse_spatial_analysis(self, response: str) -> Dict[str, Any]:
        """Parse spatial analysis response."""
        try:
            if '```json' in response:
                json_start = response.find('```json') + 7
                json_end = response.find('```', json_start)
                json_str = response[json_start:json_end].strip()
                return json.loads(json_str)
            return json.loads(response)
        except:
            return {'spatial_analysis': response, 'parse_error': True}
    
    def _parse_alert_response(self, response: str) -> Dict[str, Any]:
        """Parse alert generation response."""
        try:
            if '```json' in response:
                json_start = response.find('```json') + 7
                json_end = response.find('```', json_start)
                json_str = response[json_start:json_end].strip()
                return json.loads(json_str)
            return json.loads(response)
        except:
            return {
                'alert_title': 'Invasive Species Alert',
                'threat_summary': response[:200],
                'parse_error': True
            }