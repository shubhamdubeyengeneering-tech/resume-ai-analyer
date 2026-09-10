import { useState } from "react";
import "./App.css";

const API_URL =
  window.location.hostname === "localhost"
    ? "http://127.0.0.1:8000"
    : "https://resume-ai-analyer.onrender.com";

const SECTION_LIST = [
  ["contact", "Contact"],
  ["summary", "Summary"],
  ["education", "Education"],
  ["skills", "Skills"],
  ["experience", "Experience"],
  ["internship", "Internship"],
  ["projects", "Projects"],
  ["certifications", "Certifications"],
  ["achievements", "Achievements"],
];

function getScoreInfo(score) {
  if (score >= 90) {
    return {
      className: "good",
      label: "Excellent Resume",
    };
  }

  if (score >= 80) {
    return {
      className: "good",
      label: "Strong Resume",
    };
  }

  if (score >= 70) {
    return {
      className: "average",
      label: "Good Resume",
    };
  }

  if (score >= 60) {
    return {
      className: "average",
      label: "Needs Improvement",
    };
  }

  return {
    className: "poor",
    label: "Weak Resume",
  };
}

function canonicalSections(sections) {
  if (!Array.isArray(sections)) return [];

  return sections.map((item) =>
    String(item).toLowerCase()
  );
}

function isSectionHeading(line) {
  const value = line
    .replace(/[^a-zA-Z ]/g, "")
    .trim()
    .toLowerCase();

  const headings = [
    "professional summary",
    "summary",
    "profile",
    "objective",
    "skills",
    "technical skills",
    "experience",
    "work experience",
    "professional experience",
    "internship",
    "internships",
    "projects",
    "education",
    "certifications",
    "certification",
    "achievements",
    "awards",
    "honors",
  ];

  return headings.includes(value);
}

function isBullet(line) {
  return /^(?:[•●▪◦‣*-]|\d+[.)])\s+/.test(
    line.trim()
  );
}

function renderEnhancedPreview(text) {
  if (!text) return null;

  const lines = text.split(/\r?\n/);
  let meaningfulIndex = 0;

  return lines.map((rawLine, index) => {
    const line = rawLine.trim();

    if (!line) {
      return (
        <div
          className="resume-preview-space"
          key={index}
        />
      );
    }

    const currentMeaningfulIndex =
      meaningfulIndex;

    meaningfulIndex += 1;

    if (currentMeaningfulIndex === 0) {
      return (
        <div
          className="resume-preview-name"
          key={index}
        >
          {line}
        </div>
      );
    }

    if (
      currentMeaningfulIndex === 1 &&
      (line.includes("@") ||
        line.includes("linkedin") ||
        line.includes("github") ||
        /\d{7,}/.test(line))
    ) {
      return (
        <div
          className="resume-preview-contact"
          key={index}
        >
          {line}
        </div>
      );
    }

    if (isSectionHeading(line)) {
      return (
        <div
          className="resume-preview-section"
          key={index}
        >
          {line.toUpperCase()}
        </div>
      );
    }

    if (isBullet(line)) {
      return (
        <div
          className="resume-preview-bullet"
          key={index}
        >
          <span>•</span>

          <span>
            {line.replace(
              /^(?:[•●▪◦‣*-]|\d+[.)])\s+/,
              ""
            )}
          </span>
        </div>
      );
    }

    return (
      <div
        className="resume-preview-line"
        key={index}
      >
        {line}
      </div>
    );
  });
}

function App() {
  const [file, setFile] = useState(null);

  const [photo, setPhoto] = useState(null);
  const [photoPreview, setPhotoPreview] =
    useState("");

  const [result, setResult] = useState(null);

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const [aiAdvice, setAiAdvice] = useState(null);
  const [aiStatus, setAiStatus] = useState("");

  const [chatMessages, setChatMessages] =
    useState([]);
  const [chatInput, setChatInput] =
    useState("");
  const [chatLoading, setChatLoading] =
    useState(false);

  const [enhancing, setEnhancing] =
    useState(false);

  const [checkingPhoto, setCheckingPhoto] =
    useState(false);

  const [
    showEnhancePhotoOptions,
    setShowEnhancePhotoOptions,
  ] = useState(false);

  const [
    originalPhotoDetected,
    setOriginalPhotoDetected,
  ] = useState(null);

  const [enhancedResume, setEnhancedResume] =
    useState("");

  const [enhancedPdf, setEnhancedPdf] =
    useState("");

  const [
    enhancedFilename,
    setEnhancedFilename,
  ] = useState("");

  const [enhanceError, setEnhanceError] =
    useState("");

  const [showDetails, setShowDetails] =
    useState(false);

  const resumeJobId =
    result?.resume_job_id ||
    result?.job_id;

  const score = Number(
    result?.score || 0
  );

  const scoreInfo =
    getScoreInfo(score);

  const detectedSections =
    canonicalSections(
      result?.detected_sections ||
        result?.sections ||
        []
    );

  const skills = Array.isArray(
    result?.skills
  )
    ? result.skills
    : Array.isArray(
        result?.skills_detected
      )
      ? result.skills_detected
      : [];

  const strengths = Array.isArray(
    result?.strengths
  )
    ? result.strengths
    : [];

  const suggestions = Array.isArray(
    result?.suggestions
  )
    ? result.suggestions
    : [];

  const actionPlan =
    Array.isArray(
      result?.action_plan
    ) &&
    result.action_plan.length > 0
      ? result.action_plan
      : suggestions;

  const breakdown =
    result?.breakdown || {};

  function handleFileChange(event) {
    const selectedFile =
      event.target.files?.[0];

    if (!selectedFile) return;

    setFile(selectedFile);

    setPhoto(null);
    setPhotoPreview("");

    setResult(null);
    setError("");

    setAiAdvice(null);
    setAiStatus("");

    setEnhancedResume("");
    setEnhancedPdf("");
    setEnhancedFilename("");
    setEnhanceError("");

    setShowEnhancePhotoOptions(false);
    setCheckingPhoto(false);
    setOriginalPhotoDetected(null);

    setChatMessages([]);
    setChatInput("");
  }

  function handlePhotoChange(event) {
    const selectedPhoto =
      event.target.files?.[0];

    if (!selectedPhoto) return;

    if (
      ![
        "image/jpeg",
        "image/png",
      ].includes(selectedPhoto.type)
    ) {
      setEnhanceError(
        "Please select a JPG or PNG photo."
      );
      return;
    }

    setPhoto(selectedPhoto);
    setEnhanceError("");

    const url =
      URL.createObjectURL(
        selectedPhoto
      );

    setPhotoPreview(url);
  }

  async function fetchAIAdvice(jobId) {
    setAiStatus("processing");

    for (let i = 0; i < 80; i += 1) {
      try {
        const response =
          await fetch(
            `${API_URL}/ai-feedback/${jobId}`
          );

        const data =
          await response.json();

        if (
          data.status ===
          "completed"
        ) {
          setAiAdvice(
            data.ai_feedback
          );

          setAiStatus(
            "completed"
          );

          return;
        }

        if (
          data.status === "failed"
        ) {
          setAiStatus("failed");
          return;
        }
      } catch {
        // Continue polling.
      }

      await new Promise(
        (resolve) =>
          setTimeout(
            resolve,
            1500
          )
      );
    }

    setAiStatus("failed");
  }

  async function analyzeResume() {
    if (!file) {
      setError(
        "Please select a resume first."
      );
      return;
    }

    setLoading(true);
    setError("");

    setResult(null);
    setAiAdvice(null);
    setAiStatus("");

    setEnhancedResume("");
    setEnhancedPdf("");
    setEnhancedFilename("");
    setEnhanceError("");

    setShowEnhancePhotoOptions(
      false
    );

    setCheckingPhoto(false);
    setOriginalPhotoDetected(null);

    setPhoto(null);
    setPhotoPreview("");

    setChatMessages([]);
    setChatInput("");

    try {
      const formData =
        new FormData();

      formData.append(
        "file",
        file
      );

      const response =
        await fetch(
          `${API_URL}/analyze`,
          {
            method: "POST",
            body: formData,
          }
        );

      const data =
        await response.json();

      if (
        !response.ok ||
        !data.success
      ) {
        throw new Error(
          data.message ||
            "Resume analysis failed."
        );
      }

      setResult(data);

      const jobId =
        data.resume_job_id ||
        data.ai_feedback_job_id ||
        data.job_id;

      if (jobId) {
        fetchAIAdvice(jobId);
      }
    } catch (err) {
      setError(
        err.message ||
          "Could not analyze the resume."
      );
    } finally {
      setLoading(false);
    }
  }

  /*
   * This function checks whether the ORIGINAL
   * uploaded PDF/DOCX contains a profile photo.
   *
   * If the backend says a photo exists:
   * - Do not ask user for another photo.
   * - Directly create the enhanced resume.
   *
   * If no photo exists:
   * - Show Add Photo / Skip options.
   */
  async function handleEnhanceClick() {
    if (!resumeJobId) {
      setEnhanceError(
        "Please analyze a resume first."
      );
      return;
    }

    if (!file) {
      setEnhanceError(
        "Original resume file is not available."
      );
      return;
    }

    setCheckingPhoto(true);
    setEnhanceError("");

    setShowEnhancePhotoOptions(
      false
    );

    try {
      const formData =
        new FormData();

      formData.append(
        "job_id",
        resumeJobId
      );

      formData.append(
        "resume_file",
        file
      );

      const response =
        await fetch(
          `${API_URL}/enhance-photo-status`,
          {
            method: "POST",
            body: formData,
          }
        );

      const data =
        await response.json();

      if (
        !response.ok ||
        data.success === false
      ) {
        throw new Error(
          data.message ||
            "Could not check the original resume photo."
        );
      }

      const detected =
        Boolean(
          data.photo_detected
        );

      setOriginalPhotoDetected(
        detected
      );

      if (detected) {
        /*
         * Original photo exists.
         * Backend will preserve it.
         */
        await createEnhancedResume(
          null
        );
      } else {
        /*
         * No original photo.
         * Now ask user whether they want
         * to add one.
         */
        setShowEnhancePhotoOptions(
          true
        );
      }
    } catch (err) {
      setEnhanceError(
        err.message ||
          "Could not check the resume photo."
      );
    } finally {
      setCheckingPhoto(false);
    }
  }

  /*
   * Actually creates the enhanced resume.
   *
   * photoToSend can be:
   * - null = no user photo
   * - File = user-selected photo
   */
  async function createEnhancedResume(
    photoToSend = null
  ) {
    if (!resumeJobId) {
      setEnhanceError(
        "Please analyze a resume first."
      );
      return;
    }

    if (!file) {
      setEnhanceError(
        "Original resume file is not available."
      );
      return;
    }

    setEnhancing(true);
    setEnhanceError("");

    setEnhancedResume("");
    setEnhancedPdf("");
    setEnhancedFilename("");

    try {
      const formData =
        new FormData();

      formData.append(
        "job_id",
        resumeJobId
      );

      /*
       * Important:
       * Send the ORIGINAL resume file.
       * Backend can extract the original
       * embedded profile photo from it.
       */
      formData.append(
        "resume_file",
        file
      );

      /*
       * Only send a user photo when
       * user explicitly selected one.
       */
      if (photoToSend) {
        formData.append(
          "photo",
          photoToSend
        );
      }

      const response =
        await fetch(
          `${API_URL}/enhance`,
          {
            method: "POST",
            body: formData,
          }
        );

      const data =
        await response.json();

      if (
        !response.ok ||
        !data.success
      ) {
        throw new Error(
          data.message ||
            "Resume enhancement failed."
        );
      }

      setEnhancedResume(
        data.enhanced_resume || ""
      );

      setEnhancedPdf(
        data.pdf_base64 || ""
      );

      setEnhancedFilename(
        data.filename ||
          "ResumeAI-Professional-Resume.pdf"
      );

      /*
       * Enhancement is complete,
       * so hide photo-selection UI.
       */
      setShowEnhancePhotoOptions(
        false
      );
    } catch (err) {
      setEnhanceError(
        err.message ||
          "Could not create the professional resume."
      );
    } finally {
      setEnhancing(false);
    }
  }

  async function skipPhotoAndEnhance() {
    setPhoto(null);
    setPhotoPreview("");
    setEnhanceError("");

    await createEnhancedResume(
      null
    );
  }

  async function addPhotoAndEnhance() {
    if (!photo) {
      setEnhanceError(
        "Please choose a JPG or PNG photo first."
      );
      return;
    }

    await createEnhancedResume(
      photo
    );
  }

  function downloadEnhancedPDF() {
    if (!enhancedPdf) {
      setEnhanceError(
        "The PDF is not ready yet."
      );
      return;
    }

    try {
      const binary =
        atob(enhancedPdf);

      const bytes =
        new Uint8Array(
          binary.length
        );

      for (
        let i = 0;
        i < binary.length;
        i += 1
      ) {
        bytes[i] =
          binary.charCodeAt(i);
      }

      const blob =
        new Blob(
          [bytes],
          {
            type: "application/pdf",
          }
        );

      const url =
        URL.createObjectURL(
          blob
        );

      const link =
        document.createElement(
          "a"
        );

      link.href = url;

      link.download =
        enhancedFilename ||
        "ResumeAI-Professional-Resume.pdf";

      document.body.appendChild(
        link
      );

      link.click();

      link.remove();

      URL.revokeObjectURL(url);
    } catch {
      setEnhanceError(
        "Could not download the PDF."
      );
    }
  }

  async function sendChatMessage() {
    const message =
      chatInput.trim();

    if (
      !message ||
      !resumeJobId
    ) {
      return;
    }

    setChatInput("");

    setChatMessages(
      (previous) => [
        ...previous,
        {
          role: "user",
          text: message,
        },
      ]
    );

    setChatLoading(true);

    try {
      const response =
        await fetch(
          `${API_URL}/chat`,
          {
            method: "POST",
            headers: {
              "Content-Type":
                "application/json",
            },
            body: JSON.stringify({
              job_id:
                resumeJobId,
              message,
            }),
          }
        );

      const data =
        await response.json();

      if (!data.success) {
        throw new Error(
          data.message ||
            "Chat request failed."
        );
      }

      const chatJobId =
        data.chat_job_id;

      if (!chatJobId) {
        throw new Error(
          "AI chat job was not created."
        );
      }

      for (
        let i = 0;
        i < 80;
        i += 1
      ) {
        const pollResponse =
          await fetch(
            `${API_URL}/chat/${chatJobId}`
          );

        const pollData =
          await pollResponse.json();

        if (
          pollData.status ===
          "completed"
        ) {
          setChatMessages(
            (previous) => [
              ...previous,
              {
                role: "assistant",
                text:
                  pollData.chat_answer ||
                  pollData.answer ||
                  "",
              },
            ]
          );

          break;
        }

        if (
          pollData.status ===
          "failed"
        ) {
          throw new Error(
            pollData.message ||
              "AI chat failed."
          );
        }

        await new Promise(
          (resolve) =>
            setTimeout(
              resolve,
              1200
            )
        );
      }
    } catch (err) {
      setChatMessages(
        (previous) => [
          ...previous,
          {
            role: "assistant",
            text:
              err.message ||
              "Sorry, AI chat failed.",
          },
        ]
      );
    } finally {
      setChatLoading(false);
    }
  }

  function handleChatKeyDown(
    event
  ) {
    if (
      event.key === "Enter" &&
      !event.shiftKey
    ) {
      event.preventDefault();
      sendChatMessage();
    }
  }

  function resetApp() {
    setFile(null);

    setPhoto(null);
    setPhotoPreview("");

    setResult(null);
    setError("");

    setAiAdvice(null);
    setAiStatus("");

    setChatMessages([]);
    setChatInput("");

    setEnhancedResume("");
    setEnhancedPdf("");
    setEnhancedFilename("");
    setEnhanceError("");

    setShowEnhancePhotoOptions(
      false
    );

    setCheckingPhoto(false);
    setOriginalPhotoDetected(null);

    setShowDetails(false);
  }

  return (
    <div className="app-shell">
      <header className="topbar">
        <div className="brand">
          <div className="brand-logo">
            R
          </div>

          <div>
            <div className="brand-name">
              ResumeAI
            </div>

            <div className="brand-subtitle">
              AI Resume Analyzer
            </div>
          </div>
        </div>

        {result && (
          <button
            className="reset-button"
            onClick={resetApp}
          >
            New Resume
          </button>
        )}
      </header>

      {!result && (
        <main className="hero-section">
          <div className="hero-content">
            <div className="hero-badge">
              AI-POWERED RESUME ANALYZER
            </div>

            <h1>
              Make Your Resume
              <br />
              <span>Job Ready.</span>
            </h1>

            <p>
              Upload your resume and get an
              honest AI-powered analysis,
              actionable improvements and
              career guidance.
            </p>
          </div>

          <div className="upload-card">
            <div className="upload-icon">
              ↑
            </div>

            <h2>
              Upload Your Resume
            </h2>

            <p>
              PDF, DOCX, JPG or PNG
            </p>

            <label className="upload-button">
              Choose Resume

              <input
                type="file"
                accept=".pdf,.docx,.jpg,.jpeg,.png"
                onChange={
                  handleFileChange
                }
                hidden
              />
            </label>

            {file && (
              <div className="selected-file">
                <strong>
                  Selected:
                </strong>{" "}
                {file.name}
              </div>
            )}

            {/*
             * IMPORTANT:
             * No profile photo upload here.
             *
             * Photo selection appears only AFTER
             * the user clicks Enhance Resume.
             */}

            <button
              className="analyze-button"
              onClick={
                analyzeResume
              }
              disabled={
                loading || !file
              }
            >
              {loading
                ? "Analyzing..."
                : "Analyze Resume →"}
            </button>

            {error && (
              <div className="error-message">
                {error}
              </div>
            )}
          </div>
        </main>
      )}

      {result && (
        <main className="dashboard">
          <div className="dashboard-header">
            <div>
              <div className="hero-badge">
                ANALYSIS COMPLETE
              </div>

              <h1>
                Your Resume Report
              </h1>

              <p>
                Honest analysis based on the
                content detected in your resume.
              </p>
            </div>
          </div>

          <div className="dashboard-grid">
            <section className="score-card">
              <div className="card-heading">
                <span>📊</span>
                Resume Score
              </div>

              <div
                className={`score-circle ${scoreInfo.className}`}
              >
                <strong>
                  {score}
                </strong>

                <span>
                  / 100
                </span>
              </div>

              <h2>
                {scoreInfo.label}
              </h2>

              <p>
                {result.verdict_message ||
                  "Your score is based on resume content quality, evidence and ATS factors."}
              </p>

              {result.why_score?.length >
                0 && (
                <div className="why-score">
                  <h3>
                    Why this score?
                  </h3>

                  <ul>
                    {result.why_score.map(
                      (
                        item,
                        index
                      ) => (
                        <li
                          key={index}
                        >
                          {item}
                        </li>
                      )
                    )}
                  </ul>
                </div>
              )}
            </section>

            <section className="overview-card">
              <div className="card-heading">
                <span>📋</span>
                Resume Overview
              </div>

              <div className="section-status-list">
                {SECTION_LIST.map(
                  ([key, label]) => {
                    const present =
                      detectedSections.includes(
                        key
                      );

                    return (
                      <div
                        className="section-status"
                        key={key}
                      >
                        <span>
                          {label}
                        </span>

                        <span
                          className={
                            present
                              ? "status-present"
                              : "status-missing"
                          }
                        >
                          {present
                            ? "✓ Present"
                            : "✕ Missing"}
                        </span>
                      </div>
                    );
                  }
                )}
              </div>
            </section>
          </div>

          <section className="report-card">
            <div className="card-heading">
              <span>💡</span>
              Quick Resume Insights
            </div>

            <div className="analysis-grid">
              <div className="analysis-box">
                <h3>
                  📄 Resume Length
                </h3>

                <p className="insight-value">
                  {result.word_count ||
                    0}{" "}
                  words
                </p>

                <p className="muted">
                  Resume content detected by
                  ResumeAI.
                </p>
              </div>

              <div className="analysis-box">
                <h3>
                  🛠️ Technical Skills
                </h3>

                <p className="insight-value">
                  {skills.length}
                </p>

                <p className="muted">
                  Recognizable technical skills
                  detected.
                </p>
              </div>

              <div className="analysis-box">
                <h3>
                  📌 Resume Sections
                </h3>

                <p className="insight-value">
                  {detectedSections.length}
                </p>

                <p className="muted">
                  Resume sections detected
                  successfully.
                </p>
              </div>

              <div className="analysis-box">
                <h3>
                  📈 Measurable Evidence
                </h3>

                <p className="insight-value">
                  {Array.isArray(
                    result.metrics_found
                  )
                    ? result.metrics_found
                        .length
                    : 0}
                </p>

                <p className="muted">
                  Metrics and measurable evidence
                  found.
                </p>
              </div>
            </div>
          </section>

          <section className="report-card">
            <div className="card-heading">
              <span>📈</span>
              Score Breakdown
            </div>

            <div className="breakdown-grid">
              {Object.entries(
                breakdown
              ).map(
                ([key, value]) => (
                  <div
                    className="breakdown-item"
                    key={key}
                  >
                    <div>
                      {key
                        .replace(
                          /_/g,
                          " "
                        )
                        .replace(
                          /\b\w/g,
                          (char) =>
                            char.toUpperCase()
                        )}
                    </div>

                    <strong>
                      {value}
                    </strong>
                  </div>
                )
              )}
            </div>
          </section>

          <section className="report-card">
            <div className="card-heading">
              <span>✨</span>
              Content Analysis
            </div>

            <div className="analysis-grid">
              <div className="analysis-box">
                <h3>
                  ✅ Strengths
                </h3>

                {strengths.length >
                0 ? (
                  <ul>
                    {strengths.map(
                      (
                        item,
                        index
                      ) => (
                        <li
                          key={index}
                        >
                          {item}
                        </li>
                      )
                    )}
                  </ul>
                ) : (
                  <p className="muted">
                    No major strengths were
                    detected yet.
                  </p>
                )}
              </div>

              <div className="analysis-box">
                <h3>
                  ⚠️ Improvements
                </h3>

                {suggestions.length >
                0 ? (
                  <ul>
                    {suggestions.map(
                      (
                        item,
                        index
                      ) => (
                        <li
                          key={index}
                        >
                          {item}
                        </li>
                      )
                    )}
                  </ul>
                ) : (
                  <p className="muted">
                    No major improvements
                    detected.
                  </p>
                )}
              </div>
            </div>
          </section>

          <section className="report-card">
            <div className="card-heading">
              <span>🛠️</span>
              Detected Skills
            </div>

            <div className="skills-list">
              {skills.length >
              0 ? (
                skills.map(
                  (
                    skill,
                    index
                  ) => (
                    <span
                      className="skill-chip"
                      key={index}
                    >
                      {skill}
                    </span>
                  )
                )
              ) : (
                <p className="muted">
                  No recognizable technical
                  skills were detected.
                </p>
              )}
            </div>
          </section>

          <section className="report-card ai-advisor">
            <div className="card-heading">
              <span>🤖</span>
              AI Career Advisor
            </div>

            {aiStatus ===
              "processing" && (
              <div className="ai-loading">
                AI is reviewing your resume...
              </div>
            )}

            {aiAdvice &&
              aiAdvice.success && (
                <div className="feedback-content">
                  <div className="feedback-block">
                    <h3>
                      Overall Advice
                    </h3>

                    <p>
                      {aiAdvice.overall_advice}
                    </p>
                  </div>

                  {aiAdvice.high_priority_issues
                    ?.length >
                    0 && (
                    <div className="feedback-block">
                      <h3>
                        🔴 High Priority
                      </h3>

                      <ul>
                        {aiAdvice.high_priority_issues.map(
                          (
                            item,
                            index
                          ) => (
                            <li
                              key={
                                index
                              }
                            >
                              {item}
                            </li>
                          )
                        )}
                      </ul>
                    </div>
                  )}

                  {aiAdvice.medium_priority_issues
                    ?.length >
                    0 && (
                    <div className="feedback-block">
                      <h3>
                        🟡 Medium Priority
                      </h3>

                      <ul>
                        {aiAdvice.medium_priority_issues.map(
                          (
                            item,
                            index
                          ) => (
                            <li
                              key={
                                index
                              }
                            >
                              {item}
                            </li>
                          )
                        )}
                      </ul>
                    </div>
                  )}

                  {aiAdvice.strengths
                    ?.length >
                    0 && (
                    <div className="feedback-block">
                      <h3>
                        🟢 Strengths
                      </h3>

                      <ul>
                        {aiAdvice.strengths.map(
                          (
                            item,
                            index
                          ) => (
                            <li
                              key={
                                index
                              }
                            >
                              {item}
                            </li>
                          )
                        )}
                      </ul>
                    </div>
                  )}

                  {aiAdvice.actionable_suggestions
                    ?.length >
                    0 && (
                    <div className="feedback-block">
                      <h3>
                        🎯 Actionable Suggestions
                      </h3>

                      <ul>
                        {aiAdvice.actionable_suggestions.map(
                          (
                            item,
                            index
                          ) => (
                            <li
                              key={
                                index
                              }
                            >
                              {item}
                            </li>
                          )
                        )}
                      </ul>
                    </div>
                  )}
                </div>
              )}

            {aiStatus ===
              "failed" && (
              <p className="muted">
                AI advisor could not complete
                right now. Your rule-based report
                is still available.
              </p>
            )}
          </section>

          <section className="report-card">
            <div className="card-heading">
              <span>💬</span>
              AI Career Chat
            </div>

            <p className="muted">
              Ask anything about this resume in
              English, Hindi or Hinglish.
            </p>

            <div className="chat-box">
              <div className="chat-messages">
                {chatMessages.length ===
                  0 && (
                  <div className="chat-empty">
                    Ask your first question about
                    the resume.
                  </div>
                )}

                {chatMessages.map(
                  (
                    message,
                    index
                  ) => (
                    <div
                      className={`chat-message ${message.role}`}
                      key={index}
                    >
                      <div className="chat-role">
                        {message.role ===
                        "user"
                          ? "You"
                          : "ResumeAI"}
                      </div>

                      <div className="chat-text">
                        {message.text}
                      </div>
                    </div>
                  )
                )}

                {chatLoading && (
                  <div className="chat-message assistant">
                    <div className="chat-role">
                      ResumeAI
                    </div>

                    <div className="chat-text">
                      Thinking...
                    </div>
                  </div>
                )}
              </div>

              <div className="chat-input-row">
                <textarea
                  value={chatInput}
                  onChange={(event) =>
                    setChatInput(
                      event.target.value
                    )
                  }
                  onKeyDown={
                    handleChatKeyDown
                  }
                  placeholder="Ask about your resume..."
                  rows={2}
                  disabled={
                    chatLoading
                  }
                />

                <button
                  onClick={
                    sendChatMessage
                  }
                  disabled={
                    chatLoading ||
                    !chatInput.trim()
                  }
                >
                  Send
                </button>
              </div>
            </div>
          </section>

          <section className="report-card">
            <div className="card-heading">
              <span>🎯</span>
              Action Plan
            </div>

            {actionPlan.length >
            0 ? (
              <div className="action-plan">
                {actionPlan.map(
                  (
                    item,
                    index
                  ) => (
                    <div
                      className="action-item"
                      key={index}
                    >
                      <div className="action-number">
                        {index + 1}
                      </div>

                      <div>
                        {item}
                      </div>
                    </div>
                  )
                )}
              </div>
            ) : (
              <p className="muted">
                No action items available.
              </p>
            )}
          </section>

          <section className="report-card enhance-card">
            <div className="card-heading">
              <span>✨</span>
              Enhance My Resume
            </div>

            <div className="enhance-content">
              <div>
                <h2>
                  Create a professional PDF
                </h2>

                <p>
                  ResumeAI will improve the
                  wording and structure while
                  preserving the actual facts in
                  your resume.
                </p>

                <div className="enhance-features">
                  <span>
                    ✓ Professional formatting
                  </span>

                  <span>
                    ✓ ATS-friendly structure
                  </span>

                  <span>
                    ✓ Bold section headings
                  </span>

                  <span>
                    ✓ Clean bullet points
                  </span>

                  <span>
                    ✓ Original photo preserved
                    when available
                  </span>

                  <span>
                    ✓ Optional photo when not
                    available
                  </span>
                </div>
              </div>

              {!showEnhancePhotoOptions &&
                !enhancedResume && (
                  <button
                    className="enhance-button"
                    onClick={
                      handleEnhanceClick
                    }
                    disabled={
                      enhancing ||
                      checkingPhoto
                    }
                  >
                    {checkingPhoto
                      ? "Checking Resume..."
                      : "Enhance Resume →"}
                  </button>
                )}
            </div>

            {originalPhotoDetected ===
              true &&
              enhancing && (
                <div className="enhance-info">
                  Original profile photo detected.
                  Preserving it in the enhanced
                  resume...
                </div>
              )}

            {showEnhancePhotoOptions &&
              !enhancedResume && (
                <div className="enhance-photo-options">
                  <div className="enhance-photo-header">
                    <h3>
                      Add a Profile Photo
                      <span>
                        {" "}
                        (Optional)
                      </span>
                    </h3>

                    <p>
                      No profile photo was detected
                      in your original resume.
                      You can add one to the
                      professional PDF or skip it.
                    </p>
                  </div>

                  <div className="enhance-photo-actions">
                    <label className="photo-button">
                      {photo
                        ? "Change Photo"
                        : "Add Photo"}

                      <input
                        type="file"
                        accept=".jpg,.jpeg,.png"
                        onChange={
                          handlePhotoChange
                        }
                        hidden
                      />
                    </label>

                    <button
                      type="button"
                      className="enhance-button"
                      onClick={
                        skipPhotoAndEnhance
                      }
                      disabled={
                        enhancing
                      }
                    >
                      {enhancing
                        ? "Creating PDF..."
                        : "Skip Photo & Enhance"}
                    </button>
                  </div>

                  {photoPreview && (
                    <div className="photo-preview-wrap">
                      <img
                        src={photoPreview}
                        alt="Selected profile preview"
                        className="photo-preview"
                      />

                      <button
                        type="button"
                        className="enhance-button"
                        onClick={
                          addPhotoAndEnhance
                        }
                        disabled={
                          enhancing
                        }
                      >
                        {enhancing
                          ? "Creating PDF..."
                          : "Create Enhanced Resume"}
                      </button>
                    </div>
                  )}
                </div>
              )}

            {enhanceError && (
              <div className="enhance-error">
                {enhanceError}
              </div>
            )}

            {enhancedResume && (
              <div className="enhanced-result">
                <div className="enhanced-result-header">
                  <div>
                    <h3>
                      Professional Resume
                      Preview
                    </h3>

                    <p>
                      Your enhanced resume is
                      ready.
                    </p>
                  </div>

                  <button
                    className="download-button"
                    onClick={
                      downloadEnhancedPDF
                    }
                  >
                    ⬇ Download Professional
                    PDF
                  </button>
                </div>

                <div className="resume-paper">
                  {renderEnhancedPreview(
                    enhancedResume
                  )}
                </div>
              </div>
            )}
          </section>

          <button
            className="details-button"
            onClick={() =>
              setShowDetails(
                !showDetails
              )
            }
          >
            {showDetails
              ? "Hide Technical Details"
              : "Show Technical Details"}
          </button>

          {showDetails && (
            <section className="report-card technical-details">
              <div className="card-heading">
                <span>🔍</span>
                Technical Details
              </div>

              <pre>
                {JSON.stringify(
                  result,
                  null,
                  2
                )}
              </pre>
            </section>
          )}
        </main>
      )}
    </div>
  );
}

export default App;