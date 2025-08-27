# TalentScout – AI Hiring Assistant (Streamlit + Ollama)

A local, privacy-conscious hiring assistant that:
- Greets and guides candidates,
- Collects essential info (name, email, phone, YOE, roles, location, tech stack),
- Generates 3 questions per technology from the declared stack,
- Maintains context and handles fallbacks,
- Exits on `quit/exit/bye/stop`,
- Stores anonymized candidate data to `data/candidates.jsonl`.

## Setup

### 1) Install Ollama (local)
curl -fsSL https://ollama.com/install.sh | sh
ollama serve
ollama pull llama3.1

### 2) Install Python deps
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt

### 3) Run
streamlit run app.py
