"""
Poultry Health Chatbot - Rich Visual Response System
Generates structured, visually appealing responses with cards, icons, and formatted sections
"""

from google import genai
from dotenv import load_dotenv
from google.genai import types
from typing import Optional, List, Dict
import httpx
import json
import os
import re

class PoultryHealthChatbot:
    def __init__(self, api_key: str):
        """Initialize the chatbot with Gemini API"""
        self.client = genai.Client(api_key=api_key)
        self.model_name = 'gemini-2.5-flash'
        print(f"Chatbot initialized with model: {self.model_name}")
        
        # Load knowledge base
        self.knowledge_base = self._load_knowledge_base()
        
        # System prompt
        self.system_prompt = self._create_system_prompt()
        
        # Greeting keywords
        self.greetings = ["hello", "hi", "hey", "good morning", "good afternoon", "namaste", "help"]
    
    def _load_knowledge_base(self) -> dict:
        """Load disease and symptom data"""
        data_dir = os.path.join(os.path.dirname(__file__), "..", "data")
        knowledge = {}
        
        files = ["diseases.json", "symptoms.json", "treatments.json", "reference.json"]
        for file in files:
            path = os.path.join(data_dir, file)
            if os.path.exists(path):
                with open(path, "r", encoding="utf-8") as f:
                    knowledge[file.replace(".json", "")] = json.load(f)
        
        return knowledge
    
    def _create_system_prompt(self) -> str:
        """Create system prompt for structured responses"""
        return """You are Dr. Chicky 🐔, an expert poultry veterinarian AI. Reply like a REAL VET — short, direct, clinical.

## RULES:
- Keep answers SHORT. Max 2-3 bullet points per section.
- No filler text. No long explanations. Get to the point.
- Use section headers: [DIAGNOSIS] [TREATMENT] [WARNING] [QUESTION]
- Only use sections that are needed. Skip irrelevant ones.
- Max 2 diseases in diagnosis. Give % confidence.
- Treatment = specific drug name + dosage + duration. Be practical.
- If info is missing, ask 1-2 short questions in [QUESTION].

## EXAMPLE (follow this length):

[DIAGNOSIS]
🔴 Coccidiosis (80%) — bloody droppings + age match
🟡 E. coli (40%) — secondary possibility

[TREATMENT]
• Amprolium 20% — 1ml/L drinking water, 5 days
• ORS + vitamins in water for support

[WARNING]
⚠️ Isolate sick birds. Call vet if mortality > 5%.

## NEVER DO:
- Don't repeat the user's question back
- Don't write paragraphs
- Don't say "Based on what you described" or similar filler
- Don't give more than 4 treatment steps

Knowledge: Newcastle, Marek's, AI, IBD, IB, E. coli, Salmonella, CRD, Coccidiosis, mites, vitamin deficiencies."""

    def _is_greeting(self, message: str) -> bool:
        """Check if message is a simple greeting"""
        message_lower = message.lower().strip()
        words = message_lower.split()
        
        # Only match if message is short AND contains greeting as whole word
        if len(words) > 5:
            return False
            
        for greeting in self.greetings:
            # Check if greeting appears as a whole word
            if greeting in words:
                return True
        return False

    def _get_greeting_response(self) -> dict:
        """Return a short greeting response"""
        response = """[GREETING]
🐔 Hi! I'm **Dr. Chicky** — your poultry vet AI.

[QUESTION]
What's going on with your birds? Describe symptoms, upload droppings photos, or ask about a disease."""
        
        return {
            "response": response,
            "suggestions": ["Respiratory problems", "Blood in droppings", "Sudden deaths"],
            "disease_detected": None,
            "response_type": "greeting"
        }

    async def process_message(
        self,
        message: str,
        bird_type: str = "broiler",
        history: Optional[List[Dict]] = None
    ) -> dict:
        """Process a chat message and return a structured response"""
        
        try:
            # Handle simple greetings
            if self._is_greeting(message) and (not history or len(history) == 0):
                return self._get_greeting_response()
            
            # Build context
            context = f"""
User's Message: {message}

Common diseases to consider: Newcastle, Gumboro/IBD, Coccidiosis, E. coli, CRD, Marek's, Avian Influenza

REMEMBER: Use the structured section format with [SECTION] headers!
"""
            
            # Build chat history for context
            chat_history = []
            if history:
                for msg in history[-6:]:
                    role = msg.get("role", "user")
                    content = msg.get("content", "")
                    if role == "assistant":
                        chat_history.append(types.Content(
                            role="model",
                            parts=[types.Part.from_text(text=content)]
                        ))
                    else:
                        chat_history.append(types.Content(
                            role="user",
                            parts=[types.Part.from_text(text=content)]
                        ))
            
            full_prompt = f"{self.system_prompt}\n\n{context}"
            
            if chat_history:
                # Use chat for multi-turn conversation
                chat = self.client.chats.create(
                    model=self.model_name,
                    history=chat_history
                )
                response = chat.send_message(full_prompt)
            else:
                # Simple generate for single turn
                response = self.client.models.generate_content(
                    model=self.model_name,
                    contents=full_prompt
                )
            
            response_text = response.text
            
            # Determine response type based on sections
            response_type = self._detect_response_type(response_text)
            
            # Generate smart suggestions
            suggestions = self._generate_suggestions(response_text)
            
            # Check for disease mentions
            disease = self._detect_disease_mention(response_text)
            
            return {
                "response": response_text,
                "suggestions": suggestions,
                "disease_detected": disease,
                "response_type": response_type
            }
            
        except Exception as e:
            error_str = str(e)
            print(f"Chatbot API Error: {error_str}")  # Log the actual error
            if "quota" in error_str.lower() or "429" in error_str:
                return {
                    "response": """[WARNING]
⚠️ I'm experiencing high demand right now.

[INFO]
Please try again in a moment. Meanwhile, you can:
• Use the **Predict** tab for symptom-based diagnosis
• Check **Tools** for vaccination schedules
• View biosecurity checklists""",
                    "suggestions": ["Try again", "Go to Predict tab", "Check Tools"],
                    "disease_detected": None,
                    "response_type": "error"
                }
            return {
                "response": f"""[WARNING]
❌ I encountered an error processing your request.

[DEBUG]
Error details: {error_str[:200]}

[QUESTION]
Could you please rephrase your question or provide more details about what you're observing?""",
                "suggestions": ["Describe symptoms again", "Start fresh"],
                "disease_detected": None,
                "response_type": "error"
            }
    
    def _detect_response_type(self, text: str) -> str:
        """Detect the type of response based on content"""
        text_lower = text.lower()
        if "[diagnosis]" in text_lower:
            return "diagnosis"
        elif "[treatment]" in text_lower:
            return "treatment"
        elif "[warning]" in text_lower:
            return "warning"
        elif "[greeting]" in text_lower:
            return "greeting"
        return "info"
    
    def _generate_suggestions(self, response_text: str) -> List[str]:
        """Generate suggestions based on response content"""
        text_lower = response_text.lower()
        
        if "[question]" in text_lower:
            # Extract questions and create suggestions
            if "how old" in text_lower or "age" in text_lower:
                return ["Less than 2 weeks old", "2-4 weeks old", "Over a month old"]
            if "how many" in text_lower or "affected" in text_lower:
                return ["Just 1-2 birds", "About 10% of flock", "More than half affected"]
            if "mortality" in text_lower or "died" in text_lower:
                return ["No deaths yet", "1-2 deaths", "Multiple deaths daily"]
        
        if "[diagnosis]" in text_lower:
            return ["What treatment do you recommend?", "How to prevent this?", "Should I call a vet?"]
        
        if "[treatment]" in text_lower:
            return ["What's the dosage?", "How long to treat?", "Any withdrawal period?"]
        
        return ["Tell me more about symptoms", "How to prevent diseases?", "Vaccination schedule"]
    
    def _detect_disease_mention(self, response_text: str) -> Optional[dict]:
        """Check if a specific disease was mentioned"""
        diseases = self.knowledge_base.get("diseases", {})
        response_lower = response_text.lower()
        
        all_diseases = (
            diseases.get("broiler_diseases", []) +
            diseases.get("layer_specific", []) +
            diseases.get("nutritional_deficiencies", [])
        )
        
        for disease in all_diseases:
            if disease["name"].lower() in response_lower:
                return {
                    "id": disease["id"],
                    "name": disease["name"],
                    "severity": disease.get("severity", "unknown")
                }
        
        return None


class OllamaChatbot:
    """Chatbot using local Ollama models"""
    
    def __init__(self, model_name: str = "llama3.2:3b", base_url: str = "http://localhost:11434"):
        """Initialize the chatbot with Ollama"""
        self.model_name = model_name
        self.base_url = base_url
        print(f"OllamaChatbot initialized with model: {self.model_name}")
        
        # Load knowledge base
        self.knowledge_base = self._load_knowledge_base()
        
        # System prompt (same as Gemini version)
        self.system_prompt = self._create_system_prompt()
        
        # Greeting keywords
        self.greetings = ["hello", "hi", "hey", "good morning", "good afternoon", "namaste", "help"]
    
    def _load_knowledge_base(self) -> dict:
        """Load disease and symptom data"""
        data_dir = os.path.join(os.path.dirname(__file__), "..", "data")
        knowledge = {}
        
        files = ["diseases.json", "symptoms.json", "treatments.json", "reference.json"]
        for file in files:
            path = os.path.join(data_dir, file)
            if os.path.exists(path):
                with open(path, "r", encoding="utf-8") as f:
                    knowledge[file.replace(".json", "")] = json.load(f)
        
        return knowledge
    
    def _create_system_prompt(self) -> str:
        """Create system prompt for structured responses"""
        return """You are Dr. Chicky 🐔, an expert poultry veterinarian AI. Reply like a REAL VET — short, direct, clinical.

## RULES:
- Keep answers SHORT. Max 2-3 bullet points per section.
- No filler text. No long explanations. Get to the point.
- Use section headers: [DIAGNOSIS] [TREATMENT] [WARNING] [QUESTION]
- Only use sections that are needed. Skip irrelevant ones.
- Max 2 diseases in diagnosis. Give % confidence.
- Treatment = specific drug name + dosage + duration. Be practical.
- If info is missing, ask 1-2 short questions in [QUESTION].

## EXAMPLE (follow this length):

[DIAGNOSIS]
🔴 Coccidiosis (80%) — bloody droppings + age match
🟡 E. coli (40%) — secondary possibility

[TREATMENT]
• Amprolium 20% — 1ml/L drinking water, 5 days
• ORS + vitamins in water for support

[WARNING]
⚠️ Isolate sick birds. Call vet if mortality > 5%.

## NEVER DO:
- Don't repeat the user's question back
- Don't write paragraphs
- Don't say "Based on what you described" or similar filler
- Don't give more than 4 treatment steps

Knowledge: Newcastle, Marek's, AI, IBD, IB, E. coli, Salmonella, CRD, Coccidiosis, mites, vitamin deficiencies."""

    def _is_greeting(self, message: str) -> bool:
        """Check if message is a simple greeting"""
        message_lower = message.lower().strip()
        words = message_lower.split()
        
        if len(words) > 5:
            return False
            
        for greeting in self.greetings:
            if greeting in words:
                return True
        return False

    def _get_greeting_response(self) -> dict:
        """Return a short greeting response"""
        response = """[GREETING]
🐔 Hi! I'm **Dr. Chicky** — your poultry vet AI.

[QUESTION]
What's going on with your birds? Describe symptoms, upload droppings photos, or ask about a disease."""
        
        return {
            "response": response,
            "suggestions": ["Respiratory problems", "Blood in droppings", "Sudden deaths"],
            "disease_detected": None,
            "response_type": "greeting"
        }

    async def process_message(
        self,
        message: str,
        bird_type: str = "broiler",
        history: Optional[List[Dict]] = None
    ) -> dict:
        """Process a chat message using Ollama API"""
        
        try:
            # Handle simple greetings
            if self._is_greeting(message) and (not history or len(history) == 0):
                return self._get_greeting_response()
            
            # Build messages for Ollama
            messages = [
                {"role": "system", "content": self.system_prompt}
            ]
            
            # Add conversation history
            if history:
                for msg in history[-6:]:
                    role = msg.get("role", "user")
                    if role == "assistant":
                        role = "assistant"
                    messages.append({
                        "role": role,
                        "content": msg.get("content", "")
                    })
            
            # Add current message with context
            context = f"""
User's Message: {message}

Common diseases to consider: Newcastle, Gumboro/IBD, Coccidiosis, E. coli, CRD, Marek's, Avian Influenza

REMEMBER: Use the structured section format with [SECTION] headers!
"""
            messages.append({"role": "user", "content": context})
            
            # Call Ollama API (120s timeout for CPU inference)
            async with httpx.AsyncClient(timeout=120.0) as client:
                print(f"Calling Ollama API: {self.base_url}/api/chat with model {self.model_name}")
                response = await client.post(
                    f"{self.base_url}/api/chat",
                    json={
                        "model": self.model_name,
                        "messages": messages,
                        "stream": False
                    }
                )
                response.raise_for_status()
                result = response.json()
                print(f"Ollama response received, length: {len(str(result))}")
            
            response_text = result.get("message", {}).get("content", "")
            
            # Determine response type based on sections
            response_type = self._detect_response_type(response_text)
            
            # Generate smart suggestions
            suggestions = self._generate_suggestions(response_text)
            
            # Check for disease mentions
            disease = self._detect_disease_mention(response_text)
            
            return {
                "response": response_text,
                "suggestions": suggestions,
                "disease_detected": disease,
                "response_type": response_type
            }
            
        except httpx.ConnectError:
            return {
                "response": """[WARNING]
❌ Cannot connect to Ollama server.

[INFO]
Please make sure Ollama is running:
• Open a terminal and run: `ollama serve`
• Then try again""",
                "suggestions": ["Try again", "Switch to Gemini"],
                "disease_detected": None,
                "response_type": "error"
            }
        except Exception as e:
            error_str = str(e)
            print(f"Ollama API Error: {error_str}")
            return {
                "response": f"""[WARNING]
❌ I encountered an error processing your request.

[DEBUG]
Error details: {error_str[:200]}

[QUESTION]
Could you please rephrase your question or provide more details?""",
                "suggestions": ["Describe symptoms again", "Start fresh"],
                "disease_detected": None,
                "response_type": "error"
            }
    
    def _detect_response_type(self, text: str) -> str:
        """Detect the type of response based on content"""
        text_lower = text.lower()
        if "[diagnosis]" in text_lower:
            return "diagnosis"
        elif "[treatment]" in text_lower:
            return "treatment"
        elif "[warning]" in text_lower:
            return "warning"
        elif "[greeting]" in text_lower:
            return "greeting"
        return "info"
    
    def _generate_suggestions(self, response_text: str) -> List[str]:
        """Generate suggestions based on response content"""
        text_lower = response_text.lower()
        
        if "[question]" in text_lower:
            if "how old" in text_lower or "age" in text_lower:
                return ["Less than 2 weeks old", "2-4 weeks old", "Over a month old"]
            if "how many" in text_lower or "affected" in text_lower:
                return ["Just 1-2 birds", "About 10% of flock", "More than half affected"]
            if "mortality" in text_lower or "died" in text_lower:
                return ["No deaths yet", "1-2 deaths", "Multiple deaths daily"]
        
        if "[diagnosis]" in text_lower:
            return ["What treatment do you recommend?", "How to prevent this?", "Should I call a vet?"]
        
        if "[treatment]" in text_lower:
            return ["What's the dosage?", "How long to treat?", "Any withdrawal period?"]
        
        return ["Tell me more about symptoms", "How to prevent diseases?", "Vaccination schedule"]
    
    def _detect_disease_mention(self, response_text: str) -> Optional[dict]:
        """Check if a specific disease was mentioned"""
        diseases = self.knowledge_base.get("diseases", {})
        response_lower = response_text.lower()
        
        all_diseases = (
            diseases.get("broiler_diseases", []) +
            diseases.get("layer_specific", []) +
            diseases.get("nutritional_deficiencies", [])
        )
        
        for disease in all_diseases:
            if disease["name"].lower() in response_lower:
                return {
                    "id": disease["id"],
                    "name": disease["name"],
                    "severity": disease.get("severity", "unknown")
                }
        
        return None

