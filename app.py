# app.py
import json
import os
import time
import datetime
from difflib import get_close_matches

import streamlit as st
import cohere

# ----------------------------
# CONFIG
# ----------------------------
st.set_page_config(page_title="🧠 Mental Health Chatbot", layout="wide")

# ----------------------------
# STYLES (your UI)
# ----------------------------
st.markdown("""
<style>
header, footer, .stAppDeployButton, .stAppHeader { display: none !important; }
.block-container { padding: 0 !important; margin: 0 !important; max-width: 100% !important; }

body, .main {
    background-color: #0e1117 !important;
    color: #fafafa !important;
    font-family: 'Inter', sans-serif !important;
}

/* Navbar */
.navbar {
    position: fixed;
    top: 0; left: 0; right: 0;
    background: rgba(20, 23, 28, 0.92);
    backdrop-filter: blur(10px);
    padding: 1rem;
    text-align: center;
    font-size: 1.5rem;
    font-weight: 700;
    color: white;
    border-bottom: 1px solid #222;
    z-index: 9999;
}

/* Chat box (no 'chat-container' class) */
.chat-box {
    max-width: 820px;
    margin: 6rem auto 5rem;
    height: 78vh;
    overflow-y: auto;
    padding: 1rem 1.5rem;
}

/* Scrollbar */
.chat-box::-webkit-scrollbar { width: 6px; }
.chat-box::-webkit-scrollbar-thumb { background: #444; border-radius: 10px; }

/* Chat bubbles */
.chat-line { display: flex; width: 100%; margin-bottom: 1.2rem; }
.chat-bubble { padding: 1rem 1.2rem; border-radius: 18px; line-height: 1.55; max-width: 70%; box-shadow: 0px 3px 10px rgba(0,0,0,0.35); word-wrap: break-word; }

.user { justify-content: flex-end; }
.user .chat-bubble { background: linear-gradient(135deg, #1a73e8, #3f8efc); color: white; }

.ai { justify-content: flex-start; }
.ai .chat-bubble { background: #2c2f33; color: #f5f5f5; }

/* Compact chat input so it appears quickly */
.stChatInput {
    position: fixed;
    bottom: 0;
    left: 240px;
    right: 0;
    background-color: #111418;
    padding: 0.6rem 1.2rem !important;
    border-top: 1px solid #222;
    z-index: 9999;
}
.stTextInput>div>div>input {
    background: #1a1d23 !important;
    color: white !important;
    padding: 0.7rem 0.9rem !important;
    border-radius: 12px !important;
    border: 1px solid #333 !important;
    font-size: 1rem !important;
}
</style>

<div class="navbar">🧠 Mental Health Chatbot</div>
""", unsafe_allow_html=True)

# ----------------------------
# Load JSON (support both original and intent-format)
# ----------------------------
JSON_PATHS = ["intent_format_1000lines.json", "disease_medicine_doctor_intents.json", "med_doctors_warangal.json", "med_doctors_warangal_intent.json"]
json_file = None
for p in JSON_PATHS:
    if os.path.exists(p):
        json_file = p
        break

if json_file is None:
    st.error("No JSON file found. Please place med_doctors_warangal.json or intent_format_1000lines.json in the app folder.")
    st.stop()

with open(json_file, "r", encoding="utf-8") as f:
    raw = json.load(f)

# Normalize into internal structure: list of disease dicts with keys: name, medicines (list), doctors (list)
disease_data = []

if isinstance(raw, dict) and "intents" in raw:
    for it in raw["intents"]:
        name = it.get("tag") or it.get("intent") or it.get("disease") or ""
        meds = it.get("medicines") or it.get("medicine") or []
        docs = it.get("doctor") or it.get("doctors") or it.get("warangal_doctors") or []
        # if doctor entries are dicts with name/hospital, keep; else leave as-is
        disease_data.append({"name": name, "medicines": meds, "doctors": docs})
elif isinstance(raw, dict) and "diseases" in raw:
    # original format
    for d in raw["diseases"]:
        name = d.get("name") or d.get("disease") or ""
        meds = d.get("medicines") or d.get("medicines_list") or []
        docs = d.get("warangal_doctors") or d.get("warangal_doctors_list") or d.get("warangal_doctors", []) or d.get("doctor", [])
        disease_data.append({"name": name, "medicines": meds, "doctors": docs})
else:
    # try to interpret as list-of-objects
    if isinstance(raw, list):
        for d in raw:
            name = d.get("disease") or d.get("tag") or d.get("intent") or d.get("name") or ""
            meds = d.get("medicines") or d.get("medicine") or []
            docs = d.get("doctor") or d.get("doctors") or []
            disease_data.append({"name": name, "medicines": meds, "doctors": docs})
    else:
        st.error("Unrecognized JSON structure.")
        st.stop()

# Build quick lookup structures (base names)
disease_names = [d["name"] for d in disease_data]
disease_names_lower = [n.lower() for n in disease_names]

# Helper: normalize predicted/queried disease to base by removing prefixes like "acute", "chronic" etc.
def normalize_to_base(name: str) -> str:
    if not name:
        return name
    n = name.strip()
    lower = n.lower()
    # remove common prefixes
    for prefix in ["acute ", "chronic ", "severe ", "mild "]:
        if lower.startswith(prefix):
            n = n[len(prefix):].strip()
            break
    # also if name contains parentheses or extra suffix, strip after '('
    if "(" in n:
        n = n.split("(")[0].strip()
    return n

# Exact base-disease finder (Option 1): match normalized base name exactly against disease list (case-insensitive)
def find_disease_exact(query: str):
    if not query:
        return None
    q = normalize_to_base(query).strip().lower()
    for d in disease_data:
        if d["name"].strip().lower() == q:
            return d
    return None

# Also provide fuzzy fallback (but only after normalization) — still keep Option 1 behavior by preferring exact base
def find_disease_fuzzy(query: str):
    q = normalize_to_base(query).strip().lower()
    # exact first
    exact = find_disease_exact(q)
    if exact:
        return exact
    # fuzzy match from disease names
    matches = get_close_matches(q, disease_names_lower, n=1, cutoff=0.6)
    if matches:
        best = matches[0]
        for d in disease_data:
            if d["name"].strip().lower() == best:
                return d
    return None

# ----------------------------
# Cohere setup
# ----------------------------
COHERE_API_KEY = "sWmE1lyhhw4XomK8LVSW58LlX0fe4ke89B1fxFvz"
co = cohere.Client(COHERE_API_KEY)
COHERE_MODEL = "command-a-03-2025"

def normalize_remedies_text(raw: str):
    if not raw:
        return "<i>No remedies available.</i>"
    text = raw.strip()
    # convert markdown bold to HTML
    text = text.replace("**", "")
    # replace common bullet markers with newline-dash
    for sym in ["•", "–", "—", "•\u00A0"]:
        text = text.replace(sym, "\n- ")
    # split lines and build UL if lines contain '-'
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    if any(ln.startswith("-") for ln in lines):
        items = []
        for ln in lines:
            if ln.startswith("-"):
                items.append(ln.lstrip("- ").strip())
            else:
                items.append(ln)
        return "<ul>" + "".join(f"<li>{it}</li>" for it in items) + "</ul>"
    else:
        # join paragraphs
        return "<br>".join(lines)

def get_remedies_from_cohere(disease_name: str):
    prompt = f"Give 5 simple, safe home remedies for {disease_name}. Use short bullet points, each on a new line. Keep them non-prescriptive."
    try:
        resp = co.chat(model=COHERE_MODEL, message=prompt, temperature=0.6, max_tokens=220)
        text = resp.text
        return normalize_remedies_text(text)
    except Exception as e:
        return f"<i>⚠️ Cohere error: {e}</i>"

# Cohere-based prediction (conservative): returns base disease name or 'unknown'
def predict_disease_from_symptoms(symptoms: str):
    # If user typed a single token that exactly matches base disease, return it
    tokens = [t for t in symptoms.strip().split() if t.strip()]
    if len(tokens) == 1:
        local = find_disease_exact(tokens[0])
        if local:
            return local["name"]
    # Ask Cohere to classify
    prompt = f"""
You are a cautious clinical classifier. Based on the user's symptoms below, return EXACTLY one disease name from the provided list or 'unknown'.

Symptoms:
{symptoms}

Possible conditions:
{', '.join(disease_names)}

Return exactly one value (disease name) or 'unknown'.
"""
    try:
        res = co.chat(model=COHERE_MODEL, message=prompt, temperature=0.15, max_tokens=30)
        predicted = res.text.strip().strip('"').strip()
        # normalize and try to match base
        normalized = normalize_to_base(predicted)
        match = find_disease_exact(normalized)
        if match:
            return match["name"]
        # if the returned predicted is exactly a disease in DB, return
        if find_disease_fuzzy(predicted):
            return find_disease_fuzzy(predicted)["name"]
        return "unknown"
    except Exception:
        return "unknown"

# ----------------------------
# Session state & conversations
# ----------------------------
if "messages" not in st.session_state:
    st.session_state.messages = []  # list of {"role":"user"|"ai", "message": "<html>"}

if "pending_disease" not in st.session_state:
    st.session_state.pending_disease = None

CONV_DIR = "conversations"
os.makedirs(CONV_DIR, exist_ok=True)

def save_conversation_file():
    if not st.session_state.messages:
        return None
    fname = datetime.datetime.now().strftime("%Y%m%d_%H%M%S.json")
    path = os.path.join(CONV_DIR, fname)
    with open(path, "w", encoding="utf-8") as fw:
        json.dump(st.session_state.messages, fw, ensure_ascii=False, indent=2)
    return fname

def list_conversations():
    return sorted([f for f in os.listdir(CONV_DIR) if f.endswith(".json")], reverse=True)

def load_conversation(filename):
    path = os.path.join(CONV_DIR, filename)
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as fr:
            st.session_state.messages = json.load(fr)
        st.session_state.pending_disease = None
        return True
    return False

# ----------------------------
# Sidebar: Chat Logs & Quick Lookup
# ----------------------------
st.sidebar.title("📁 Chat Logs (Saved)")
convs = list_conversations()
if convs:
    selected_log = st.sidebar.selectbox("Open saved chat", [""] + convs)
    if selected_log:
        loaded = load_conversation(selected_log)
        if loaded:
            st.sidebar.success(f"Loaded {selected_log}")
else:
    st.sidebar.write("No saved chats yet.")

st.sidebar.title("🔎 Quick Lookup")
selected_quick = st.sidebar.selectbox("Search disease", [""] + disease_names)
if selected_quick:
    rec = find_disease_exact(selected_quick)
    if rec:
        st.sidebar.markdown(f"**{rec.get('name')}**")
        st.sidebar.markdown("**Medicines:**")
        for m in rec.get("medicines", []):
            st.sidebar.write(f"- {m}")
        st.sidebar.markdown("**Doctors:**")
        for d in rec.get("doctors", [])[:6]:
            # If doctor entries are dicts, format nicely
            if isinstance(d, dict):
                name = d.get("name", "Unknown")
                hosp = d.get("hospital", "")
                spec = d.get("specialization", "")
                st.sidebar.write(f"- {name} ({spec}) — {hosp}")
            else:
                st.sidebar.write(f"- {d}")

# ----------------------------
# Render chat messages
# ----------------------------
st.markdown("<div class='chat-box'>", unsafe_allow_html=True)
for msg in st.session_state.messages:
    role = msg.get("role", "ai")
    st.markdown(f"""<div class="chat-line {role}"><div class="chat-bubble">{msg.get('message')}</div></div>""", unsafe_allow_html=True)
st.markdown("</div>", unsafe_allow_html=True)

# ----------------------------
# Intent keywords (Option A rules)
# ----------------------------
MED_KEYWORDS = ["medicine", "medicines", "tablet", "tablets", "dose", "treatment", "drug", "meds"]
DOC_KEYWORDS = ["doctor", "doctors", "specialist", "hospital", "clinic", "consult", "see a doctor"]
BOTH_KEYWORDS = ["both", "both please", "medicine and doctor", "medicine & doctor", "medicines and doctors"]

def contains_any(text: str, keywords):
    t = text.lower()
    return any(k in t for k in keywords)

def html_bullet_list(items):
    if not items:
        return "<i>None listed</i>"
    return "<ul>" + "".join(f"<li>{it}</li>" for it in items) + "</ul>"

# ----------------------------
# Input handling
# ----------------------------
user_input = st.chat_input("Type your symptoms or question...")

if user_input:
    # store user message first
    st.session_state.messages.append({"role": "user", "message": user_input})

    u = user_input.strip()
    u_lower = u.lower()

    # 1) If pending_disease exists, interpret user input as follow-up choice
    if st.session_state.pending_disease:
        choice = u_lower
        disease_name = st.session_state.pending_disease
        record = find_disease_exact(disease_name)
        if not record:
            reply_html = "Sorry — couldn't find disease details. Try again."
        else:
            if contains_any(choice, MED_KEYWORDS) and not contains_any(choice, DOC_KEYWORDS):
                reply_html = f"<b>💊 Medicines for {record.get('name')}:</b><br>{html_bullet_list(record.get('medicines', []))}"
            elif contains_any(choice, DOC_KEYWORDS) and not contains_any(choice, MED_KEYWORDS):
                docs = record.get("doctors", [])
                docs_html = "<ul>"
                for d in docs:
                    if isinstance(d, dict):
                        docs_html += f"<li><b>{d.get('name','Unknown')}</b> — {d.get('specialization','')} ({d.get('hospital','')})</li>"
                    else:
                        docs_html += f"<li>{d}</li>"
                docs_html += "</ul>"
                reply_html = f"<b>👨‍⚕️ Doctors for {record.get('name')}:</b><br>{docs_html}"
            elif contains_any(choice, BOTH_KEYWORDS) or (contains_any(choice, MED_KEYWORDS) and contains_any(choice, DOC_KEYWORDS)):
                med_html = html_bullet_list(record.get('medicines', []))
                docs = record.get("doctors", [])
                docs_html = "<ul>"
                for d in docs:
                    if isinstance(d, dict):
                        docs_html += f"<li><b>{d.get('name','Unknown')}</b> - ({d.get('hospital','')})</li>"
                    else:
                        docs_html += f"<li>{d}</li>"
                docs_html += "</ul>"
                reply_html = f"<b>💊 Medicines for {record.get('name')}:</b><br>{med_html}<br><b>👨‍⚕️ Doctors:</b><br>{docs_html}"
            else:
                reply_html = "Please type <b>medicine</b>, <b>doctor</b>, or <b>both</b> (or include the disease name)."

        # clear pending flag
        st.session_state.pending_disease = None

        # animate and save
        placeholder = st.empty()
        lines = reply_html.splitlines()
        built = ""
        for line in lines:
            built += line + "\n"
            placeholder.markdown(f"""<div class="chat-line ai"><div class="chat-bubble">{built}</div></div>""", unsafe_allow_html=True)
            time.sleep(0.06)
        st.session_state.messages.append({"role": "ai", "message": reply_html})
        save_conversation_file()
        st.rerun()

    # 2) If message explicitly asks for medicine/doctor/both and includes disease name -> serve without prediction
    elif contains_any(u_lower, MED_KEYWORDS) or contains_any(u_lower, DOC_KEYWORDS) or contains_any(u_lower, BOTH_KEYWORDS):
        # attempt to detect disease name inside message (exact base match preferred)
        found = None
        for name in disease_names:
            if name.lower() in u_lower:
                found = name
                break

        if found:
            rec = find_disease_exact(found)
            if not rec:
                reply_html = "Couldn't find that disease in our database."
            else:
                if contains_any(u_lower, MED_KEYWORDS) and not contains_any(u_lower, DOC_KEYWORDS):
                    reply_html = f"<b>💊 Medicines for {rec.get('name')}:</b><br>{html_bullet_list(rec.get('medicines', []))}"
                elif contains_any(u_lower, DOC_KEYWORDS) and not contains_any(u_lower, MED_KEYWORDS):
                    docs_html = "<ul>" + "".join(
                        f"<li><b>{d.get('name')}</b> — {d.get('specialization')} ({d.get('hospital')})</li>" if isinstance(d, dict) else f"<li>{d}</li>"
                        for d in rec.get('doctors', [])
                    ) + "</ul>"
                    reply_html = f"<b>👨‍⚕️ Doctors for {rec.get('name')}:</b><br>{docs_html}"
                else:
                    med_html = html_bullet_list(rec.get('medicines', []))
                    docs_html = "<ul>" + "".join(
                        f"<li><b>{d.get('name')}</b> — {d.get('specialization')} ({d.get('hospital')})</li>" if isinstance(d, dict) else f"<li>{d}</li>"
                        for d in rec.get('doctors', [])
                    ) + "</ul>"
                    reply_html = f"<b>💊 Medicines for {rec.get('name')}:</b><br>{med_html}<br><b>👨‍⚕️ Doctors:</b><br>{docs_html}"

            # animate & save
            placeholder = st.empty()
            lines = reply_html.splitlines()
            built = ""
            for line in lines:
                built += line + "\n"
                placeholder.markdown(f"""<div class="chat-line ai"><div class="chat-bubble">{built}</div></div>""", unsafe_allow_html=True)
                time.sleep(0.05)
            st.session_state.messages.append({"role": "ai", "message": reply_html})
            save_conversation_file()
            st.rerun()
        else:
            # No disease in the same message → ask for disease name explicitly (no prediction)
            reply_html = "I didn't detect the disease name. Please include the disease (e.g., 'medicine for fever') or describe your symptoms so I can predict."
            st.session_state.messages.append({"role": "ai", "message": reply_html})
            save_conversation_file()
            st.rerun()

    # 3) Otherwise treat message as symptoms → predict & provide remedies (Option 1)
    else:
        # if user typed a single word that matches base disease, use it directly
        matched = None
        toks = [t for t in u.split() if t.strip()]
        if len(toks) == 1:
            local = find_disease_exact(toks[0])
            if local:
                matched = local

        # try to match input phrase directly (exact base)
        if not matched:
            matched = find_disease_exact(u)

        # if still not matched, call classifier
        if not matched:
            predicted = predict_disease_from_symptoms(u)
            if predicted and predicted.lower() != "unknown":
                matched = find_disease_exact(predicted)

        if matched:
            disease_name = matched.get("name")
            remedies_html = get_remedies_from_cohere(disease_name)
            reply_html = f"<b>🤖 Predicted Condition: {disease_name}</b><br><br><b>🌿 Remedies:</b><br>{remedies_html}<br><br>Would you like <b>medicine</b>, <b>doctor</b>, or <b>both</b>?"
            st.session_state.pending_disease = disease_name

            # animate & save
            placeholder = st.empty()
            lines = reply_html.splitlines()
            built = ""
            for line in lines:
                built += line + "\n"
                placeholder.markdown(f"""<div class="chat-line ai"><div class="chat-bubble">{built}</div></div>""", unsafe_allow_html=True)
                time.sleep(0.08)
            st.session_state.messages.append({"role": "ai", "message": reply_html})
            save_conversation_file()
            st.rerun()
        else:
            reply_html = "I couldn't identify the condition. Please describe your symptoms more clearly or name the disease."
            st.session_state.messages.append({"role": "ai", "message": reply_html})
            save_conversation_file()
            st.rerun()
