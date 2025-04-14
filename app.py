# app.py
import streamlit as st
import base64
import google.generativeai as genai
import fitz  # PyMuPDF
from typing import List
import re
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# === PAGE CONFIG ===
st.set_page_config(page_title="Aphasia & Dyslexia Support", layout="wide")

# === GEMINI SETUP ===
genai.configure(api_key="AIzaSyAOyZfNpq1scopeXCMPUejHyGwPKLAFRLI")
gemini_model = genai.GenerativeModel("gemini-2.0-flash")

# === FONT INJECT ===
def inject_opendyslexic_font():
    font_path = "OpendyslexicRegular-nRLZ0.ttf"
    with open(font_path, "rb") as f:
        base64_font = base64.b64encode(f.read()).decode("utf-8")
    st.markdown(f"""
        <style>
        @font-face {{
            font-family: 'OpenDyslexic';
            src: url(data:font/ttf;base64,{base64_font}) format('truetype');
        }}
        .dyslexic {{
            font-family: 'OpenDyslexic', sans-serif;
            font-size: 18px;
            line-height: 1.8;
            white-space: pre-wrap;
        }}
        </style>
    """, unsafe_allow_html=True)

# === HELPERS ===
def chunk_text(text: str, max_words: int = 500) -> List[str]:
    words = text.split()
    return [' '.join(words[i:i + max_words]) for i in range(0, len(words), max_words)]

def simplify_chunk(text: str) -> str:
    prompt = f"""
You are an aphasia support assistant. Simplify this text:
- Use basic vocabulary (A1/A2 CEFR level)
- Max 8 words per sentence
- Always use active voice
- Keep the original meaning

Text: {text}
Simplified version:"""
    return gemini_model.generate_content(prompt).text.strip()

def extract_text_from_pdf(file) -> str:
    doc = fitz.open(stream=file.read(), filetype="pdf")
    text = "\n".join([page.get_text() for page in doc])
    doc.close()
    return text

def extract_text_from_txt(file) -> str:
    return file.read().decode("utf-8")

def generate_pdf_with_opendyslexic(text: str) -> BytesIO:
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    font_path = "OpendyslexicRegular-nRLZ0.ttf"
    pdfmetrics.registerFont(TTFont("OpenDyslexic", font_path))
    c.setFont("OpenDyslexic", 12)
    width, height = A4
    x, y = 40, height - 40
    for line in text.split('\n'):
        if y < 40:
            c.showPage()
            c.setFont("OpenDyslexic", 12)
            y = height - 40
        c.drawString(x, y, line)
        y -= 18
    c.save()
    buffer.seek(0)
    return buffer

# === MAIN APP ===
st.title("🧠 Aphasia and Dyslexia-Friendly Text Simplifier")
inject_opendyslexic_font()

uploaded_file = st.file_uploader("📄 Upload a PDF or TXT file", type=["pdf", "txt"])

if uploaded_file:
    with st.spinner("🔍 Extracting and simplifying..."):
        if uploaded_file.name.endswith(".pdf"):
            text = extract_text_from_pdf(uploaded_file)
        else:
            text = extract_text_from_txt(uploaded_file)

        chunks = chunk_text(text, max_words=500)
        simplified_chunks = []

        for i, chunk in enumerate(chunks, 1):
            st.info(f"✨ Simplifying chunk {i} of {len(chunks)}")
            simplified = simplify_chunk(chunk)
            simplified_chunks.append(simplified)

        simplified_text = "\n\n".join(simplified_chunks)

        st.markdown("### ✅ Simplified Text (OpenDyslexic Font)")
        st.markdown(f"<div class='dyslexic'>{simplified_text}</div>", unsafe_allow_html=True)

        pdf_buffer = generate_pdf_with_opendyslexic(simplified_text)
        st.download_button(
            label="📄 Download Simplified PDF",
            data=pdf_buffer,
            file_name="simplified_text.pdf",
            mime="application/pdf"
        )
else:
    st.info("Please upload a PDF or TXT file to simplify.")
