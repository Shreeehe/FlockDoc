"""
Poultry Disease Prediction Chatbot - Main FastAPI Application
Uses Gemini 2.5 Flash Lite for AI-powered disease diagnosis
"""

from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional, List
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from .chatbot import PoultryHealthChatbot, OllamaChatbot
from .disease_predictor import DiseasePredictor
from .image_analyzer import ImageAnalyzer

# Initialize FastAPI app
app = FastAPI(
    title="Poultry Disease Prediction Chatbot",
    description="AI-powered disease diagnosis for broiler and layer chickens",
    version="1.0.0"
)

# CORS middleware for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize components based on AI provider
AI_PROVIDER = os.getenv("AI_PROVIDER", "gemini").lower()
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2:3b")

print(f"AI Provider: {AI_PROVIDER}")

if AI_PROVIDER == "ollama":
    print(f"Using Ollama with model: {OLLAMA_MODEL}")
    chatbot = OllamaChatbot(model_name=OLLAMA_MODEL)
else:
    # Default to Gemini
    GEMINI_API_KEY = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
    if not GEMINI_API_KEY:
        print("WARNING: No API key found! Set GOOGLE_API_KEY or GEMINI_API_KEY in .env file")
        GEMINI_API_KEY = ""
    print(f"API Key loaded: {'Yes (length: ' + str(len(GEMINI_API_KEY)) + ')' if GEMINI_API_KEY else 'No'}")
    chatbot = PoultryHealthChatbot(api_key=GEMINI_API_KEY)

predictor = DiseasePredictor()
image_analyzer = ImageAnalyzer()


# Pydantic models
class ChatMessage(BaseModel):
    message: str
    bird_type: str = "broiler"  # broiler or layer
    conversation_history: Optional[List[dict]] = None

class ChatResponse(BaseModel):
    response: str
    suggestions: Optional[List[str]] = None
    disease_detected: Optional[dict] = None

class PredictionRequest(BaseModel):
    bird_type: str
    age_days: int
    breed: str
    symptoms: List[str]
    mortality_rate: float
    flock_size: int
    additional_info: Optional[str] = None

class PredictionResponse(BaseModel):
    diseases: List[dict]
    severity: str
    treatment: dict
    deficiencies: Optional[List[str]] = None
    facts: List[str]
    prevention: List[str]
    when_to_call_vet: bool
    confidence: float

class ImageAnalysisResponse(BaseModel):
    droppings_type: str
    color_analysis: str
    health_indicators: List[str]
    possible_conditions: List[str]
    severity: str
    recommendations: List[str]

# Routes
@app.get("/")
async def root():
    """Serve the main HTML page"""
    html_path = os.path.join(os.path.dirname(__file__), "..", "index.html")
    if os.path.exists(html_path):
        return FileResponse(html_path)
    return {"message": "Poultry Disease Prediction API", "status": "running"}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "poultry-disease-chatbot"}

@app.get("/style.css")
async def get_css():
    """Serve CSS file"""
    css_path = os.path.join(os.path.dirname(__file__), "..", "style.css")
    return FileResponse(css_path, media_type="text/css")

@app.get("/app.js")
async def get_js():
    """Serve JavaScript file"""
    js_path = os.path.join(os.path.dirname(__file__), "..", "app.js")
    return FileResponse(js_path, media_type="application/javascript")

@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatMessage):
    """
    Chat endpoint for natural language interaction
    """
    try:
        response = await chatbot.process_message(
            message=request.message,
            bird_type=request.bird_type,
            history=request.conversation_history
        )
        return ChatResponse(**response)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/predict", response_model=PredictionResponse)
async def predict_disease(request: PredictionRequest):
    """
    Predict disease based on symptoms and bird information
    """
    try:
        result = predictor.predict(
            bird_type=request.bird_type,
            age_days=request.age_days,
            breed=request.breed,
            symptoms=request.symptoms,
            mortality_rate=request.mortality_rate,
            flock_size=request.flock_size,
            additional_info=request.additional_info
        )
        return PredictionResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/analyze-image", response_model=ImageAnalysisResponse)
async def analyze_image(
    image: UploadFile = File(...),
    bird_type: str = Form("broiler")
):
    """
    Analyze droppings or symptom images
    """
    try:
        # Read image bytes
        image_bytes = await image.read()
        
        # Analyze with Gemini Vision
        result = await image_analyzer.analyze(
            image_bytes=image_bytes,
            bird_type=bird_type,
            api_key=GEMINI_API_KEY
        )
        return ImageAnalysisResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/symptoms")
async def get_symptoms():
    """Get list of all symptoms for selection"""
    return predictor.get_symptom_list()

@app.get("/api/breeds/{bird_type}")
async def get_breeds(bird_type: str):
    """Get list of breeds for a bird type"""
    return predictor.get_breeds(bird_type)

@app.get("/api/diseases/{bird_type}")
async def get_diseases(bird_type: str):
    """Get list of diseases for reference"""
    return predictor.get_disease_list(bird_type)

@app.get("/api/facts")
async def get_random_facts():
    """Get random poultry facts"""
    return predictor.get_random_facts()

@app.get("/api/tools")
async def get_tools_data():
    """Get tools data (vaccination, feed, biosecurity)"""
    tools_path = os.path.join(os.path.dirname(__file__), "..", "data", "tools.json")
    if os.path.exists(tools_path):
        import json
        with open(tools_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

# Mount static files
static_path = os.path.join(os.path.dirname(__file__), "..")
if os.path.exists(static_path):
    app.mount("/static", StaticFiles(directory=static_path), name="static")
