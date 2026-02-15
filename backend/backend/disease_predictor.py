"""
Disease Predictor - Rule-based + AI-enhanced disease prediction
"""

import json
import os
import random
from typing import List, Dict, Optional
from collections import defaultdict

class DiseasePredictor:
    def __init__(self):
        """Initialize the disease predictor with knowledge base"""
        self.data_dir = os.path.join(os.path.dirname(__file__), "..", "data")
        self.diseases = self._load_json("diseases.json")
        self.symptoms = self._load_json("symptoms.json")
        self.treatments = self._load_json("treatments.json")
        self.reference = self._load_json("reference.json")
    
    def _load_json(self, filename: str) -> dict:
        """Load a JSON file from data directory"""
        path = os.path.join(self.data_dir, filename)
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}
    
    def predict(
        self,
        bird_type: str,
        age_days: int,
        breed: str,
        symptoms: List[str],
        mortality_rate: float,
        flock_size: int,
        additional_info: Optional[str] = None
    ) -> dict:
        """
        Predict disease based on input parameters
        Returns comprehensive diagnosis with treatment
        """
        # Get all applicable diseases
        all_diseases = self._get_applicable_diseases(bird_type)
        
        # Score each disease based on symptoms
        disease_scores = self._score_diseases(all_diseases, symptoms, age_days, bird_type)
        
        # Sort by score and get top matches
        sorted_diseases = sorted(disease_scores.items(), key=lambda x: x[1]["score"], reverse=True)
        top_diseases = sorted_diseases[:3]  # Top 3 matches
        
        # Prepare response
        diseases = []
        all_facts = []
        all_prevention = []
        deficiencies = []
        
        for disease_id, score_info in top_diseases:
            if score_info["score"] > 0:
                disease_data = score_info["disease"]
                
                diseases.append({
                    "id": disease_id,
                    "name": disease_data["name"],
                    "category": disease_data.get("category", "unknown"),
                    "match_score": round(score_info["score"] * 100, 1),
                    "matched_symptoms": score_info["matched_symptoms"],
                    "severity": disease_data.get("severity", "moderate"),
                    "causes": disease_data.get("causes", []),
                    "mortality_rate": disease_data.get("mortality_rate", "variable")
                })
                
                all_facts.extend(disease_data.get("facts", []))
                all_prevention.extend(disease_data.get("prevention", []))
                
                if disease_data.get("deficiency_related"):
                    deficiencies.extend(disease_data.get("deficiency", []))
        
        # Determine overall severity
        severity = self._calculate_severity(diseases, mortality_rate, len(symptoms))
        
        # Get treatment recommendations
        treatment = self._get_treatment_recommendations(diseases, severity)
        
        # Calculate confidence
        confidence = self._calculate_confidence(diseases, symptoms)
        
        # Determine if vet is needed
        when_to_call_vet = self._should_call_vet(severity, mortality_rate, diseases)
        
        return {
            "diseases": diseases,
            "severity": severity,
            "treatment": treatment,
            "deficiencies": list(set(deficiencies)) if deficiencies else None,
            "facts": list(set(all_facts))[:5],  # Top 5 unique facts
            "prevention": list(set(all_prevention))[:5],  # Top 5 prevention tips
            "when_to_call_vet": when_to_call_vet,
            "confidence": confidence
        }
    
    def _get_applicable_diseases(self, bird_type: str) -> List[dict]:
        """Get diseases applicable to the bird type"""
        diseases = []
        
        # General diseases
        for disease in self.diseases.get("broiler_diseases", []):
            if bird_type in disease.get("affects", []):
                diseases.append(disease)
        
        # Layer-specific diseases
        if bird_type == "layer":
            diseases.extend(self.diseases.get("layer_specific", []))
        
        # Nutritional deficiencies apply to all
        diseases.extend(self.diseases.get("nutritional_deficiencies", []))
        
        return diseases
    
    def _score_diseases(
        self,
        diseases: List[dict],
        input_symptoms: List[str],
        age_days: int,
        bird_type: str
    ) -> Dict[str, dict]:
        """Score each disease based on symptom match"""
        scores = {}
        symptom_mapping = self.symptoms.get("disease_symptom_mapping", {})
        
        for disease in diseases:
            disease_id = disease["id"]
            disease_symptoms = symptom_mapping.get(disease_id, disease.get("symptoms", []))
            
            # Calculate symptom match score
            matched = []
            for symptom in input_symptoms:
                symptom_lower = symptom.lower().replace(" ", "_")
                for ds in disease_symptoms:
                    if symptom_lower in ds.lower() or ds.lower() in symptom_lower:
                        matched.append(symptom)
                        break
            
            if disease_symptoms:
                match_ratio = len(matched) / len(disease_symptoms)
                input_coverage = len(matched) / len(input_symptoms) if input_symptoms else 0
                
                # Combined score
                score = (match_ratio * 0.6) + (input_coverage * 0.4)
                
                # Age adjustment
                if self._is_age_appropriate(disease, age_days, bird_type):
                    score *= 1.2
                
                scores[disease_id] = {
                    "score": min(score, 1.0),
                    "matched_symptoms": matched,
                    "disease": disease
                }
        
        return scores
    
    def _is_age_appropriate(self, disease: dict, age_days: int, bird_type: str) -> bool:
        """Check if disease is common at this age"""
        age_info = disease.get("age_susceptibility", "").lower()
        
        if "all ages" in age_info:
            return True
        
        if bird_type == "broiler":
            if age_days <= 7 and "young" in age_info:
                return True
            if 21 <= age_days <= 35 and ("3-6 weeks" in age_info or "grower" in age_info):
                return True
        else:  # layer
            if age_days >= 140 and ("production" in age_info or "peak" in age_info):
                return True
        
        return False
    
    def _calculate_severity(
        self,
        diseases: List[dict],
        mortality_rate: float,
        symptom_count: int
    ) -> str:
        """Calculate overall severity"""
        if not diseases:
            return "low"
        
        # Check disease severities
        severities = [d.get("severity", "moderate") for d in diseases]
        
        if "critical" in severities or mortality_rate > 10:
            return "critical"
        elif "high" in severities or mortality_rate > 5:
            return "high"
        elif "moderate" in severities or symptom_count >= 4:
            return "moderate"
        else:
            return "low"
    
    def _get_treatment_recommendations(
        self,
        diseases: List[dict],
        severity: str
    ) -> dict:
        """Get treatment recommendations based on diagnosed diseases"""
        if not diseases:
            return {
                "primary": ["Consult a veterinarian for proper diagnosis"],
                "supportive": ["Provide electrolytes", "Ensure clean water", "Reduce stress"],
                "medications": [],
                "duration": "As advised by veterinarian"
            }
        
        # Get the primary disease
        primary_disease = diseases[0]
        disease_data = primary_disease.get("disease") if isinstance(primary_disease, dict) else primary_disease
        
        # Find disease treatment in knowledge base
        treatment_info = {
            "primary": [],
            "supportive": [],
            "medications": [],
            "duration": "5-7 days (adjust based on response)"
        }
        
        # Get treatment from disease data
        if isinstance(disease_data, dict):
            disease_treatment = disease_data.get("treatment", {})
            treatment_info["primary"] = disease_treatment.get("medications", [])
            treatment_info["supportive"] = disease_treatment.get("supportive", [])
            treatment_info["duration"] = disease_treatment.get("duration", "5-7 days")
        
        # Add general supportive care
        treatment_info["supportive"].extend([
            "Electrolytes in drinking water",
            "Vitamin supplementation (AD3E)",
            "Reduce overcrowding and stress"
        ])
        
        # Remove duplicates
        treatment_info["supportive"] = list(set(treatment_info["supportive"]))[:5]
        
        return treatment_info
    
    def _calculate_confidence(self, diseases: List[dict], symptoms: List[str]) -> float:
        """Calculate prediction confidence"""
        if not diseases or not symptoms:
            return 0.0
        
        # Base confidence on match score and symptom coverage
        top_score = diseases[0].get("match_score", 0) / 100
        symptom_factor = min(len(symptoms) / 5, 1.0)  # More symptoms = more confident
        
        confidence = (top_score * 0.7) + (symptom_factor * 0.3)
        return round(min(confidence, 0.95), 2)  # Cap at 95%
    
    def _should_call_vet(
        self,
        severity: str,
        mortality_rate: float,
        diseases: List[dict]
    ) -> bool:
        """Determine if veterinary attention is needed"""
        if severity in ["critical", "high"]:
            return True
        if mortality_rate > 5:
            return True
        
        # Check for notifiable diseases
        notifiable = ["newcastle", "avian_influenza", "mareks_disease"]
        for disease in diseases:
            if disease.get("id") in notifiable:
                return True
        
        return False
    
    def get_symptom_list(self) -> dict:
        """Get categorized symptom list for UI"""
        return self.symptoms.get("symptom_categories", {})
    
    def get_breeds(self, bird_type: str) -> List[dict]:
        """Get breed list for a bird type"""
        breeds = self.reference.get("common_breeds", {})
        return breeds.get(bird_type, [])
    
    def get_disease_list(self, bird_type: str) -> List[dict]:
        """Get simplified disease list for reference"""
        diseases = self._get_applicable_diseases(bird_type)
        return [
            {
                "id": d["id"],
                "name": d["name"],
                "category": d.get("category", "unknown"),
                "severity": d.get("severity", "moderate")
            }
            for d in diseases
        ]
    
    def get_random_facts(self) -> List[str]:
        """Get random poultry facts"""
        facts = self.reference.get("quick_facts", {})
        all_facts = (
            facts.get("general", []) +
            facts.get("broiler", []) +
            facts.get("layer", [])
        )
        return random.sample(all_facts, min(3, len(all_facts)))
