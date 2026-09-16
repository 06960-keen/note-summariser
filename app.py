import io
import docx
from PIL import Image
from pydantic import BaseModel, Field
from pypdf import PdfReader
from google import genai
import streamlit as st

# Initialize Gemini Client
client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])

st.set_page_config(page_title="AI Note Summarizer", page_icon="📝", layout="wide")

if "history" not in st.session_state:
    st.session_state.history = []
# ---------- Sidebar ----------
with st.sidebar:
    st.header("⚙️ Settings")

    style = st.selectbox(
        "Summary style:",
        ["Bullet points", "Paragraph", "Explain like I'm 5"],
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
    st.header("🧠 Quiz Options")
    num_questions = st.slider(
        "Number of quiz questions:",
        min_value=1,
        max_value=10,
        value=5,
    )

    st.dvider()
    st.caption("Made for School Project")
    st.caption("Upload notes or paste them, choose a style, then generate.")

    if st.session_state.history:
        st.divider()
        if st.button("🗑️ Clear history"):
            st.session_state.history = []
            st.rerun()
            
st.title("📝 AI Note Summarizer")
st.write("Paste text or upload notes files (PDF, Word, TXT) and diagrams/images (PNG, JPG).")


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


def build_prompt(notes, style, length, language):
    style_instructions = {
        "Bullet points": "Format the summary as clear bullet points grouped under short headings.",
        "Paragraph": "Format the summary as flowing paragraphs, not bullet points.",
        "Explain like I'm 5": "Explain the concepts in very simple language, using simple analogies.",
    }
    length_instructions = {
        "Short": "Keep the summary brief — just the essential points.",
        "Medium": "Give a moderately detailed summary covering main points.",
        "Detailed": "Give a thorough summary covering key concepts and details.",
    }

    if language == "Auto-detect (match my notes)":
        language_instruction = "Detect the note/image language, write response in that language."
    else:
        language_instruction = f"Write response in {language}."

    return (
        "You are a study assistant. Summarize the provided lecture text/images into key concepts.\n\n"
        f"Style: {style_instructions[style]}\n"
        f"Length: {length_instructions[length]}\n"
        f"Language: {language_instruction}\n\n"
        f"Text Notes:\n{notes}"
    )
# Structured JSON Schema for Pop Quiz
class QuizQuestion(BaseModel):
    question: str = Field(description="The question based on notes and images")
    options: list[str] = Field(description="List of 4 distinct choices")
    correct_answer: str = Field(description="Exact string matching the correct option")
    explanation: str = Field(description="Brief explanation of why correct")

class Quiz(BaseModel):
    questions: list[QuizQuestion]

def generate_quiz(notes, images, count, language):
    prompt = (
        f"Generate a {count}-question multiple-choice quiz based on the notes and attached images.\n"
        f"Language instruction: {language}\n\nNotes:\n{notes}"
    )
    
    # Combine prompt text and images for Gemini multimodal execution
    contents = [prompt] + images

    response = client.models.generate_content(
        model="gemini-3-flash-preview",
        contents=contents,
        config={
            "response_mime_type": "application/json",
            "response_schema": Quiz,
        },
    )
    return Quiz.model_validate_json(response.text)

# Upload UI
col1, col2 = st.columns(2)
with col1:
    uploaded_files = st.file_uploader(
        "Upload notes files (PDF, DOCX, TXT):",
        type=["pdf", "docx", "txt"],
        accept_multiple_files=True,
    )
with col2:
    uploaded_images = st.file_uploader(
        "Upload study images/diagrams:",
        type=["png", "jpg", "jpeg", "webp"],
        accept_multiple_files=True,
    )

extracted_text = ""
loaded_images = []

if uploaded_files:
    for file in uploaded_files:
        extracted_text += extract_text_from_file(file) + "\n\n"
    if extracted_text.strip():
        st.success(f"Loaded content from {len(uploaded_files)} file(s).")

if uploaded_images:
    for img_file in uploaded_images:
        img = Image.open(img_file)
        loaded_images.append(img)
    st.image(loaded_images, caption=[f.name for f in uploaded_images], width=150)

user_notes = st.text_area(
    "Paste your lecture notes here:",
    value=extracted_text,
    height=200,
)

generate_clicked = st.button("Generate Summary", type="primary")
 
if generate_clicked:
    if user_notes.strip() or loaded_images:
        with st.spinner("Summarizing text & analyzing images..."):
            prompt = build_prompt(user_notes, style, length, language)
            contents = [prompt] + loaded_images

            response = client.models.generate_content(
                model="gemini-3-flash-preview",
                contents=contents,
            )

            st.session_state.history.append(
                {
                    "notes": user_notes,
                    "images": loaded_images,
                    "summary": response.text,
                    "style": style,
                    "length": length,
                    "language": language,
                }
            )
            if "quiz" in st.session_state:
                del st.session_state.quiz
    else:
        st.warning("Please upload files, images, or enter notes first!")
 

# ---------- Show latest summary ----------
if st.session_state.history:
    latest = st.session_state.history[-1]
    st.subheader("Summary & Study Points")
    st.write(latest["summary"])
 
    st.download_button(
        label="⬇️ Download this summary",
        data=latest["summary"],
        file_name="summary.txt",
        mime="text/plain",
    )

st.divider()

    # Quiz Trigger
    if st.button(f"🎮 Generate Pop Quiz ({num_questions} Questions)"):
        with st.spinner("Creating quiz..."):
            st.session_state.quiz = generate_quiz(
                latest["notes"],
                latest["images"],
                num_questions,
                latest["language"],
            )

    # Quiz Render Form
    if "quiz" in st.session_state and st.session_state.quiz:
        st.subheader("🧠 Memory Recall Quiz")

        with st.form("quiz_form"):
            user_answers = {}
            for idx, q in enumerate(st.session_state.quiz.questions):
                st.write(f"**Q{idx + 1}: {q.question}**")
                user_answers[idx] = st.radio(
                    "Select your answer:",
                    q.options,
                    key=f"q_{idx}",
                    index=None,
                )
                st.write("")

            submitted = st.form_submit_button("Submit Answers")

            if submitted:
                score = 0
                for idx, q in enumerate(st.session_state.quiz.questions):
                    selected = user_answers[idx]
                    if selected == q.correct_answer:
                        st.success(f"Q{idx + 1}: Correct! 🎉 {q.explanation}")
                        score += 1
                    else:
                        st.error(
                            f"Q{idx + 1}: Incorrect. Correct answer: **{q.correct_answer}**. {q.explanation}"
                        )

                st.metric(
                    "Final Score",
                    f"{score} / {len(st.session_state.quiz.questions)}",
                )
 
# ---------- Past results ----------
if len(st.session_state.history) > 1:
    st.divider()
    st.subheader("📚 Past Summaries")
    for i, entry in enumerate(reversed(st.session_state.history[:-1])):
        with st.expander(f"Summary {len(st.session_state.history) - 1 - i} — {entry['style']}, {entry['length']}"):
            st.write(entry["summary"])
            st.download_button(
                label="⬇️ Download",
                data=entry["summary"],
                file_name=f"summary_{len(st.session_state.history) - 1 - i}.txt",
                mime="text/plain",
                key=f"download_{i}",
            )
 
