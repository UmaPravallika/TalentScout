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
```bash
curl -fsSL https://ollama.com/install.sh | sh
ollama serve
ollama pull llama3.1
