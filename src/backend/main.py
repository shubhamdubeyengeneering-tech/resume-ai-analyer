from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware

import fitz
from docx import Document

import io
import re
import os
import pytesseract
from PIL import Image, ImageOps

from dotenv import load_dotenv
from google import genai


# =========================
# APP + GEMINI
# =========================

load_dotenv()

app = FastAPI()

gemini_api_key = os.getenv("GEMINI_API_KEY")

gemini_client = None

if gemini_api_key:
    gemini_client = genai.Client(
        api_key=gemini_api_key
    )


# =========================
# TESSERACT OCR
# =========================

# Windows
windows_tesseract = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

if os.path.exists(windows_tesseract):
    pytesseract.pytesseract.tesseract_cmd = windows_tesseract

# On Render/Linux, Tesseract should be available in PATH
# through the Docker environment.


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
# IMAGE OCR
# =========================

def extract_image_text(file_bytes):

    image = Image.open(
        io.BytesIO(file_bytes)
    )

    image = ImageOps.exif_transpose(image)

    if image.mode != "RGB":
        image = image.convert("RGB")

    # Keep OCR reasonably fast
    max_dimension = 2200

    if max(image.size) > max_dimension:
        image.thumbnail(
            (max_dimension, max_dimension),
            Image.Resampling.LANCZOS
        )

    text = pytesseract.image_to_string(
        image,
        config="--psm 6"
    )

    return text


# =========================
# PDF TEXT + OCR
# =========================

def extract_pdf_text(file_bytes):

    pdf = fitz.open(
        stream=file_bytes,
        filetype="pdf"
    )

    text_parts = []

    # First try normal PDF text extraction.
    # This is much faster than OCR.
    for page in pdf:
        page_text = page.get_text()

        if page_text:
            text_parts.append(page_text)

    normal_text = "\n".join(
        text_parts
    ).strip()

    # Normal text PDF -> return immediately.
    if len(normal_text) >= 100:
        pdf.close()
        return normal_text

    # Scanned/image PDF -> OCR
    ocr_text = []

    for page in pdf:

        # 150 DPI keeps OCR reasonably fast.
        pix = page.get_pixmap(
            dpi=150,
            alpha=False
        )

        image = Image.open(
            io.BytesIO(
                pix.tobytes("png")
            )
        )

        if image.mode != "RGB":
            image = image.convert("RGB")

        page_text = pytesseract.image_to_string(
            image,
            config="--psm 6"
        )

        if page_text:
            ocr_text.append(page_text)

    pdf.close()

    return "\n".join(
        ocr_text
    )


# =========================
# DOCX TEXT
# =========================

def extract_docx_text(file_bytes):

    document = Document(
        io.BytesIO(file_bytes)
    )

    text = []

    # Normal paragraphs
    for paragraph in document.paragraphs:

        paragraph_text = paragraph.text.strip()

        if paragraph_text:
            text.append(
                paragraph_text
            )

    # Resume tables
    for table in document.tables:

        for row in table.rows:

            for cell in row.cells:

                cell_text = cell.text.strip()

                if cell_text:
                    text.append(
                        cell_text
                    )

    return "\n".join(text)


# =========================
# TEXT QUALITY CHECK
# =========================

def text_quality_is_reasonable(text):

    cleaned = re.sub(
        r"\s+",
        " ",
        text
    ).strip()

    if len(cleaned) < 50:
        return False

    # Count alphabetic characters.
    letters = len(
        re.findall(
            r"[A-Za-z]",
            cleaned
        )
    )

    # A resume should contain a reasonable amount
    # of readable alphabetic text.
    if letters < 30:
        return False

    # OCR corruption indicator.
    # If too many strange symbols appear, reject it.
    strange_chars = len(
        re.findall(
            r"[^A-Za-z0-9\s@.,:;()/&+#%\-_'|]",
            cleaned
        )
    )

    if len(cleaned) > 100:
        strange_ratio = (
            strange_chars / len(cleaned)
        )

        if strange_ratio > 0.20:
            return False

    return True


# =========================
# RESUME VALIDATION
# =========================

def looks_like_resume(text):

    text_lower = re.sub(
        r"\s+",
        " ",
        text.lower()
    ).strip()

    if len(text_lower) < 80:
        return False

    if not text_quality_is_reasonable(text):
        return False

    # -------------------------
    # Clearly non-resume documents
    # -------------------------

    non_resume_signals = [
        "marksheet",
        "mark sheet",
        "statement of marks",
        "grade sheet",
        "marks obtained",
        "total marks",
        "subject code",
        "semester result",
        "examination result",
        "academic transcript",
        "transcript of records",
        "fee receipt",
        "payment receipt",
        "invoice",
        "purchase order",
        "bank statement",
        "admit card",
        "question paper",
        "hall ticket",
        "fee challan",
        "medical report",
        "prescription",
        "laboratory report",
        "test report"
    ]

    negative_score = sum(
        1
        for signal in non_resume_signals
        if signal in text_lower
    )

    # One very strong document-type signal can be enough
    # when combined with other obvious result-document terms.
    strong_non_resume = [
        "statement of marks",
        "marks obtained",
        "total marks",
        "semester result",
        "examination result",
        "academic transcript",
        "transcript of records",
        "fee receipt",
        "payment receipt",
        "bank statement",
        "admit card",
        "question paper"
    ]

    if any(
        signal in text_lower
        for signal in strong_non_resume
    ):
        return False

    if negative_score >= 2:
        return False

    # -------------------------
    # Resume section categories
    # -------------------------

    resume_signals = {

        "education": [
            "education",
            "academic background",
            "b.tech",
            "btech",
            "bachelor",
            "bachelors",
            "degree",
            "university",
            "college",
            "school"
        ],

        "skills": [
            "skills",
            "technical skills",
            "technologies",
            "technical expertise",
            "programming skills"
        ],

        "experience": [
            "experience",
            "work experience",
            "employment",
            "professional experience",
            "work history"
        ],

        "projects": [
            "projects",
            "project experience",
            "academic projects"
        ],

        "internship": [
            "internship",
            "intern",
            "industrial training"
        ],

        "profile": [
            "summary",
            "professional summary",
            "profile",
            "objective",
            "career objective",
            "about me"
        ],

        "certifications": [
            "certifications",
            "certificates",
            "certification"
        ],

        "achievements": [
            "achievements",
            "awards",
            "honors",
            "accomplishments"
        ],

        "professional_links": [
            "linkedin",
            "github",
            "portfolio"
        ]
    }

    categories_found = 0

    for keywords in resume_signals.values():

        if any(
            keyword in text_lower
            for keyword in keywords
        ):
            categories_found += 1

    # -------------------------
    # Contact evidence
    # -------------------------

    email_found = bool(
        re.search(
            r"[\w\.-]+@[\w\.-]+\.\w+",
            text_lower
        )
    )

    phone_found = bool(
        re.search(
            r"(?:\+91[\s-]?)?[6-9]\d{9}",
            text_lower
        )
    )

    linkedin_found = bool(
        re.search(
            r"linkedin(?:\.com)?",
            text_lower
        )
    )

    github_found = bool(
        re.search(
            r"github(?:\.com)?",
            text_lower
        )
    )

    contact_found = (
        email_found
        or phone_found
        or linkedin_found
        or github_found
    )

    # -------------------------
    # Technical skill evidence
    # -------------------------

    technical_terms = [
        "python",
        "java",
        "javascript",
        "typescript",
        "c++",
        "c#",
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
        "power bi",
        "excel"
    ]

    skill_count = sum(
        1
        for skill in technical_terms
        if skill in text_lower
    )

    # -------------------------
    # Professional activity evidence
    # -------------------------

    activity_terms = [
        "developed",
        "created",
        "built",
        "designed",
        "implemented",
        "deployed",
        "integrated",
        "programmed",
        "engineered",
        "analyzed",
        "tested",
        "optimized",
        "managed",
        "worked on",
        "responsible for"
    ]

    activity_count = sum(
        1
        for activity in activity_terms
        if activity in text_lower
    )

    # -------------------------
    # Strong resume identity
    # -------------------------

    explicit_resume_identity = any(
        phrase in text_lower
        for phrase in [
            "resume",
            "curriculum vitae",
            "cv"
        ]
    )

    # -------------------------
    # Final validation rules
    # -------------------------

    # Very strong case:
    # several resume categories + contact.
    if categories_found >= 4 and contact_found:
        return True

    # Strong case:
    # categories + technical skills + contact.
    if (
        categories_found >= 3
        and skill_count >= 2
        and contact_found
    ):
        return True

    # Technical/student resume without contact:
    # several categories + multiple skills + activity.
    if (
        categories_found >= 4
        and skill_count >= 2
        and activity_count >= 1
    ):
        return True

    # Explicit resume/CV with supporting structure.
    if (
        explicit_resume_identity
        and categories_found >= 3
        and (
            contact_found
            or skill_count >= 2
        )
    ):
        return True

    # Non-technical resumes can still be valid.
    # Require stronger structure for them.
    if (
        categories_found >= 5
        and contact_found
        and activity_count >= 1
    ):
        return True

    return False


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


# =========================
# SECTION DETECTION
# =========================

def detect_sections(text):

    text_lower = text.lower()

    section_keywords = {

        "Contact Information": [
            "email",
            "phone",
            "linkedin",
            "github",
            "portfolio"
        ],

        "Summary": [
            "summary",
            "profile",
            "objective",
            "professional summary"
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
            "technologies",
            "programming skills"
        ],

        "Experience": [
            "experience",
            "work experience",
            "employment",
            "professional experience"
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


# =========================
# SKILL DETECTION
# =========================

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


# =========================
# METRICS
# =========================

def detect_metrics(text):

    patterns = [
        r"\b\d+%",
        r"\b\d+\+",
        r"\b\d+\s*(?:users|customers|projects|clients|members)",
        r"\b\d+(?:,\d{3})\s*(?:records|rows|items)",
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


# =========================
# ACTION VERBS
# =========================

def detect_action_verbs(text):

    action_verbs = [
        "developed",
        "created",
        "built",
        "designed",
        "implemented",
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
# RULE-BASED ANALYSIS
# =========================

def analyze_resume_text(text):

    sections = detect_sections(text)
    skills = detect_skills(text)
    metrics = detect_metrics(text)
    action_verbs = detect_action_verbs(text)

    score = 0

    breakdown = {}

    # Sections
    section_score = min(
        len(sections) * 5,
        30
    )

    score += section_score

    breakdown["Sections"] = section_score

    # Skills
    skill_score = min(
        len(skills) * 2,
        20
    )

    score += skill_score

    breakdown["Skills"] = skill_score

    # Action verbs
    verb_score = min(
        len(action_verbs) * 2,
        15
    )

    score += verb_score

    breakdown["Action Verbs"] = verb_score

    # Metrics
    metric_score = min(
        len(metrics) * 3,
        15
    )

    score += metric_score

    breakdown["Quantified Results"] = metric_score

    # Contact
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

    linkedin_found = (
        "linkedin" in text.lower()
    )

    github_found = (
        "github" in text.lower()
    )

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

    score = min(
        score,
        100
    )

    # =========================
    # STRENGTHS
    # =========================

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

    # =========================
    # SUGGESTIONS
    # =========================

    suggestions = []

    if "Summary" not in sections:

        suggestions.append(
            "Consider adding a concise professional summary tailored to your target role."
        )

    if "Projects" not in sections:

        suggestions.append(
            "Add relevant projects and clearly explain your contribution and technologies used."
        )

    if (
        "Experience" not in sections
        and "Internship" not in sections
    ):

        suggestions.append(
            "If you have relevant experience or internships, include them with specific responsibilities and genuine results."
        )

    if "Certifications" not in sections:

        suggestions.append(
            "If you have relevant certifications, consider adding a Certifications section. Choose certifications related to your target role."
        )

    if len(metrics) == 0:

        suggestions.append(
            "Add genuine numbers or measurable outcomes to project or experience bullets where available."
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

    if (
        not github_found
        and len(skills) > 0
    ):

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

    if gemini_client is None:

        return (
            "AI feedback is unavailable because the Gemini API key "
            "is not configured."
        )

    # Keep AI prompt reasonably small for faster response.
    # Rule-based analysis still uses the complete text.
    resume_for_ai = resume_text[:12000]

    prompt = f"""
You are an expert resume and career advisor.

Analyze the resume below.

IMPORTANT RULES:

- Give honest and specific feedback.
- Use ONLY information present in the resume.
- Never invent skills, achievements, experience, numbers, technologies, employers, or results.
- Never recommend fake achievements.
- If a certification, skill, project, or extra section could help, explain that it should be added ONLY if it is genuinely relevant and the candidate actually has it or can legitimately earn it.
- Do not claim that a candidate has a certification or skill unless it appears in the resume.
- Identify actual weaknesses from the provided resume.
- Keep the advice useful for a student or job applicant.

Give your response in this structure:

OVERALL ASSESSMENT

HIGH PRIORITY IMPROVEMENTS

MEDIUM PRIORITY IMPROVEMENTS

STRENGTHS

SPECIFIC WRITING IMPROVEMENTS

CERTIFICATION / EXTRA SKILL SUGGESTIONS

FINAL CAREER ADVICE

RESUME:
{resume_for_ai}
"""

    try:

        response = gemini_client.models.generate_content(
            model="gemini-3.5-flash-lite",
            contents=prompt
        )

        if response.text:
            return response.text

        return (
            "AI feedback was not generated."
        )

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
    # Supported file types
    # -------------------------

    supported_extensions = (
        ".pdf",
        ".docx",
        ".jpg",
        ".jpeg",
        ".png"
    )

    if not filename.endswith(
        supported_extensions
    ):

        return {
            "success": False,
            "message":
            "Please upload a PDF, DOCX, JPG, JPEG, or PNG resume."
        }

    file_bytes = await file.read()

    if not file_bytes:

        return {
            "success": False,
            "message":
            "The uploaded file is empty."
        }

    # -------------------------
    # Extract text
    # -------------------------

    try:

        if filename.endswith(".pdf"):

            text = extract_pdf_text(
                file_bytes
            )

        elif filename.endswith(".docx"):

            text = extract_docx_text(
                file_bytes
            )

        else:

            text = extract_image_text(
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
            "Could not read this document. Please upload a clear, readable resume."
        }

    text = text.strip()

    # -------------------------
    # Empty / unreadable check
    # -------------------------

    if len(text) < 50:

        return {
            "success": False,
            "message":
            "Could not read enough text from this document. Please upload a clearer resume."
        }

    if not text_quality_is_reasonable(text):

        return {
            "success": False,
            "message":
            "The document text could not be read clearly enough. Please upload a clearer resume."
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
    # Gemini AI Advisor
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