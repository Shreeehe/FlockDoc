"""
Image Analyzer - Gemini Vision for droppings and symptom analysis
"""

from google import genai
from google.genai import types
from PIL import Image
import io
import base64
from typing import Dict, List

class ImageAnalyzer:
    def __init__(self):
        """Initialize the image analyzer"""
        self.analysis_prompt = self._create_analysis_prompt()
    
    def _create_analysis_prompt(self) -> str:
        """Create the prompt for image analysis"""
        return """You are an expert poultry veterinarian analyzing an image of chicken droppings or visual symptoms.

Analyze the image and provide:

1. DROPPINGS TYPE: Identify the type (normal, bloody, greenish, yellowish, whitish, watery, foamy, mucoid)

2. COLOR ANALYSIS: Describe the colors present and what they indicate

3. HEALTH INDICATORS: List specific health indicators visible in the image

4. POSSIBLE CONDITIONS: List possible diseases or conditions based on visual analysis:
   - If bloody/dark red: Consider Coccidiosis
   - If greenish: Consider Newcastle disease, bile issues, reduced feed intake
   - If yellowish: Consider bacterial infections, liver issues
   - If whitish/chalky: Consider kidney issues, Gumboro, high urates
   - If watery: Consider diarrhea from various causes

5. SEVERITY: Rate as LOW, MODERATE, HIGH, or CRITICAL

6. RECOMMENDATIONS: Provide immediate action recommendations

Respond ONLY in this JSON format:
{
    "droppings_type": "type here",
    "color_analysis": "detailed color description",
    "health_indicators": ["indicator1", "indicator2"],
    "possible_conditions": ["condition1", "condition2"],
    "severity": "LOW|MODERATE|HIGH|CRITICAL",
    "recommendations": ["action1", "action2"]
}

If the image is not of poultry droppings or is unclear, still provide best guess based on what's visible, and note the uncertainty in recommendations."""
    
    async def analyze(
        self,
        image_bytes: bytes,
        bird_type: str,
        api_key: str
    ) -> Dict:
        """
        Analyze an image using Gemini Vision
        """
        try:
            # Create client with API key
            client = genai.Client(api_key=api_key)
            
            # Prepare image
            image = Image.open(io.BytesIO(image_bytes))
            
            # Convert image to bytes for the API
            img_byte_arr = io.BytesIO()
            image.save(img_byte_arr, format=image.format or 'PNG')
            img_byte_arr = img_byte_arr.getvalue()
            
            # Create prompt with context
            full_prompt = f"""Bird Type: {bird_type.upper()}

{self.analysis_prompt}"""
            
            # Generate response with image
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=[
                    types.Content(
                        role="user",
                        parts=[
                            types.Part.from_text(text=full_prompt),
                            types.Part.from_bytes(data=img_byte_arr, mime_type="image/png")
                        ]
                    )
                ]
            )
            
            # Parse response
            result = self._parse_response(response.text)
            return result
            
        except Exception as e:
            # Return default analysis on error
            return {
                "droppings_type": "Unable to determine",
                "color_analysis": f"Analysis error: {str(e)}",
                "health_indicators": ["Image could not be fully analyzed"],
                "possible_conditions": ["Please consult a veterinarian for accurate diagnosis"],
                "severity": "unknown",
                "recommendations": [
                    "Upload a clearer image",
                    "Ensure good lighting",
                    "Take photo from directly above droppings",
                    "Consult a local veterinarian if concerned"
                ]
            }
    
    def _parse_response(self, response_text: str) -> Dict:
        """Parse Gemini response into structured format"""
        import json
        
        try:
            # Try to extract JSON from response
            # Handle cases where response might have extra text
            json_start = response_text.find("{")
            json_end = response_text.rfind("}") + 1
            
            if json_start != -1 and json_end > json_start:
                json_str = response_text[json_start:json_end]
                result = json.loads(json_str)
                
                # Validate required fields
                required_fields = ["droppings_type", "color_analysis", "health_indicators", 
                                   "possible_conditions", "severity", "recommendations"]
                
                for field in required_fields:
                    if field not in result:
                        result[field] = self._get_default_value(field)
                
                return result
            else:
                # No JSON found, create structured response from text
                return self._create_fallback_response(response_text)
                
        except json.JSONDecodeError:
            return self._create_fallback_response(response_text)
    
    def _get_default_value(self, field: str):
        """Get default value for a field"""
        defaults = {
            "droppings_type": "Unknown",
            "color_analysis": "Unable to determine",
            "health_indicators": [],
            "possible_conditions": [],
            "severity": "unknown",
            "recommendations": ["Consult a veterinarian"]
        }
        return defaults.get(field, "")
    
    def _create_fallback_response(self, response_text: str) -> Dict:
        """Create a structured response from free-text"""
        return {
            "droppings_type": "Analysis completed",
            "color_analysis": response_text[:200] if len(response_text) > 200 else response_text,
            "health_indicators": ["See detailed analysis above"],
            "possible_conditions": ["Please review the analysis description"],
            "severity": "moderate",
            "recommendations": [
                "Review the analysis carefully",
                "Compare with healthy droppings",
                "Monitor birds for other symptoms",
                "Consult a veterinarian if concerned"
            ]
        }
    
    def get_droppings_guide(self) -> Dict[str, Dict]:
        """Get reference guide for droppings analysis"""
        return {
            "normal": {
                "description": "Brown/gray with white urate cap",
                "indicates": "Healthy digestion",
                "action": "No action needed"
            },
            "bloody": {
                "description": "Red or dark red coloration",
                "indicates": "Intestinal bleeding, likely Coccidiosis",
                "action": "Urgent - start anticoccidial treatment"
            },
            "greenish": {
                "description": "Green or olive colored",
                "indicates": "Bile in droppings, reduced feed intake, possible viral infection",
                "action": "Check for other symptoms, possible Newcastle"
            },
            "yellowish": {
                "description": "Yellow or mustard colored",
                "indicates": "Bacterial infection, liver issues",
                "action": "Consider antibiotic treatment"
            },
            "whitish": {
                "description": "White, chalky appearance",
                "indicates": "Excess urates, kidney issues, viral infections",
                "action": "Ensure adequate water intake, check for IBD"
            },
            "watery": {
                "description": "Very liquid, little solid matter",
                "indicates": "Diarrhea from various causes",
                "action": "Provide electrolytes, identify cause"
            },
            "foamy": {
                "description": "Bubbly or frothy appearance",
                "indicates": "Malabsorption, intestinal upset",
                "action": "Check feed quality, consider probiotics"
            }
        }
