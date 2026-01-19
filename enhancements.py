import streamlit as st
from google import genai
import requests

client = genai.Client(api_key="YOUR_KEY")

user_message = st.chat_input("Ask about job fit...")

if user_message:
    try:
        with st.spinner("🤔 The gears are spinning..."):
            st.markdown("### Fit Analysis")
            placeholder = st.empty()
            full_text = ""

            # Streaming Gemini output with timeout
            for chunk in client.models.stream_generate_content(
                model="gemini-2.5-flash",
                contents=user_message,
                request_options={"timeout": 15}  # fail fast after 15s
            ):
                if chunk.text:
                    full_text += chunk.text
                    placeholder.markdown(full_text)

        st.success("✅ Done!")

    except requests.exceptions.Timeout:
        st.error("⏳ The request took too long and timed out. Please try again later.")

    except requests.exceptions.RequestException as e:
        st.error("⚠️ Network issue detected. Please check your connection.")
        st.text(f"Details: {e}")

    except Exception as e:
        st.error("❌ Something went wrong while processing your request.")
        st.text(f"Details: {e}")

# 🔑 Key Points
# request_options={"timeout": 15} → sets a 15‑second timeout. Adjust as needed.

# requests.exceptions.Timeout → specifically catches slow network/API stalls.

# requests.exceptions.RequestException → covers other connectivity issues.

# Friendly messages (⏳, ⚠️, ❌) keep the UX clear and human.

# Excellent — let’s make sure your app doesn’t get overwhelmed if users spam Enter in st.chat_input. Streamlit runs top‑to‑bottom on each interaction, so if multiple Gemini calls are triggered at once, they can overlap or crash. The fix is to queue or lock requests so only one runs at a time.

# 🔧 Pattern: Prevent Overlapping Gemini Requests
# You can use a simple session state flag (st.session_state) to track whether a request is already in progress. If the user presses Enter again while Gemini is still crunching, you show a polite message instead of starting another call.

import streamlit as st
from google import genai
import requests

client = genai.Client(api_key="YOUR_KEY")

# Initialize session state flag
if "busy" not in st.session_state:
    st.session_state.busy = False

user_message = st.chat_input("Ask about job fit...")

if user_message:
    if st.session_state.busy:
        st.warning("⚠️ Gemini is already processing a request. Please wait until it finishes.")
    else:
        st.session_state.busy = True  # lock

        try:
            with st.spinner("🤔 The gears are spinning..."):
                st.markdown("### Fit Analysis")
                placeholder = st.empty()
                full_text = ""

                # Streaming Gemini output with timeout
                for chunk in client.models.stream_generate_content(
                    model="gemini-2.5-flash",
                    contents=user_message,
                    request_options={"timeout": 15}
                ):
                    if chunk.text:
                        full_text += chunk.text
                        placeholder.markdown(full_text)

            st.success("✅ Done!")

        except requests.exceptions.Timeout:
            st.error("⏳ The request took too long and timed out. Please try again later.")

        except requests.exceptions.RequestException as e:
            st.error("⚠️ Network issue detected. Please check your connection.")
            st.text(f"Details: {e}")

        except Exception as e:
            st.error("❌ Something went wrong while processing your request.")
            st.text(f"Details: {e}")

        finally:
            st.session_state.busy = False  # unlock


# That sounds like a smart move 👍 — the lock approach is lightweight and keeps things simple. With the st.session_state.busy flag in place, you’ll prevent overlapping Gemini calls without having to juggle a queue.

# Here’s the streamlined version you can drop in and test:
import streamlit as st
from google import genai
import requests

client = genai.Client(api_key="YOUR_KEY")

# Initialize lock flag
if "busy" not in st.session_state:
    st.session_state.busy = False

user_message = st.chat_input("Ask about job fit...")

if user_message:
    if st.session_state.busy:
        st.warning("⚠️ Gemini is already processing a request. Please wait until it finishes.")
    else:
        st.session_state.busy = True  # lock

        try:
            with st.spinner("🤔 The gears are spinning..."):
                st.markdown("### Fit Analysis")
                placeholder = st.empty()
                full_text = ""

                # Streaming Gemini output with timeout
                for chunk in client.models.stream_generate_content(
                    model="gemini-2.5-flash",
                    contents=user_message,
                    request_options={"timeout": 15}
                ):
                    if chunk.text:
                        full_text += chunk.text
                        placeholder.markdown(full_text)

            st.success("✅ Done!")

        except requests.exceptions.Timeout:
            st.error("⏳ The request took too long and timed out. Please try again later.")

        except requests.exceptions.RequestException as e:
            st.error("⚠️ Network issue detected. Please check your connection.")
            st.text(f"Details: {e}")

        except Exception as e:
            st.error("❌ Something went wrong while processing your request.")
            st.text(f"Details: {e}")

        finally:
            st.session_state.busy = False  # unlock


