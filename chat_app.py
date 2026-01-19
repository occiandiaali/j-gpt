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
        response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}) 
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
st.markdown("""
            <div class="tooltip">&#9432;
            <span class="tooltiptext">
            Drop/Upload your CV & provide the web-link of a job listing to begin. 
            Click 'Analyze CV vs Job Fit' for relevant feedback, 
            or type a question in the text-field at the bottom to chat with the AI 
            (Wait for the AI's response to each question). 
            Click 'Reset' under the header or 'Start over', when it appears, to clear the page or start over, as appropriate.
            </span>
            </div>
            <style>
            .tooltip{position: relative;display:inline-block;top:10%;left:0;font-size:24px;cursor:pointer}
            .tooltip .tooltiptext{
            position:absolute;
            visibility:hidden;
            width:180px;
            font-size:12px;
            background-color:black;
            color:#fff;
            text-align:center;
            padding:4px;
            border-radius:6px;
            z-index:1
            }
            .tooltip:hover .tooltiptext{visibility: visible;}
            </style>
            """, unsafe_allow_html=True)
st.logo("images/logo-nobg.png", size="large")
st.title("💼 CV + Job Fit Advisor")

if st.button("Reset", width="content", type="secondary"):
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
    st.success("CV received. Ensure there's a job link added before initiating analysis/chat.") 

    st.text_area("Extracted CV Text", cv_text, height=300)

# --- Enter Job URL --- 
job_url = st.text_input("Enter the job description URL to analyze or ask about:", placeholder="e.g. https://joblink.domain") 
job_text = "" 
company_info = "" 
if job_url: 
    try: 
        response = requests.get(job_url, headers={"User-Agent": "Mozilla/5.0"}) 
        soup = BeautifulSoup(response.text, "html.parser") 
        job_text = soup.get_text(separator="\n") 
        st.success("Job description loaded! You may now chat with AI advisor. Or, add a CV for analysis.") 
     
        # --- Simple heuristic: Gemini can infer company name from job_text --- 
        # For now, just display job_text and let Gemini extract company name later 
        #st.text_area("Job Description", job_text, height=300) 
    except Exception as e: st.error(f"Error fetching job description: {e}") 

# --- One-click Fit Analysis ---
if st.button("🔍 Analyze CV vs Job Fit", disabled=not cv_text or not job_text):
    try:
        placeholding = st.empty()
        placeholding.write("🤔 Thinking...")
        heading_shown = False
        full_text = ""

        context = f"""
        Candidate CV:
        {cv_text}

        Job Description:
        {job_text}

        Task:
        Provide a structured analysis:
        - Extract probable company name from {job_text}
        - Comment on company reputation (if the information is available).
        - Candidate key strengths (skills/experience that match).
        - Gaps or missing qualifications.
        - Evaluate cultural fit based on company values and candidate’s background.
        - Probability of fit (low/medium/high).
        - Advice to improve chances.
        - Numeric fit score (0–100) with explanation.
        """
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

    except requests.exceptions.Timeout:
        st.error("⏳ The request took too long and timed out. Please try again later.")

    except requests.exceptions.RequestException as e:
        st.error("⚠️ Network issue detected. Please check your connection.")
        #st.text(f"Details: {e}")

    except Exception as e:
        st.error("❌ Something went wrong while processing your request.")
        st.text(f"Details: {e}")            

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

# --- Chat Interface ---
if "messages" not in st.session_state:
    st.session_state.messages = []

# Initialize lock flag
if "busy" not in st.session_state:
    st.session_state.busy = False    

st.subheader("Chat with AI advisor")

user_input = st.chat_input("Ask about this job...", disabled=not job_text or st.session_state.busy)

if user_input:
    if st.session_state.busy:
        st.warning("⚠️ While jobsGPT is processing a request, please wait until it finishes.")
        st.session_state.busy = False  # unlock
        if st.button("Start over", type="primary"):
            st.rerun()
    else:
        st.session_state.busy = True  # lock
        try:    
            with st.spinner("🤔 Checking..."):
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
                - Respond to the candidate named in {cv_text} with professional advice about {user_input}, using {job_text} for relevant reference.
                """

                #response = model.generate_content(context)
                response = client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=context
                )
            answer = response.text
            st.session_state.messages.append({"role": "assistant", "content": answer})
            if answer:
                st.session_state.busy = False  # unlock
            # Display chat history
            for msg in st.session_state.messages:
                if msg["role"] == "user":
                    st.chat_message("user").write(msg["content"])
                else:
                    st.chat_message("assistant").write(msg["content"])

        except requests.exceptions.Timeout:
            st.error("⏳ The request took too long and timed out. Please try again later.")

        except requests.exceptions.RequestException as e:
            st.error("⚠️ Network issue detected. Please check your connection.")
            #st.text(f"Details: {e}")

        except Exception as e:
            st.error("❌ Something went wrong while processing your request.")
            st.text(f"Details: {e.message}")

        # finally:
        #     st.session_state.busy = False  # unlock        

        # if company_info: 
        #     st.subheader("Company News") 
        #     st.text(fetch_company_news(company_info)) 
        #     st.subheader("Company Reviews (Indeed)") 
        #     st.text(fetch_company_reviews(company_info))
        # 

    # # Display chat history
    # for msg in st.session_state.messages:
    #     if msg["role"] == "user":
    #         st.chat_message("user").write(msg["content"])
    #     else:
    #         st.chat_message("assistant").write(msg["content"])

