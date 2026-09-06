from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
import fitz
from docx import Document
import io
import re

app = FastAPI()

# Frontend ko backend se connect karne ki permission
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
        text += page.get_text() + "\n"

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
# RESUME ANALYSIS
# =========================

def analyze_resume_text(text):

    text_lower = text.lower()

    # -------------------------
    # SECTION DETECTION
    # -------------------------

    sections = {
        "contact": [
            "email",
            "phone",
            "mobile",
            "linkedin",
            "github"
        ],

        "summary": [
            "summary",
            "profile",
            "objective",
            "about me"
        ],

        "education": [
            "education",
            "academic",
            "b.tech",
            "btech",
            "bachelor",
            "degree",
            "university",
            "college"
        ],

        "skills": [
            "skills",
            "technical skills",
            "technologies",
            "programming",
            "tools"
        ],

        "experience": [
            "experience",
            "work experience",
            "employment",
            "professional experience"
        ],

        "internship": [
            "internship",
            "intern"
        ],

        "projects": [
            "projects",
            "project"
        ],

        "certifications": [
            "certification",
            "certifications",
            "certificate"
        ],

        "achievements": [
            "achievement",
            "achievements",
            "awards"
        ]
    }

    detected_sections = []

    for section, keywords in sections.items():

        if any(
            keyword in text_lower
            for keyword in keywords
        ):
            detected_sections.append(section)


    # =========================
    # CONTACT ANALYSIS
    # =========================

    email_found = bool(
        re.search(
            r"[\w\.-]+@[\w\.-]+\.\w+",
            text
        )
    )

    phone_found = bool(
        re.search(
            r"\b(?:\+91[\s-]?)?[6-9]\d{9}\b",
            text
        )
    )

    linkedin_found = "linkedin" in text_lower
    github_found = "github" in text_lower


    # =========================
    # ACHIEVEMENT / METRICS
    # =========================

    number_patterns = [
        r"\b\d+%",
        r"\b\d+\+",
        r"\b\d+\s*(users|projects|clients|students|customers)",
        r"\b\d+\s*(days|months|years)",
        r"\b\d+\s*(members|people)"
    ]

    quantified_results = 0

    for pattern in number_patterns:

        quantified_results += len(
            re.findall(
                pattern,
                text_lower
            )
        )


    # =========================
    # ACTION VERBS
    # =========================

    action_verbs = [
        "developed",
        "designed",
        "created",
        "built",
        "implemented",
        "improved",
        "optimized",
        "develop",
        "design",
        "create",
        "build",
        "implement",
        "manage",
        "managed",
        "analyzed",
        "led",
        "tested",
        "deployed",
        "automated"
    ]

    action_verb_count = 0

    for verb in action_verbs:

        action_verb_count += len(
            re.findall(
                r"\b" + re.escape(verb) + r"\b",
                text_lower
            )
        )


    # =========================
    # SKILL KEYWORDS
    # =========================

    common_skills = [
        "python",
        "java",
        "javascript",
        "typescript",
        "react",
        "node.js",
        "node",
        "html",
        "css",
        "sql",
        "mongodb",
        "mysql",
        "git",
        "github",
        "docker",
        "fastapi",
        "flask",
        "django",
        "machine learning",
        "artificial intelligence",
        "data analysis",
        "c++",
        "c",
        "aws",
        "azure"
    ]

    detected_skills = []

    for skill in common_skills:

        if skill in text_lower:
            detected_skills.append(skill)


    # =========================
    # SCORE
    # =========================

    score = 0

    breakdown = {}


    # CONTACT: 15
    contact_score = 0

    if email_found:
        contact_score += 5

    if phone_found:
        contact_score += 5

    if linkedin_found or github_found:
        contact_score += 5

    breakdown["contact"] = contact_score
    score += contact_score


    # EDUCATION: 15
    education_score = 15 if "education" in detected_sections else 0

    breakdown["education"] = education_score
    score += education_score


    # SKILLS: 15
    skills_score = 0

    if "skills" in detected_sections:
        skills_score += 5

    if len(detected_skills) >= 3:
        skills_score += 5

    if len(detected_skills) >= 7:
        skills_score += 5

    breakdown["skills"] = skills_score
    score += skills_score


    # EXPERIENCE: 15
    experience_score = 0

    if "experience" in detected_sections:
        experience_score += 8

    if "internship" in detected_sections:
        experience_score += 7

    breakdown["experience"] = experience_score
    score += experience_score


    # PROJECTS: 15
    project_score = 0

    if "projects" in detected_sections:
        project_score += 10

    if action_verb_count >= 3:
        project_score += 5

    breakdown["projects"] = project_score
    score += project_score


    # ACHIEVEMENTS: 10
    achievement_score = 0

    if quantified_results >= 1:
        achievement_score += 5

    if "achievements" in detected_sections:
        achievement_score += 5

    breakdown["achievements"] = achievement_score
    score += achievement_score


    # SUMMARY: 5
    summary_score = 5 if "summary" in detected_sections else 0

    breakdown["summary"] = summary_score
    score += summary_score


    # CERTIFICATIONS: 5
    certification_score = (
        5
        if "certifications" in detected_sections
        else 0
    )

    breakdown["certifications"] = certification_score
    score += certification_score


    # =========================
    # IMPROVEMENT SUGGESTIONS
    # =========================

    suggestions = []


    if not email_found:
        suggestions.append(
            "Add a professional email address."
        )


    if not phone_found:
        suggestions.append(
            "Add a valid phone number."
        )


    if not linkedin_found:
        suggestions.append(
            "Consider adding your LinkedIn profile."
        )


    if "summary" not in detected_sections:
        suggestions.append(
            "Add a short professional summary tailored to your target role."
        )


    if "skills" not in detected_sections:
        suggestions.append(
            "Add a clearly labelled Skills section."
        )
    elif len(detected_skills) < 3:
        suggestions.append(
            "Your resume contains very few recognizable technical skills. Add relevant skills you genuinely have."
        )


    if "projects" not in detected_sections:
        suggestions.append(
            "Add relevant projects and clearly explain your contribution."
        )


    if (
        "experience" not in detected_sections
        and "internship" not in detected_sections
    ):
        suggestions.append(
            "If you have genuine internship, work, or practical experience, add it."
        )


    if quantified_results == 0:
        suggestions.append(
            "Where truthful, add measurable results to your achievements or project bullets."
        )


    if action_verb_count < 3:
        suggestions.append(
            "Use stronger action verbs such as developed, designed, implemented, analyzed, or optimized where accurate."
        )


    if "achievements" not in detected_sections:
        suggestions.append(
            "Add relevant achievements, awards, or results if you have them."
        )


    # =========================
    # STRENGTHS
    # =========================

    strengths = []


    if "education" in detected_sections:
        strengths.append(
            "Education section detected."
        )


    if len(detected_skills) >= 3:
        strengths.append(
            f"{len(detected_skills)} relevant technical skills detected."
        )


    if "projects" in detected_sections:
        strengths.append(
            "Projects section detected."
        )


    if quantified_results > 0:
        strengths.append(
            "Measurable information detected in the resume."
        )


    if action_verb_count >= 3:
        strengths.append(
            "Good use of action-oriented language."
        )


    # =========================
    # FINAL RESULT
    # =========================

    return {
        "score": min(score, 100),

        "breakdown": breakdown,

        "detected_sections": detected_sections,

        "skills_detected": len(detected_skills),

        "skills": detected_skills,

        "strengths": strengths,

        "suggestions": suggestions,

        "metrics_found": quantified_results,

        "action_verbs_found": action_verb_count
    }


# =========================
# BASIC RESUME VALIDATION
# =========================

def looks_like_resume(text):

    text_lower = text.lower()

    resume_signals = [
        "education",
        "skills",
        "experience",
        "projects",
        "resume",
        "curriculum vitae",
        "objective",
        "summary",
        "internship",
        "certifications"
    ]

    found = sum(
        1
        for signal in resume_signals
        if signal in text_lower
    )

    return found >= 3


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

    filename = file.filename.lower()


    # File type check
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


    # Extract text
    try:

        if filename.endswith(".pdf"):

            text = extract_pdf_text(
                file_bytes
            )

        else:

            text = extract_docx_text(
                file_bytes
            )

    except Exception:

        return {
            "success": False,
            "message":
            "Could not read this document."
        }


    # Empty / unreadable document
    if len(text.strip()) < 50:

        return {
            "success": False,
            "message":
            "Could not read enough text from this document."
        }


    # Resume validation
    if not looks_like_resume(text):

        return {
            "success": False,
            "message":
            "This document does not appear to be a resume. Please upload a valid resume."
        }


    # Analyze
    analysis = analyze_resume_text(text)


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

        "text_preview":
        text[:500]
    }