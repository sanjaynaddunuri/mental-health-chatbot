import json 
import os
import datetime
import cohere
import streamlit as st
import threading
import time   # 👈 Added for typing animation
# -----------------------------
# PAGE CONFIG
# -----------------------------
st.set_page_config(page_title="🧠 Mental Health Chatbot", layout="wide")

# -----------------------------
# CUSTOM STYLES
# -----------------------------
st.markdown("""
<style>
/* Hide Streamlit header/footer */
header, footer, .stAppDeployButton, .stAppHeader { display: none !important; }
.block-container { padding: 0 !important; margin: 0 !important; max-width: 100% !important; }

/* Global */
body, .main {
    background-color: #0e1117 !important;
    color: #f5f5f5 !important;
    font-family: 'Inter', sans-serif !important;
    overflow-x: hidden !important;
}

/* Navbar */
.navbar {
    position: fixed;
    top: 0; left: 0; right: 0;
    background: rgba(17, 20, 24, 0.9);
    backdrop-filter: blur(10px);
    padding: 1rem 1.5rem;
    text-align: center;
    font-size: 1.6rem;
    font-weight: 700;
    color: #ffffff;
    border-bottom: 1px solid #222;
    box-shadow: 0 2px 8px rgba(0,0,0,0.5);
    z-index: 9999;
}

/* Chat Container */
.chat-container {
    display: flex;
    flex-direction: column;
    max-width: 850px;
    margin: 6rem auto 5rem;
    padding: 1rem 1.5rem;
    background-color: transparent;
    overflow-y: auto;
    max-height: 78vh;
    scroll-behavior: smooth;
}

/* Hide scrollbar until hover */
.chat-container::-webkit-scrollbar { width: 0; }
.chat-container:hover::-webkit-scrollbar { width: 8px; }
.chat-container::-webkit-scrollbar-thumb {
    background-color: #444;
    border-radius: 10px;
}

/* Chat bubbles */
.chat-line {
    display: flex;
    width: 100%;
    margin-bottom: 1rem;
}

.chat-bubble {
    padding: 1rem 1.3rem;
    border-radius: 18px;
    line-height: 1.6;
    max-width: 70%;
    box-shadow: 0 2px 8px rgba(0,0,0,0.3);
    word-wrap: break-word;
}

/* User bubble (right) */
.user {
    justify-content: flex-end;
}
.user .chat-bubble {
    background: linear-gradient(135deg, #1a73e8, #3f8efc);
    color: white;
    border-bottom-right-radius: 6px;
}

/* AI bubble (left) */
.ai {
    justify-content: flex-start;
}
.ai .chat-bubble {
    background: #2c2f33;
    color: #f5f5f5;
    border-bottom-left-radius: 6px;
}

/* Timestamp */
.timestamp {
    font-size: 0.7rem;
    color: #aaa;
    margin-top: 4px;
    text-align: right;
}

/* Input bar (ChatGPT style) */
.stChatInput {
    position: fixed;
    bottom: 0;
    left: 250px; /* adjust if sidebar is hidden */
    right: 0;
    background-color: #111418;
    padding: 1rem 2rem;
    border-top: 1px solid #222;
    box-shadow: 0 -2px 6px rgba(0,0,0,0.4);
    z-index: 999;
}

.stTextInput>div>div>input {
    background-color: #1a1d23 !important;
    color: white !important;
    border-radius: 18px !important;
    padding: 0.9rem 1.2rem !important;
    border: 1px solid #333 !important;
    font-size: 1rem !important;
}
</style>

<!-- Navbar -->
<div class="navbar">🧠 Mental Health Chatbot</div>

<!-- Auto Scroll -->
<script>
let observer = new MutationObserver(() => {
    const chat = window.parent.document.querySelector('.chat-container');
    if (chat) chat.scrollTop = chat.scrollHeight;
});
observer.observe(window.parent.document.body, {childList: true, subtree: true});
</script>
""", unsafe_allow_html=True)


# -----------------------------
# COHERE MODEL SETUP
# -----------------------------
co = cohere.Client("sWmE1lyhhw4XomK8LVSW58LlX0fe4ke89B1fxFvz")

class CohereWrapper:
    def __init__(self, client, model="command-a-03-2025"):
        self.client = client
        self.model = model
    def __call__(self, prompt):
        try:
            res = self.client.chat(model=self.model, message=prompt, temperature=0.8, max_tokens=350)
            return res.text.strip()
        except Exception as e:
            return f"⚠️ Model error: {e}"

llm = CohereWrapper(co)

# -----------------------------
# SYSTEM PROMPT
# -----------------------------
SYSTEM_PROMPT = """
You are a kind, compassionate, and supportive AI therapist.
Provide gentle, motivational, and empathetic advice.
Always respond warmly and positively.
"""

# -----------------------------
# CHAT HISTORY
# -----------------------------
HISTORY_DIR = "conversations"
os.makedirs(HISTORY_DIR, exist_ok=True)

def save_conversation():
    if "messages" in st.session_state and st.session_state.messages:
        file = datetime.datetime.now().strftime("%Y%m%d_%H%M%S.json")
        with open(os.path.join(HISTORY_DIR, file), "w", encoding="utf-8") as f:
            json.dump(st.session_state.messages, f, ensure_ascii=False, indent=2)

def list_histories():
    return sorted([f for f in os.listdir(HISTORY_DIR) if f.endswith(".json")], reverse=True)

def load_history(name):
    with open(os.path.join(HISTORY_DIR, name), "r", encoding="utf-8") as f:
        st.session_state.messages = json.load(f)

# -----------------------------
# SIDEBAR
# -----------------------------
st.sidebar.title("💬 Chat History")
history_files = list_histories()
selected = st.sidebar.selectbox("Select Chat", ["New Chat"] + history_files)
if selected != "New Chat":
    load_history(selected)
else:
    if "messages" not in st.session_state:
        st.session_state.messages = []

# -----------------------------
# MAIN CHAT UI
# -----------------------------
st.markdown("<div class='chat-container' id='chatBox'>", unsafe_allow_html=True)
for msg in st.session_state.messages:
    role_class = "user" if msg["role"] == "user" else "ai"
    bubble_html = f"""
    <div class="chat-line {role_class}">
        <div class="chat-bubble">{msg['message']}
            <div class="timestamp">{msg['timestamp']}</div>
        </div>
    </div>
    """
    st.markdown(bubble_html, unsafe_allow_html=True)
st.markdown("</div>", unsafe_allow_html=True)

# -----------------------------
# INPUT HANDLER WITH TYPING ANIMATION
# -----------------------------
user_input = st.chat_input("Type your message here...")

if user_input:
    ts = datetime.datetime.now().strftime("%H:%M")
    st.session_state.messages.append({"role": "user", "message": user_input, "timestamp": ts})

    with st.spinner("Thinking..."):
        prompt = f"{SYSTEM_PROMPT}\nUser: {user_input}"
        reply = llm(prompt)

    # --- Typing animation for AI reply ---
    typing_placeholder = st.empty()
    typed_text = ""
    for word in reply.split():
        typed_text += word + " "
        typing_placeholder.markdown(
            f"""
            <div class="chat-line ai">
                <div class="chat-bubble">{typed_text.strip()}
                    <div class="timestamp">{datetime.datetime.now().strftime("%H:%M")}</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        time.sleep(0.04)  # typing speed (adjust as needed)

    # Finalize message and save
    ts = datetime.datetime.now().strftime("%H:%M")
    st.session_state.messages.append({"role": "ai", "message": reply, "timestamp": ts})
    save_conversation()
    st.rerun()
