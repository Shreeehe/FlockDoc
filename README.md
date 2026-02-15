# 🐔 Poultry Health AI - Disease Prediction Chatbot

An AI-powered chatbot for poultry farmers to diagnose diseases in **broiler** and **layer** chickens. Supports both cloud AI (Google Gemini) and local AI (Ollama) for intelligent conversations and disease prediction.

![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.109+-green.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

## ✨ Features

- 🤖 **AI Chatbot**: Natural language conversation about poultry health (Dr. Chicky)
- 🔬 **Disease Prediction**: Symptom-based disease diagnosis with confidence scores
- 📷 **Image Analysis**: Analyze droppings photos for health indicators
- 📚 **Knowledge Base**: Comprehensive information on 30+ poultry diseases
- 💊 **Treatment Recommendations**: Medications, dosages, and supportive care
- 🛡️ **Prevention Tips**: Vaccination schedules and biosecurity checklists
- 🏠 **Dual AI Support**: Use cloud (Gemini) or local (Ollama) AI models

## 🚀 Quick Start

### Prerequisites

- Python 3.10 or higher
- [Ollama](https://ollama.com/) (optional, for local AI)

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/poultry-health-ai.git
cd poultry-health-ai
```

### 2. Setup Virtual Environment

```bash
# Linux/Mac
python3 -m venv .venv
source .venv/bin/activate

# Windows
python -m venv .venv
.\.venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment

Create a `.env` file:

```bash
# For Local AI (Ollama) - Recommended for privacy
AI_PROVIDER=ollama
OLLAMA_MODEL=llama3.2:3b

# For Cloud AI (Gemini) - Requires API key
# AI_PROVIDER=gemini
# GOOGLE_API_KEY=your-api-key-here
```

### 5. Start Ollama (if using local AI)

```bash
# Pull the model first
ollama pull llama3.2:3b

# Start Ollama server
ollama serve
```

### 6. Run the Application

```bash
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

### 7. Open the App

Visit **http://localhost:8000** in your browser.

## 📁 Project Structure

```
poultry-health-ai/
├── index.html              # Main web interface
├── style.css               # Premium dark/light theme styling
├── app.js                  # Frontend application logic
├── backend/
│   ├── main.py             # FastAPI server & routes
│   ├── chatbot.py          # AI chatbots (Gemini + Ollama)
│   ├── disease_predictor.py # Rule-based disease prediction
│   └── image_analyzer.py   # Droppings image analysis
├── data/
│   ├── diseases.json       # Disease database (30+ diseases)
│   ├── symptoms.json       # Symptom categories & mappings
│   ├── treatments.json     # Treatment protocols
│   ├── tools.json          # Vaccination & feed calculators
│   └── reference.json      # Breeds, facts, etc.
├── .env                    # Environment configuration
├── requirements.txt        # Python dependencies
└── pyproject.toml          # Project metadata
```

## 🔌 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Web interface |
| `/api/chat` | POST | Chat with Dr. Chicky AI |
| `/api/predict` | POST | Predict disease from symptoms |
| `/api/analyze-image` | POST | Analyze droppings image |
| `/api/symptoms` | GET | Get symptom categories |
| `/api/breeds/{type}` | GET | Get breeds (broiler/layer) |
| `/api/diseases/{type}` | GET | Get disease list |
| `/api/tools` | GET | Get tools data |
| `/health` | GET | Health check |

## 🤖 AI Providers

### Ollama (Local) - Recommended

Run AI models locally on your machine. No API key required.

```bash
# Supported models
ollama pull llama3.2:3b    # 2GB, fast
ollama pull gemma3:4b      # 3GB, better quality
```

**GPU Support**: Install NVIDIA drivers for faster inference.

### Gemini (Cloud)

Use Google's Gemini API. Requires API key from [Google AI Studio](https://aistudio.google.com/apikey).

```bash
AI_PROVIDER=gemini
GOOGLE_API_KEY=your-key
```

## 🦠 Diseases Covered

### Viral
- Newcastle Disease, Gumboro (IBD), Avian Influenza
- Marek's Disease, Infectious Bronchitis

### Bacterial
- E. coli (Colibacillosis), Mycoplasmosis (CRD)
- Fowl Cholera, Salmonellosis

### Parasitic
- Coccidiosis, Internal worms, External parasites

### Nutritional
- Vitamin A, D, E, B deficiencies
- Calcium deficiency (for layers)

## 🛠️ Technologies

- **Frontend**: HTML5, CSS3 (dark/light themes), Vanilla JavaScript
- **Backend**: Python 3.10+, FastAPI, Uvicorn
- **AI**: Google Gemini 2.5 Flash / Ollama (Llama 3.2, Gemma 3)
- **Image Processing**: Pillow, Google Vision API

## 📄 License

MIT License - Free to use and modify.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📧 Contact

For questions or support, please open an issue on GitHub.

---

**Made with ❤️ for poultry farmers**
