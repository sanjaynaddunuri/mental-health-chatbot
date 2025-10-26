import streamlit as st
import json
import time
import os
import datetime
import random
import re
import speech_recognition as sr
from langchain_together import Together
from langchain.llms import Cohere
from textblob import TextBlob
from gtts import gTTS
import tempfile

# Set API Key
TOGETHER_API_KEY = "sWmE1lyhhw4XomK8LVSW58LlX0fe4ke89B1fxFvz"

# ✅ Load dataset function (fixed to use relative path)
@st.cache_data
def load_mental_health_data():
    json_path = os.path.join(os.path.dirname(__file__), "text.json")
    with open(json_path, "r", encoding="utf-8") as file:
        return json.load(file)

# System prompt
SYSTEM_PROMPT = """
You are a kind, compassionate, and supportive mental health assistant.  
Your goal is to **uplift, encourage, and provide clear, practical advice** to users in distress.
**Start with a reassuring sentence in CAPITALS and bold**. Provide empowering solutions. Offer achievable steps. Remind users of their strength.
"""

# Initialize models
models = {
    "Mistral AI": Together(model="mistralai/Mistral-7B-Instruct-v0.3", together_api_key=TOGETHER_API_KEY),
    "LLaMA 3.3 Turbo": Together(model="meta-llama/Llama-3-8b-chat-hf", together_api_key=TOGETHER_API_KEY),
    "Cohere Command": Cohere(model="command-xlarge", cohere_api_key="sWmE1lyhhw4XomK8LVSW58LlX0fe4ke89B1fxFvz")
}

# Affirmations
affirmations = [
    "You are stronger than you think 💪",
    "Every day is a new beginning 🌅",
    "You are not alone 🤝",
    "You are doing your best, and that’s enough 🌼"
]

# Save conversation history
def save_conversation(history):
    with open("conversation_history.txt", "w", encoding="utf-8") as file:
        for entry in history:
            file.write(f"[{entry['timestamp']}] {entry['role'].capitalize()}: {entry['message']}\n")

# Text-to-speech
def speak_text(text):
    tts = gTTS(text=text, lang='en')
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp_file:
        tts.save(tmp_file.name)
        audio_file = tmp_file.name
    st.audio(audio_file, format="audio/mp3")

# Voice-to-text
def listen_to_voice():
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        st.info("🎤 Listening... Please speak now.")
        audio = recognizer.listen(source)
    try:
        return recognizer.recognize_google(audio)
    except sr.UnknownValueError:
        return "Sorry, I couldn't understand."
    except sr.RequestError:
        return "Speech recognition service error."

# Mood-based reply adjustment
def adjust_reply(reply, mood):
    mood_adjustments = {
        "Happy 😊": "I'm glad you're feeling good! Here's how to stay positive:",
        "Sad 😢": "I'm really sorry you're feeling this way. Please know things can get better.",
        "Angry 😠": "I understand you're feeling frustrated. Let's work through it calmly.",
        "Anxious 😰": "It's okay to feel anxious. Let's take a deep breath and talk about it."
    }
    return f"{mood_adjustments.get(mood, '')} {reply}"

# Streamlit layout
st.set_page_config(page_title="Mental Health AI Chatbot", layout="centered")
st.title("🧠 Mental Health Support Chatbot")

# Greeting by time
hour = datetime.datetime.now().hour
greeting = "Good Morning" if hour < 12 else ("Good Afternoon" if hour < 17 else "Good Evening")
st.subheader(f"{greeting}, I'm here to help you feel better 🌟")

# Select model
model_name = st.selectbox("Choose your model:", list(models.keys()))
llm = models[model_name]

# Mood input
mood = st.radio("How are you feeling today?", ["Happy 😊", "Sad 😢", "Angry 😠", "Anxious 😰", "Neutral 😐"])

# Session state for chat
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat history
for msg in st.session_state.messages:
    st.markdown(f"**{msg['role'].capitalize()}** [{msg['timestamp']}]: {msg['message']}  {'👍👎' if msg['role']=='ai' else ''}")

# Input method
input_type = st.radio("Input Method:", ["Text", "Voice"])
user_input = ""
if input_type == "Text":
    user_input = st.text_input("You:", key="user_input")
else:
    if st.button("🎙️ Speak"):
        user_input = listen_to_voice()
        st.text_input("Recognized Text:", value=user_input, disabled=True)

# Handle user message
if user_input:
    timestamp = datetime.datetime.now().strftime("%H:%M:%S")
    st.session_state.messages.append({"role": "user", "message": user_input, "timestamp": timestamp})

    full_prompt = f"{SYSTEM_PROMPT}\nUser's mood: {mood}\nUser: {user_input}"
    with st.spinner("Thinking..."):
        reply = llm(full_prompt)
        reply = adjust_reply(reply, mood)
        st.success("Response ready")

    timestamp = datetime.datetime.now().strftime("%H:%M:%S")
    st.session_state.messages.append({"role": "ai", "message": reply, "timestamp": timestamp})

    st.markdown(f"**AI** [{timestamp}]: {reply} 👍👎")
    speak_text(reply)

# Export history
if st.button("📄 Export Chat History"):
    save_conversation(st.session_state.messages)
    st.success("Chat history saved to 'conversation_history.txt'")

# Footer
st.markdown("<hr>", unsafe_allow_html=True)
st.info(random.choice(affirmations))
