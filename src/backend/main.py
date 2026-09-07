from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware

import fitz
from docx import Document

import io
import re
import os
import pytesseract
from PIL import Image
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
from dotenv import load_dotenv
from google import genai


# =========================
# APP + GEMINI
# =========================

load_dotenv()

app = FastAPI()

gemini_client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY")
)


# =========================
# CORS
# =========================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =========================
# TEXT EXTRACTION
# =========================
def extract_pdf_text(file_bytes):

    text = ""

    pdf = fitz.open(
        stream=file_bytes,
        filetype="pdf"
    )

    for page in pdf:
        text += page.get_text()

    # Agar normal PDF text nahi mila, OCR try karo
    if len(text.strip()) < 100:

        ocr_text = ""

        for page in pdf:
            pix = page.get_pixmap(dpi=200)

            image = Image.open(
                io.BytesIO(
                    pix.tobytes("png")
                )
            )

            ocr_text += pytesseract.image_to_string(image)

        text = ocr_text

    pdf.close()

    return text


def extract_docx_text(file_bytes):

    document = Document(
        io.BytesIO(file_bytes)
    )

    text = []

    for paragraph in document.paragraphs:
        text.append(paragraph.text)

    return "\n".join(text)


# =========================
# RESUME VALIDATION
# =========================

def looks_like_resume(text):

    text_lower = text.lower()

    resume_signals = [
        "education",
        "skills",
        "experience",
        "work experience",
        "projects",
        "project",
        "internship",
        "certifications",
        "achievements",
        "summary",
        "objective",
        "professional summary",
        "b.tech",
        "btech",
        "bachelor",
        "university",
        "college",
        "linkedin",
        "github",
        "curriculum vitae"
    ]

    found = sum(
        1
        for signal in resume_signals
        if signal in text_lower
    )

    return found >= 3


# =========================
# HELPERS
# =========================

def find_first(text, patterns):

    for pattern in patterns:

        match = re.search(
            pattern,
            text,
            re.IGNORECASE
        )

        if match:
            return match.group(0)

    return None


def detect_sections(text):

    text_lower = text.lower()

    section_keywords = {

        "Contact Information": [
            "email",
            "phone",
            "linkedin",
            "github"
        ],

        "Summary": [
            "summary",
            "profile",
            "objective"
        ],

        "Education": [
            "education",
            "academic",
            "b.tech",
            "btech",
            "bachelor",
            "degree",
            "university",
            "college"
        ],

        "Skills": [
            "skills",
            "technical skills",
            "technologies"
        ],

        "Experience": [
            "experience",
            "work experience",
            "employment"
        ],

        "Internship": [
            "internship",
            "intern"
        ],

        "Projects": [
            "projects",
            "project"
        ],

        "Certifications": [
            "certifications",
            "certificates",
            "certification"
        ],

        "Achievements": [
            "achievements",
            "awards",
            "honors"
        ]
    }

    detected = []

    for section, keywords in section_keywords.items():

        for keyword in keywords:

            if keyword in text_lower:

                detected.append(section)
                break

    return detected


def detect_skills(text):

    skills_list = [
        "python",
        "java",
        "javascript",
        "typescript",
        "react",
        "node.js",
        "nodejs",
        "html",
        "css",
        "sql",
        "mongodb",
        "mysql",
        "postgresql",
        "fastapi",
        "django",
        "flask",
        "c++",
        "c#",
        "git",
        "github",
        "docker",
        "aws",
        "azure",
        "machine learning",
        "deep learning",
        "artificial intelligence",
        "data analysis",
        "pandas",
        "numpy",
        "tensorflow",
        "pytorch",
        "excel",
        "power bi"
    ]

    text_lower = text.lower()

    found = []

    for skill in skills_list:

        if skill in text_lower:
            found.append(skill)

    return sorted(
        set(found)
    )


def detect_metrics(text):

    patterns = [
        r"\b\d+%",
        r"\b\d+\+",
        r"\b\d+\s*(?:users|customers|projects|clients|members)",
        r"\b\d+(?:,\d{3})\s(?:records|rows|items)",
        r"\b\d+(?:\.\d+)?\s*(?:seconds|ms|hours|days|months|years)"
    ]

    results = []

    for pattern in patterns:

        matches = re.findall(
            pattern,
            text,
            re.IGNORECASE
        )

        results.extend(matches)

    return list(
        dict.fromkeys(results)
    )


def detect_action_verbs(text):

    action_verbs = [
        "developed",
        "created",
        "built",
        "designed",
        "implemented",
        "developed",
        "managed",
        "led",
        "analyzed",
        "improved",
        "optimized",
        "automated",
        "tested",
        "deployed",
        "integrated",
        "configured",
        "maintained",
        "engineered",
        "delivered"
    ]

    text_lower = text.lower()

    found = []

    for verb in action_verbs:

        if re.search(
            r"\b" + re.escape(verb) + r"\b",
            text_lower
        ):

            found.append(verb)

    return sorted(
        set(found)
    )


# =========================
# RULE-BASED RESUME ANALYSIS
# =========================

def analyze_resume_text(text):

    sections = detect_sections(text)
    skills = detect_skills(text)
    metrics = detect_metrics(text)
    action_verbs = detect_action_verbs(text)

    score = 0

    breakdown = {}

    # -------------------------
    # Sections
    # -------------------------

    section_score = min(
        len(sections) * 5,
        30
    )

    score += section_score

    breakdown["Sections"] = section_score


    # -------------------------
    # Skills
    # -------------------------

    skill_score = min(
        len(skills) * 2,
        20
    )

    score += skill_score

    breakdown["Skills"] = skill_score


    # -------------------------
    # Action verbs
    # -------------------------

    verb_score = min(
        len(action_verbs) * 2,
        15
    )

    score += verb_score

    breakdown["Action Verbs"] = verb_score


    # -------------------------
    # Metrics
    # -------------------------

    metric_score = min(
        len(metrics) * 3,
        15
    )

    score += metric_score

    breakdown["Quantified Results"] = metric_score


    # -------------------------
    # Contact information
    # -------------------------

    email_found = bool(
        re.search(
            r"[\w\.-]+@[\w\.-]+\.\w+",
            text
        )
    )

    phone_found = bool(
        re.search(
            r"(?:\+91[\s-]?)?[6-9]\d{9}",
            text
        )
    )

    linkedin_found = "linkedin" in text.lower()
    github_found = "github" in text.lower()

    contact_score = 0

    if email_found:
        contact_score += 3

    if phone_found:
        contact_score += 3

    if linkedin_found:
        contact_score += 2

    if github_found:
        contact_score += 2

    score += contact_score

    breakdown["Contact Information"] = contact_score


    # -------------------------
    # Final score
    # -------------------------

    score = min(
        score,
        100
    )


    # -------------------------
    # Strengths
    # -------------------------

    strengths = []

    if "Education" in sections:
        strengths.append(
            "Education section is clearly present."
        )

    if len(skills) >= 3:
        strengths.append(
            "Good number of technical skills detected."
        )

    if "Projects" in sections:
        strengths.append(
            "Projects section is present."
        )

    if "Experience" in sections:
        strengths.append(
            "Work experience is included."
        )

    if "Internship" in sections:
        strengths.append(
            "Internship experience is included."
        )

    if len(metrics) > 0:
        strengths.append(
            "Resume contains measurable information."
        )

    if email_found:
        strengths.append(
            "Email address detected."
        )

    if linkedin_found:
        strengths.append(
            "LinkedIn profile detected."
        )

    if github_found:
        strengths.append(
            "GitHub profile detected."
        )

    if not strengths:
        strengths.append(
            "Resume contains identifiable resume content."
        )


    # -------------------------
    # Suggestions
    # -------------------------

    suggestions = []

    if "Summary" not in sections:
        suggestions.append(
            "Consider adding a concise professional summary tailored to your target role."
        )

    if "Projects" not in sections:
        suggestions.append(
            "Add relevant projects and clearly explain your contribution and technologies used."
        )

    if "Experience" not in sections and "Internship" not in sections:
        suggestions.append(
            "If you have relevant experience or internships, include them with specific responsibilities and results."
        )

    if len(metrics) == 0:
        suggestions.append(
            "Your bullets contain few measurable results. Add genuine numbers or outcomes where available."
        )

    if len(action_verbs) < 3:
        suggestions.append(
            "Use stronger action verbs such as developed, implemented, analyzed, or optimized where truthful."
        )

    if len(skills) < 3:
        suggestions.append(
            "Make relevant technical skills easier to identify for recruiters and ATS systems."
        )

    if not linkedin_found:
        suggestions.append(
            "Consider adding your LinkedIn profile if you have one."
        )

    if not github_found and len(skills) > 0:
        suggestions.append(
            "If you have relevant code projects, consider adding your GitHub profile."
        )


    return {

        "score": score,

        "breakdown": breakdown,

        "detected_sections": sections,

        "skills_detected": len(skills),

        "skills": skills,

        "strengths": strengths,

        "suggestions": suggestions,

        "metrics_found": metrics,

        "action_verbs_found": action_verbs
    }


# =========================
# GEMINI AI FEEDBACK
# =========================

def generate_ai_feedback(resume_text):

    prompt = f"""
You are an expert resume and career advisor.

Analyze the resume below.

IMPORTANT RULES:

- Give honest and specific feedback.
- Use ONLY information present in the resume.
- Never invent skills, achievements, experience, numbers, technologies, employers, or results.
- Do not recommend fake achievements.
- If metrics are missing, say the candidate should add genuine metrics if they have them.
- Identify actual weaknesses from the provided resume.
- Avoid generic advice when the resume gives enough information for specific advice.
- Keep the advice professional and useful for a student or job applicant.

Give your response in this structure:

OVERALL ASSESSMENT

HIGH PRIORITY IMPROVEMENTS

MEDIUM PRIORITY IMPROVEMENTS

STRENGTHS

SPECIFIC WRITING IMPROVEMENTS

FINAL CAREER ADVICE

RESUME:
{resume_text}
"""

    try:

        response = gemini_client.models.generate_content(
            model="gemini-3.5-flash-lite",
            contents=prompt
        )

        if response.text:
            return response.text

        return "AI feedback was not generated."

    except Exception as e:

        print(
            "Gemini error:",
            e
        )

        return (
            "AI feedback is temporarily unavailable. "
            "The rule-based resume analysis is still available."
        )


# =========================
# HOME
# =========================

@app.get("/")
def home():

    return {
        "message":
        "AI Resume Analyzer Backend is running!"
    }


# =========================
# ANALYZE RESUME
# =========================

@app.post("/analyze")
async def analyze_resume(
    file: UploadFile = File(...)
):

    filename = (
        file.filename or ""
    ).lower()


    # -------------------------
    # File type check
    # -------------------------

    if not (
        filename.endswith(".pdf")
        or filename.endswith(".docx")
    ):

        return {
            "success": False,
            "message":
            "Please upload a PDF or DOCX resume."
        }


    file_bytes = await file.read()


    # -------------------------
    # Extract text
    # -------------------------

    try:

        if filename.endswith(".pdf"):

            text = extract_pdf_text(
                file_bytes
            )

        else:

            text = extract_docx_text(
                file_bytes
            )

    except Exception as e:

        print(
            "Document reading error:",
            e
        )

        return {
            "success": False,
            "message":
            "Could not read this document."
        }


    # -------------------------
    # Empty document check
    # -------------------------

    if len(text.strip()) < 50:

        return {
            "success": False,
            "message":
            "Could not read enough text from this document."
        }


    # -------------------------
    # Resume validation
    # -------------------------

    if not looks_like_resume(text):

        return {
            "success": False,
            "message":
            "This document does not appear to be a resume. Please upload a valid resume."
        }


    # -------------------------
    # Rule-based analysis
    # -------------------------

    analysis = analyze_resume_text(
        text
    )


    # -------------------------
    # Gemini analysis
    # -------------------------

    ai_feedback = generate_ai_feedback(
        text
    )


    # -------------------------
    # Final response
    # -------------------------

    return {

        "success": True,

        "message":
        "Resume successfully analyzed.",

        "score":
        analysis["score"],

        "breakdown":
        analysis["breakdown"],

        "detected_sections":
        analysis["detected_sections"],

        "skills_detected":
        analysis["skills_detected"],

        "skills":
        analysis["skills"],

        "strengths":
        analysis["strengths"],

        "suggestions":
        analysis["suggestions"],

        "metrics_found":
        analysis["metrics_found"],

        "action_verbs_found":
        analysis["action_verbs_found"],

        "ai_feedback":
        ai_feedback,

         "text_preview":
        text[:500]
    }