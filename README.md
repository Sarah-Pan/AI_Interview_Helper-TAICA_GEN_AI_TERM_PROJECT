# AI Interview Helper  
TAICA GenAI Term Project

This project is an AI-powered interview practice tool that generates interview questions, evaluates user responses, and provides feedback to help improve interview performance.

## Features
- **Resume upload** (`Home.py`) — users can upload a PDF resume
- **English interview practice** (`pages/1_EN_Interview`)
- **Chinese interview practice** (`pages/2_ZH_Interview`)
- **Automated evaluation** — clarity, structure, tone, and improvement suggestions
- Modular utilities under `utils/`

## Requirements
You must create a **GROQ API Key** to run this project.

1. Visit https://console.groq.com  
2. Sign up and create an API Key  
3. Create a `.env` file in the project root:
```bash
GROQ_API_KEY=your_api_key_here
```

## Installation
```bash
git clone https://github.com/Sarah-Pan/AI_Interview_Helper-TAICA_GEN_AI_TERM_PROJECT-.git
cd AI_Interview_Helper-TAICA_GEN_AI_TERM_PROJECT-
python3 -m venv venv
source venv/bin/activate   # macOS/Linux
pip install -r requirements.txt
```
## Run
```bash
python3 -m streamlit run Home.py 
```

## Project Structure
.  
├── Home.py                 # Resume upload + main entry point  
├── pages/  
│   ├── 1_EN_Interview.py     # English interview practice  
│   ├── 2_ZH_Interview.py     # Chinese interview practice  
├── utils/                  # Helper functions  
├── requirements.txt  
└── README.md

## License
See the LICENSE file included in this repository.

