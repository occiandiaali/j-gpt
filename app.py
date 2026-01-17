import os
import time
from dotenv import load_dotenv
load_dotenv()

import streamlit as st
import google.generativeai as genai

# Gemini API config
API_KEY = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=API_KEY)

# Streamlit page config
st.set_page_config(page_title="Job Applicant Helper Chatbot", layout="centered")
st.title("JobGPT")
st.subheader("Your conversational AI helper chatbot for getting a job")
# st.write("Available LLMs")
# if st.button("Models", type="secondary"):
#     for model in genai.list_models():
#         if 'generateContent' in model.supported_generation_methods:
#             st.write(model.name)           

# Init chat history
if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": "Hi! I'm your job application helper. Share your CV and a job listing, then ask me anything about the job, and its/your suitability."
        }
    ]

# State mgt. for uploader visibility
if "uploader_visible" not in st.session_state:
    st.session_state["uploader_visible"] = False

def show_cv_uploader(state: bool):
    st.session_state["uploader_visible"] = state

# For the JD upload (Link or raw text)
if "jd_uploader_visible" not in st.session_state:
    st.session_state["jd_uploader_visible"] = False

def show_jd_uploader(state: bool):
    st.session_state["jd_uploader_visible"] = state

col1, col2 = st.columns(2)        

# Button to show/hide the uploader
with col1:
    if st.button("Upload your CV", type="secondary"):
        show_cv_uploader(True)
with col2:
    if st.button("Share the job description", type="secondary"):
        show_jd_uploader(True)        


if st.session_state["uploader_visible"]:
    file = st.file_uploader("Please, provide only the supported format(s)", type=["pdf", "txt", "png", "jpg"])
    if file:
        with st.spinner("Processing your file.."):
            time.sleep(2) # Simulate processing duration
            st.success("File upload successful!")
            st.session_state.have_cv = file

if st.session_state["jd_uploader_visible"]:
    link = st.text_input("Job description link", placeholder="e.g. https://joblink.whatever")
    if link:
        st.toast("Something was entered..")                       

def display_msgs():
    """Display all messages in the chat history"""
    for msg in st.session_state.messages:
        author = "user" if msg["role"] == "user" else "assistant"
        with st.chat_message(author):
            st.write(msg["content"])

def friendly_wrap(raw_text):
    """Add a friendly tone to AI responses"""
    return (
        f"{raw_text.strip()}"
        "Would you like me to elaborate any part of this, or do you have other related questions?"
    ) 

# Display existing messages
display_msgs()

# Handle new user input
prompt = st.chat_input("Ask something")

# if prompt:
#     # Add user message to history
#     st.session_state.messages.append({"role": "user", "content": prompt})

#     # Show user message
#     with st.chat_message("user"):
#         st.write(prompt)

#     # Show thinking indicator while processing
#     with st.chat_message("assistant"):
#         placeholder = st.empty()
#         placeholder.write("🤔 Thinking...")

#         # Call Gemini API
#         try:
#             model = genai.GenerativeModel('gemini-2.5-flash')
#             response = model.generate_content(
#                 f"You are a helpful jobs application assessment expert. Please provide a summarized but accurate, and friendly information about: {prompt}"
#             )

#             # Extract response text
#             answer = response.text
#             friendly_answer = friendly_wrap(answer)

#         except Exception as e:
#             friendly_answer = f"I apologize. I encountered an unexpected error: {e}. Or, try repeating what you typed."

#         # Replace thinking indicator with actual response
#         placeholder.write(friendly_answer)

#         # Add assistant's response to history
#         st.session_state.messages.append({"role": "assistant", "content": {friendly_answer}})

#     # Refresh page to show updated chat
#     st.rerun()
if prompt and "have_cv" in st.session_state:
    # Add user message to history
    st.session_state.messages.append({"role": "user", "content": prompt})

    # Show user message
    with st.chat_message("user"):
        st.write(prompt)

    # Show thinking indicator while processing
    with st.chat_message("assistant"):
        placeholder = st.empty()
        placeholder.write("🤔 Thinking...")

        # Call Gemini API
        try:
            model = genai.GenerativeModel('gemini-2.5-flash')
            response = model.generate_content(
                f"You are a helpful jobs application assessment expert. Please provide a summarized but accurate, and friendly information about: {prompt}"
            )

            # Extract response text
            answer = response.text
            friendly_answer = friendly_wrap(answer)

        except Exception as e:
            friendly_answer = f"I apologize. I encountered an unexpected error: {e}. Or, try repeating what you typed."

        # Replace thinking indicator with actual response
        placeholder.write(friendly_answer)

        # Add assistant's response to history
        st.session_state.messages.append({"role": "assistant", "content": {friendly_answer}})

    # Refresh page to show updated chat
    st.rerun()
elif prompt and not "have_cv" in st.session_state:
    st.error("I could use the help of your CV and JD uploads!")                    

