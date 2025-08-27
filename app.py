# app.py
import json
import streamlit as st
from typing import List, Dict

from prompts import SYSTEM_PROMPT, QUESTION_GENERATOR_PROMPT, FALLBACK_PROMPT
from llm_helper import stream_llm, complete_llm, safe_json_extract
from storage import save_candidate, anonymized_preview

st.set_page_config(page_title="TalentScout – Hiring Assistant", initial_sidebar_state="expanded")
st.title("🧭 TalentScout – Hiring Assistant")

# ---- Session State ----
if "chat_messages" not in st.session_state:
    st.session_state.chat_messages = [{"role": "system", "content": SYSTEM_PROMPT}]

if "candidate" not in st.session_state:
    st.session_state.candidate = {
        "full_name": "",
        "email": "",
        "phone": "",
        "years_of_experience": "",
        "desired_roles": [],
        "location": "",
        "tech_stack": [],
        "answers": {}
    }

if "asked_questions" not in st.session_state:
    st.session_state.asked_questions = {}  # {tech: [q1, q2, ...]}

if "stage" not in st.session_state:
    st.session_state.stage = "greeting"  # greeting -> collecting_info -> generated_questions -> asking_questions -> done

END_KEYWORDS = {"quit", "exit", "bye", "stop", "end"}

# ---- Sidebar ----
with st.sidebar:
    st.markdown("### Settings")
    model = st.text_input("Ollama Model", value="llama3.1", help="Make sure you've pulled this model via `ollama pull llama3.1`")
    temperature = st.slider("Temperature", 0.0, 1.0, 0.5, 0.1)
    st.divider()
    st.markdown("**Data Privacy**")
    st.caption("Candidate data is stored locally in `data/candidates.jsonl`. Emails/phones are masked in previews. Please delete files after evaluation if needed (GDPR hygiene).")

# ---- Helpers ----
def append_and_stream_assistant(text: str):
    st.session_state.chat_messages.append({"role": "assistant", "content": ""})
    with st.chat_message("assistant"):
        st.markdown(text)

def stream_from_llm():
    with st.chat_message("assistant"):
        stream = stream_llm(
            model=model,
            messages=st.session_state.chat_messages,
            temperature=temperature
        )
        full = ""
        for chunk in stream:
            full += chunk
            st.write(chunk)
        st.session_state.chat_messages.append({"role": "assistant", "content": full})

def all_info_collected(cand: Dict) -> bool:
    return all([
        bool(cand["full_name"]),
        bool(cand["email"]),
        bool(cand["phone"]),
        bool(cand["years_of_experience"]),
        bool(cand["desired_roles"]),
        bool(cand["location"]),
        bool(cand["tech_stack"])
    ])

def parse_list(s: str) -> List[str]:
    return [x.strip() for x in s.split(",") if x.strip()]

# ---- Initial greeting ----
if st.session_state.stage == "greeting":
    greeting = (
        "Hello! I’m TalentScout 🤖. I’ll collect a few details and then ask targeted technical questions based on your tech stack. "
        "You can type **quit/exit/bye/stop** anytime to end the chat."
    )
    append_and_stream_assistant(greeting)
    st.session_state.stage = "collecting_info"

# ---- Display chat history (user + assistant; system is hidden) ----
for msg in st.session_state.chat_messages:
    if msg["role"] in ("user", "assistant"):
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

# ---- Information collection form ----
if st.session_state.stage == "collecting_info":
    st.subheader("📋 Candidate Information")
    with st.form("candidate_form", clear_on_submit=False):
        full_name = st.text_input("Full Name", value=st.session_state.candidate["full_name"])
        email = st.text_input("Email Address", value=st.session_state.candidate["email"])
        phone = st.text_input("Phone Number", value=st.session_state.candidate["phone"])
        yoe = st.text_input("Years of Experience (e.g., 2, 3.5)", value=str(st.session_state.candidate["years_of_experience"]))
        desired_roles = st.text_input("Desired Position(s) (comma-separated)", value=", ".join(st.session_state.candidate["desired_roles"]))
        location = st.text_input("Current Location", value=st.session_state.candidate["location"])
        tech_stack = st.text_input("Tech Stack (comma-separated, e.g., Python, Django, PostgreSQL)", value=", ".join(st.session_state.candidate["tech_stack"]))
        submitted = st.form_submit_button("Save & Generate Questions")

    if submitted:
        st.session_state.candidate.update({
            "full_name": full_name.strip(),
            "email": email.strip(),
            "phone": phone.strip(),
            "years_of_experience": yoe.strip(),
            "desired_roles": parse_list(desired_roles),
            "location": location.strip(),
            "tech_stack": parse_list(tech_stack),
        })

        if not all_info_collected(st.session_state.candidate):
            st.warning("Please fill all required fields before proceeding.")
        else:
            # Generate questions per technology
            tech_list_str = ", ".join(st.session_state.candidate["tech_stack"]) or "general software engineering"
            roles_str = ", ".join(st.session_state.candidate["desired_roles"]) or "Software Engineer"

            prompt = QUESTION_GENERATOR_PROMPT.format(
                tech_list=tech_list_str,
                yoe=st.session_state.candidate["years_of_experience"] or "unknown",
                roles=roles_str
            )

            messages = [
                {"role": "system", "content": "You are a helpful assistant that outputs strict JSON only."},
                {"role": "user", "content": prompt}
            ]

            raw = complete_llm(model=model, messages=messages, temperature=0.2)
            data = safe_json_extract(raw) or {"questions": {}}

            # Keep at most 3 questions per tech to keep interview short
            asked = {}
            for tech, qlist in data.get("questions", {}).items():
                if isinstance(qlist, list) and qlist:
                    asked[tech] = qlist[:3]

            st.session_state.asked_questions = asked
            if not asked:
                st.info("Couldn’t generate stack-specific questions. I’ll ask general questions instead.")
                st.session_state.asked_questions = {
                    "general": [
                        "Describe a challenging bug you fixed recently and how you diagnosed it.",
                        "How do you design tests for a new feature to ensure reliability?",
                        "Explain a time you optimized code for performance—what was your strategy?"
                    ]
                }

            st.session_state.stage = "asking_questions"
            st.success("Questions generated. Scroll down to continue the chat.")

# ---- Chat Input & Flow ----
user_input = st.chat_input("Type your reply here…")

def end_conversation():
    farewell = "Thanks for your time! 🎉 TalentScout will review your responses and get back to you about next steps."
    st.session_state.chat_messages.append({"role": "assistant", "content": farewell})
    with st.chat_message("assistant"):
        st.markdown(farewell)
    # Save candidate data
    save_candidate(st.session_state.candidate)
    st.session_state.stage = "done"

if user_input and st.session_state.stage != "done":
    # End keywords
    if user_input.strip().lower() in END_KEYWORDS:
        end_conversation()
    else:
        st.session_state.chat_messages.append({"role": "user", "content": user_input})

        # Fallback steering if off-topic
        if st.session_state.stage in ("collecting_info", "asking_questions"):
            # quick heuristic: if obviously off-topic and not answering current question, steer back
            if len(user_input.strip()) < 2:
                steer_msg = FALLBACK_PROMPT.format(user_message=user_input)
                steer_resp = complete_llm(model=model, messages=[
                    {"role": "system", "content": "Keep it brief and helpful."},
                    {"role": "user", "content": steer_msg}
                ], temperature=0.3)
                st.session_state.chat_messages.append({"role": "assistant", "content": steer_resp})
                with st.chat_message("assistant"):
                    st.markdown(steer_resp)
            else:
                # proceed normally
                stream_from_llm()
        else:
            stream_from_llm()

# ---- Ask the generated technical questions sequentially ----
if st.session_state.stage == "asking_questions":
    st.subheader("🧪 Technical Screening")
    any_left = False
    for tech, questions in st.session_state.asked_questions.items():
        remaining = [q for q in questions if q not in st.session_state.candidate["answers"].get(tech, {})]
        if remaining:
            any_left = True
            with st.expander(f"{tech.upper()} questions"):
                for q in remaining:
                    st.write(f"- **{q}**")
            break

    # Capture an answer to the first remaining question (one at a time via chat)
    if user_input and any_left and user_input.strip().lower() not in END_KEYWORDS:
        # Save answer to the first unanswered question
        for tech, questions in st.session_state.asked_questions.items():
            for q in questions:
                if q not in st.session_state.candidate["answers"].get(tech, {}):
                    st.session_state.candidate["answers"].setdefault(tech, {})[q] = user_input.strip()
                    break
            else:
                continue
            break

    # Move to done if all answered
    done = True
    for tech, questions in st.session_state.asked_questions.items():
        answered = st.session_state.candidate["answers"].get(tech, {})
        if len(answered) < len(questions):
            done = False
            break

    if done:
        end_conversation()
