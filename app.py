import streamlit as st
from google import genai
from pypdf import PdfReader
import docx
import io

# Initialize Gemini Client (replace with your key from AI Studio)
client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])

st.set_page_config(page_title="AI Note Summarizer", page_icon="📝", layout="wide")

# ---------- Sidebar ----------
with st.sidebar:
    st.header("⚙️ Settings")

    style = st.selectbox(
        "Summary style:",
        ["Bullet points", "Paragraph", "Explain like I'm 5 (ELI5)"],
    )

    length = st.select_slider(
        "Summary length:",
        options=["Short", "Medium", "Detailed"],
        value="Medium",
    )
    language = st.selectbox(
        "Response language:",
        ["Auto-detect (match my notes)", "English", "Thai", "Spanish", "French", "Chinese", "Japanese"],
    )

    st.divider()
    st.caption("Made for School Project")
    st.caption("Upload notes or paste them, choose a style, then generate.")

st.title("📝 AI Note Summarizer")
st.write("Paste your notes below, or upload a file (PDF, Word, or TXT).")


def extract_text_from_file(uploaded_file):
    """Return plain text from an uploaded pdf, docx, or txt file."""
    file_type = uploaded_file.name.split(".")[-1].lower()

    if file_type == "pdf":
        reader = PdfReader(uploaded_file)
        text = "\n".join(page.extract_text() or "" for page in reader.pages)
        return text

    elif file_type == "docx":
        document = docx.Document(io.BytesIO(uploaded_file.read()))
        text = "\n".join(paragraph.text for paragraph in document.paragraphs)
        return text

    elif file_type == "txt":
        return uploaded_file.read().decode("utf-8")

    else:
        return ""


def build_prompt(notes, style, length):
    style_instructions = {
        "Bullet points": "Format the summary as clear bullet points grouped under short headings.",
        "Paragraph": "Format the summary as flowing paragraphs, not bullet points.",
        "Explain like I'm 5 (ELI5)": "Explain the concepts in very simple language, as if teaching a beginner with no background knowledge, using short sentences and simple analogies.",
    }
    length_instructions = {
        "Short": "Keep the summary brief — just the most essential points.",
        "Medium": "Give a moderately detailed summary covering the main points.",
        "Detailed": "Give a thorough, detailed summary covering all key concepts and supporting details.",
    }
    if language == "Auto-detect (match my notes)":
        language_instruction = "Detect the language the notes are written in, and write your entire response in that same language."
    else:
        language_instruction = f"Write your entire response in {language}, regardless of what language the notes are written in."

    return (
        "You are a study assistant. Summarize the following lecture notes into "
        "key concepts and study points.\n\n"
        f"Style: {style_instructions[style]}\n"
        f"Length: {length_instructions[length]}\n\n"
        f"Notes:\n{notes}"
    )


uploaded_file = st.file_uploader(
    "Upload notes file:", type=["pdf", "docx", "txt"]
)

extracted_text = ""
if uploaded_file is not None:
    with st.spinner("Reading file..."):
        extracted_text = extract_text_from_file(uploaded_file)
    if extracted_text.strip():
        st.success(f"Loaded text from {uploaded_file.name}")
    else:
        st.warning("Couldn't find any readable text in that file.")

user_notes = st.text_area(
    "Paste your lecture notes here:",
    value=extracted_text,
    height=200,
)

generate_clicked = st.button("Generate Summary", type="primary")

if generate_clicked:
    if user_notes.strip():
        with st.spinner("Summarizing..."):
            prompt = build_prompt(user_notes, style, length)
            response = client.models.generate_content(
                model="gemini-3-flash-preview",
                contents=prompt,
            )
            st.subheader("Summary & Study Points")
            st.write(response.text)
    else:
        st.warning("Please enter some notes first!")
