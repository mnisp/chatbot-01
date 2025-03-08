import streamlit as st
import requests
import json
import os
import io
from audiorecorder import audiorecorder
from dotenv import load_dotenv

load_dotenv()
DEEPGRAM_API_KEY = os.getenv("DEEPGRAM_API_KEY")

# API URLs(local ollama for chat responses, deepgram for voice transcription)
OLLAMA_URL = "http://localhost:11434/api/chat"
DEEPGRAM_URL = "https://api.deepgram.com/v1/listen"


def stream_response(model_name, messages):
    """
    Sends a conversation history(messages) to Ollama and streams the response.
    Args:
        model_name (str): The name of the LLM model.
        messages (list): A list of conversation history to maintain context
    Returns:
        str: The chatbot's response.
    """
    # Converting input(python objects) into json format, which APIs expect
    headers = {'Content-Type': 'application/json'}
    data = json.dumps({"model": model_name, "messages": messages})

    # Sending http request to OLLAMA_URL, stream=True: Tells the API to send response in chunks
    with requests.post(OLLAMA_URL, data=data, headers=headers, stream=True) as response:
        response.raise_for_status()
        response_text = ""          # this will store the chatbot’s reply as it builds up
        response_area = st.empty()  # Placeholder that updates in real-time as text arrives


        # Reading response line by line, to decode each chunk and display words in real time
        for chunk in response.iter_lines():

            # chunk.decode() converts raw bytes from non-empty chunks into string
            # json.loads() parses that json text to a python dict, and extracts AI response
            if chunk:
                content = json.loads(chunk.decode("utf-8"))["message"]["content"]
                
                if "<|im_end|>" in content:
                    break
                response_text += content
                response_area.markdown(response_text)  # Update UI dynamically

        return response_text.strip()


def transcribe_audio(audio_data):
    """
    Transcribes audio input into text using Deepgram API.
    Args:
        audio_data (bytes): The audio data in WAV format.
    Returns:
        str: The transcribed text or an error message.
    """
    # if not DEEPGRAM_API_KEY:
    #     st.error("Deepgram API key is missing. Check your .env file.")
    #     return ""

    # headers are just the metadata sent with request for verification and specifying data type
    headers = {
        "Authorization": f"Token {DEEPGRAM_API_KEY}",
        "Content-Type": "audio/wav",
    }
    response = requests.post(DEEPGRAM_URL, headers=headers, data=audio_data)

    # if api request succeeds, convert the response into a dictionary and extract transcript(final text output)
    if response.status_code == 200:
        return response.json().get("results", {}).get("channels", [{}])[0].get("alternatives", [{}])[0].get(
            "transcript", "").strip()

    st.error("Error transcribing audio")
    return ""


def handle_chat(user_input):
    """
    Handles user input, updates the conversation history, and generates a chatbot response.
    Args:
        user_input (str): The user's text input.
    """
    if not user_input:
        return

    # Adding user message to streamlit's session state as a dictionary
    st.session_state.messages.append({"role": "user", "content": user_input})

    # Displaying user's message in the chat UI
    with st.chat_message("user"):
        st.markdown(user_input)

    # Get response from the chatbot
    with st.chat_message("assistant"):
        response_text = stream_response("my-chatbot", st.session_state.messages)

    # Saving responses in streamlit's session state, so that chatbot can keep the chat history
    st.session_state.messages.append({"role": "assistant", "content": response_text})


# Streamlit UI Setup
st.set_page_config(page_title="ChatEase - AI Assistant", page_icon="🤖")

st.markdown("<h2 style='text-align: center;'>ChatEase 🤖</h2>", unsafe_allow_html=True)   # by default, sStreamlit blocks raw HTML for security reasons

st.markdown("<p style='text-align: center; color: gray;'>Your friendly AI assistant, now with voice!</p>", unsafe_allow_html=True)

# streamlit resets state on every interaction, so we use st.session_state to ensure past messages stay visible
if "messages" not in st.session_state:
    st.session_state.messages = []

# Displaying chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat Input Section, textbox and the record button
col1, col2 = st.columns([8, 1])
with col1:
    if user_input := st.chat_input("Ask me anything..."):
        handle_chat(user_input)
with col2:
    audio = audiorecorder("၊၊||၊", "|၊၊|၊၊")

# creating in-memory audio buffer and converting recorded audio to WAV(it preserves high quality audio)
if audio:
    audio_buffer = io.BytesIO()
    audio.export(audio_buffer, format="wav")

    # Simultaneously checking & assigning the value of transcribed transcript(using walrus operator)
    if transcript := transcribe_audio(audio_buffer.getvalue()):
        handle_chat(transcript)  # Convert voice to text and handle chat
















