import streamlit as st
from google import genai

# Initialize Gemini Client (replace with your key from AI Studio)
client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])

st.title("📝 AI Note Summarizer")

user_notes = st.text_area("Paste your lecture notes here:", height=200)

if st.button("Generate Summary"):
    if user_notes.strip():
        with st.spinner("Summarizing..."):
            response = client.models.generate_content(
                model="gemini-3-flash-preview",
                contents=f"You are a study assistant. Summarize these notes into key concepts and bullet points:\n\n{user_notes}",
            )
            st.subheader("Summary & Study Points")
            st.write(response.text)
    else:
        st.warning("Please enter some notes first!")