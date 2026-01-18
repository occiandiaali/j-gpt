import os
import time
import streamlit as st
import requests
from bs4 import BeautifulSoup
import pdfplumber
import xml.etree.ElementTree as ET
from docx import Document

from google import genai
from dotenv import load_dotenv
load_dotenv()

# Gemini API config
API_KEY = st.secrets["general"]["GEMINI_API_KEY"] #os.getenv("GEMINI_API_KEY")

client = genai.Client(api_key=API_KEY)

# --Helper functions --
def fetch_company_reviews(company_name): 
    reviews_text = "" 
    # Example: Indeed company reviews page 
    url = f"https://www.indeed.com/cmp/{company_name}/reviews" 
    try: 
        res = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}) 
        soup = BeautifulSoup(response.text, "html.parser") 
        # Grab some snippets of reviews (class names may change!) 
        snippets = soup.find_all("div") 
        for snip in snippets[:3]: 
            text = snip.get_text(strip=True) 
            if text: 
                reviews_text += "- " + text[:200] + "...\n" 
    except Exception as e: 
        reviews_text = f"Error fetching reviews: {e}" 
    return reviews_text

def fetch_company_news(company_name): 
    news_text = "" 
    url = f"https://news.google.com/search?q={company_name}" 
    try: 
        response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}) 
        soup = BeautifulSoup(response.text, "html.parser") 
        headlines = soup.find_all("a", {"class": "DY5T1d"}) 
        for h in headlines[:5]: 
            news_text += "- " + h.get_text() + "\n" 
    except Exception as e: 
        news_text = f"Error fetching news: {e}" 
    return news_text

st.set_page_config(page_title="CV + Job Fit Advisor", layout="wide")
st.logo("images/logo_white.jpg", size="large")
st.title("💼 CV + Job Fit Advisor")

if st.button("Clear all", type="tertiary"):
    cv_text = ""
    job_text = ""
    company_info = ""
    url = ""
    st.session_state.messages = []
    st.rerun()

# --- Upload CV ---
cv_text = ""
uploaded_file = st.file_uploader("Share your CV", type=["pdf", "xml", "docx"])

# if uploaded_file:
#     with pdfplumber.open(uploaded_file) as pdf:
#         for page in pdf.pages:
#             text = page.extract_text()
#             if text:
#                 cv_text += text + "\n"
#     st.success("CV received and text extracted!")
if uploaded_file: 
    if uploaded_file.name.endswith(".pdf"): 
        with pdfplumber.open(uploaded_file) as pdf: 
            for page in pdf.pages: 
                text = page.extract_text() 
                if text: 
                    cv_text += text + "\n" 

    elif uploaded_file.name.endswith(".xml"): 
        tree = ET.parse(uploaded_file) 
        root = tree.getroot() 
        cv_text = " ".join([elem.text for elem in root.iter() if elem.text]) 

    elif uploaded_file.name.endswith(".docx"): 
        doc = Document(uploaded_file) 
        cv_text = "\n".join([para.text for para in doc.paragraphs]) 
    st.success("CV received and text extracted!") 
    st.text_area("Extracted CV Text", cv_text, height=300)

# # --- Enter Job URL ---
# url = st.text_input("Enter the job description URL:", placeholder="e.g. https://joblink.whatever")
# job_text = ""
# if url:
#     try:
#         response = requests.get(url)
#         soup = BeautifulSoup(response.text, "html.parser")
#         job_text = soup.get_text(separator="\n")
#         st.success("Job description loaded!")
#     except Exception as e:
#         st.error(f"Error fetching job description: {e}")
# --- Enter Job URL --- 
url = st.text_input("Enter the job description URL to analyze or ask about:", placeholder="e.g. https://joblink.whatever") 
job_text = "" 
company_info = "" 
if url: 
    try: 
        response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}) 
        soup = BeautifulSoup(response.text, "html.parser") 
        job_text = soup.get_text(separator="\n") 
        st.success("Job description loaded!") 
        # --- Simple heuristic: Gemini can infer company name from job_text --- 
        # For now, just display job_text and let Gemini extract company name later 
        #st.text_area("Job Description", job_text, height=300) 
    except Exception as e: st.error(f"Error fetching job description: {e}")   

# --- Chat Interface ---
if "messages" not in st.session_state:
    st.session_state.messages = []

st.subheader("Chat with AI advisor")

user_input = st.chat_input("Ask about this job...", disabled=not job_text)

if user_input and (cv_text or job_text):
    with st.spinner("🤔 Genius at work..."):
        st.session_state.messages.append({"role": "user", "content": user_input})
        company_info = job_text

        context = f"""
        Candidate CV:
        {cv_text}

        Job Description:
        {job_text}

        Company Data:
        {company_info}

        Task:
        - Extract probable company name from {job_text} and assign it to {company_info}.
        - Evaluate cultural fit based on company values and candidate’s background.
        - Comment on company reputation (if the information is available).
        - Respond with professional advice to {user_input}, keeping the above in mind, as relevant.
        """

        #response = model.generate_content(context)
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=context
        )
    answer = response.text
    st.session_state.messages.append({"role": "assistant", "content": answer})    

# if company_info: 
#     st.subheader("Company News") 
#     st.text(fetch_company_news(company_info)) 
#     st.subheader("Company Reviews (Indeed)") 
#     st.text(fetch_company_reviews(company_info))
# 

# Display chat history
for msg in st.session_state.messages:
    if msg["role"] == "user":
        st.chat_message("user").write(msg["content"])
    else:
        st.chat_message("assistant").write(msg["content"])

# --- One-click Fit Analysis ---
if st.button("🔍 Analyze CV vs Job Fit", disabled=not cv_text or not job_text):
    placeholding = st.empty()
    placeholding.write("🤔 The gears are spinning...")
    heading_shown = False
    full_text = ""

    context = f"""
    Candidate CV:
    {cv_text}

    Job Description:
    {job_text}

    Task:
    Provide a structured analysis:
    1. Key strengths (skills/experience that match).
    2. Gaps or missing qualifications.
    3. Probability of fit (low/medium/high).
    4. Advise to improve chances.
    5. Numeric fit score (0–100) with explanation.
    """
    # response = client.models.generate_content(
    #     model="gemini-2.5-flash",
    #     contents=context,
    #     stream=True
    # )
    # for chunk in response:
    #     if chunk.text:
    #         full_text += chunk.text
    #         # Show heading only once, when streaming starts
    #         if not heading_shown:
    #             st.markdown("### Fit Analysis")
    #             heading_shown = True

    #         placeholding.markdown(full_text) 
    # Streaming call for the new google.genai api
    for chunk in client.models.generate_content_stream(model="gemini-2.5-flash",contents=context):
        if chunk.text:
            full_text += chunk.text
            if not heading_shown:
                st.markdown("### Fit Analysis")
                heading_shown = True
                #print(chunk.text, end="", flush=True) 
            placeholding.markdown(full_text) 

    st.write("✅ Done!")
