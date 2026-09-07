import { useState } from "react";
import "./App.css";

function App() {
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);

  function handleFile(event) {
    const selectedFile = event.target.files[0];

    if (!selectedFile) {
      return;
    }

    const name = selectedFile.name.toLowerCase();

    if (!name.endsWith(".pdf") && !name.endsWith(".docx")) {
      alert("Please upload a PDF or DOCX resume.");
      return;
    }

    setFile(selectedFile);
    setResult(null);
  }

  async function analyzeResume() {
    if (!file) {
      alert("Please upload your resume first.");
      return;
    }

    setLoading(true);
    setResult(null);

    const formData = new FormData();
    formData.append("file", file);

    try {
      const response = await fetch(
        "https://resume-ai-analyer.onrender.com/analyze",
        {
          method: "POST",
          body: formData
        }
      );

      const data = await response.json();

      setResult(data);
    } catch (error) {
      setResult({
        success: false,
        message:
          "Backend se connection nahi ho raha. FastAPI server check karo."
      });
    } finally {
      setLoading(false);
    }
  }

  function resetApp() {
    setFile(null);
    setResult(null);
  }

  function scoreText(score) {
    if (score >= 80) {
      return "Strong Resume";
    }

    if (score >= 60) {
      return "Good, but can improve";
    }

    if (score >= 40) {
      return "Needs Improvement";
    }

    return "Major Improvements Needed";
  }

  function scoreClass(score) {
    if (score >= 80) {
      return "score-good";
    }

    if (score >= 60) {
      return "score-average";
    }

    return "score-low";
  }

  function showAIAdvice(advice) {
    if (!advice) {
      return (
        <p className="muted">
          AI advice is currently unavailable.
        </p>
      );
    }

    if (typeof advice === "string") {
      return (
        <div className="ai-text">
          {advice}
        </div>
      );
    }

    return (
      <pre className="ai-text">
        {JSON.stringify(advice, null, 2)}
      </pre>
    );
  }

  return (
    <div className="app">

      <header className="topbar">

        <div className="brand">

          <div className="brand-logo">
            R
          </div>

          <div>
            <div className="brand-name">
              Resume<span>AI</span>
            </div>

            <div className="brand-subtitle">
              INTELLIGENT RESUME ANALYZER
            </div>
          </div>

        </div>

        <div className="engine-status">
          <span className="status-dot"></span>
          AI ANALYSIS ENGINE
        </div>

      </header>


      {!result && (

        <main className="home-page">

          <section className="hero">

            <div className="eyebrow">
              AI-POWERED CAREER INTELLIGENCE
            </div>

            <h1>
              Make your resume
              <br />
              <span>impossible to ignore.</span>
            </h1>

            <p className="hero-description">
              Get an honest resume score, ATS insights,
              skill detection and personalized AI career advice.
            </p>

          </section>


          <section className="upload-card">

            <div className="upload-icon">
              ↑
            </div>

            <h2>
              Upload your Resume
            </h2>

            <p>
              Upload a PDF or DOCX resume to begin the analysis.
            </p>


            <label className="choose-button">

              Choose Resume

              <input
                type="file"
                accept=".pdf,.docx"
                onChange={handleFile}
              />

            </label>


            {file && (

              <div className="selected-file">

                <div className="file-type">
                  {file.name.toLowerCase().endsWith(".pdf")
                    ? "PDF"
                    : "DOCX"}
                </div>

                <div className="file-details">

                  <strong>
                    {file.name}
                  </strong>

                  <span>
                    {(file.size / 1024).toFixed(1)} KB
                  </span>

                </div>

                <div className="file-ok">
                  ✓
                </div>

              </div>

            )}


            <button
              className="analyze-button"
              onClick={analyzeResume}
              disabled={loading}
            >

              {loading ? (
                <>
                  <span className="loading-spinner"></span>
                  Analyzing Resume...
                </>
              ) : (
                <>
                  Analyze Resume
                  <span>→</span>
                </>
              )}

            </button>


            <div className="privacy">
              Your resume is analyzed from the document you upload.
            </div>

          </section>

        </main>

      )}


      {result && !result.success && (

        <main className="error-page">

          <div className="error-card">

            <div className="error-symbol">
              !
            </div>

            <h1>
              Resume Not Accepted
            </h1>

            <p>
              {result.message}
            </p>

            <button
              className="analyze-button"
              onClick={resetApp}
            >
              Upload Another Resume
              <span>→</span>
            </button>

          </div>

        </main>

      )}


      {result && result.success && (

        <main className="dashboard">

          <aside className="sidebar">

            <button
              className="new-analysis-button"
              onClick={resetApp}
            >
              + New Analysis
            </button>


            <div className="score-panel">

              <div className="panel-label">
                RESUME SCORE
              </div>

              <div
                className={
                  "score-circle " + scoreClass(result.score)
                }
              >

                <div className="score-number">
                  {result.score}
                  <span>/100</span>
                </div>

              </div>

              <div className="score-status">
                {scoreText(result.score)}
              </div>

            </div>


            <div className="sidebar-section">

              <div className="sidebar-title">
                RESUME SECTIONS
              </div>

              <div className="section-tags">

                {result.detected_sections &&
                  result.detected_sections.map(
                    function (section, index) {
                      return (
                        <span key={index}>
                          ✓ {section}
                        </span>
                      );
                    }
                  )}

              </div>

            </div>


            <div className="sidebar-section">

              <div className="sidebar-title">
                DETECTED SKILLS
              </div>

              <div className="skill-count">
                {result.skills_detected || 0}
              </div>

            </div>

          </aside>


          <section className="report">

            <div className="report-header">

              <div>

                <div className="eyebrow">
                  RESUME ANALYSIS
                </div>

                <h1>
                  Your Resume Report
                </h1>

                <p>
                  Detailed feedback based on your actual resume.
                </p>

              </div>


              {file && (

                <div className="uploaded-file">

                  <strong>
                    {file.name}
                  </strong>

                  <span>
                    Analysis complete
                  </span>

                </div>

              )}

            </div>


            <div className="stats-grid">

              <div className="stat-card">

                <div className="stat-icon">
                  ◎
                </div>

                <div>
                  <small>RESUME SCORE</small>
                  <strong>{result.score}/100</strong>
                </div>

              </div>


              <div className="stat-card">

                <div className="stat-icon">
                  ✓
                </div>

                <div>
                  <small>SKILLS DETECTED</small>
                  <strong>{result.skills_detected || 0}</strong>
                </div>

              </div>


              <div className="stat-card">

                <div className="stat-icon">
                  #
                </div>

                <div>
                  <small>METRICS FOUND</small>

                  <strong>
                    {result.metrics_found
                      ? result.metrics_found.length
                      : 0}
                  </strong>

                </div>

              </div>


              <div className="stat-card">

                <div className="stat-icon">
                  ✦
                </div>

                <div>
                  <small>ACTION VERBS</small>

                  <strong>
                    {result.action_verbs_found
                      ? result.action_verbs_found.length
                      : 0}
                  </strong>

                </div>

              </div>

            </div>


            <div className="report-card">

              <div className="card-heading">

                <div>

                  <div className="card-label">
                    CONTENT
                  </div>

                  <h2>
                    Content Analysis
                  </h2>

                  <p>
                    Important observations from your resume.
                  </p>

                </div>

                <div className="issue-count">

                  {result.suggestions
                    ? result.suggestions.length
                    : 0}

                  {" "}ISSUES

                </div>

              </div>


              <div className="feedback-section">

                <h3>
                  ⚠️ High Priority
                </h3>


                {result.suggestions &&
                result.suggestions.length > 0 ? (

                  result.suggestions
                    .slice(0, 3)
                    .map(function (suggestion, index) {

                      return (
                        <div
                          className="feedback-item"
                          key={index}
                        >

                          <div className="feedback-icon">
                            ×
                          </div>

                          <div>
                            <strong>
                              Improvement needed
                            </strong>

                            <p>
                              {suggestion}
                            </p>
                          </div>

                        </div>
                      );
                    })

                ) : (

                  <p className="muted">
                    No major improvement suggestions were detected.
                  </p>

                )}

              </div>


              <div className="feedback-section">

                <h3 className="positive-heading">
                  ✓ Strengths
                </h3>


                {result.strengths &&
                result.strengths.length > 0 ? (

                  result.strengths.map(
                    function (strength, index) {

                      return (
                        <div
                          className="feedback-item"
                          key={index}
                        >

                          <div className="feedback-icon positive">
                            ✓
                          </div>

                          <div>
                            <p>
                              {strength}
                            </p>
                          </div>

                        </div>
                      );
                    }
                  )

                ) : (

                  <p className="muted">
                    No strengths detected.
                  </p>

                )}

              </div>

            </div>


            <div className="report-card">

              <div className="card-heading">

                <div>

                  <div className="card-label">
                    SKILLS
                  </div>

                  <h2>
                    Skills Detected
                  </h2>

                  <p>
                    Skills found directly in your uploaded resume.
                  </p>

                </div>

              </div>


              <div className="skills-container">

                {result.skills &&
                result.skills.length > 0 ? (

                  result.skills.map(
                    function (skill, index) {

                      return (
                        <span key={index}>
                          {skill}
                        </span>
                      );
                    }
                  )

                ) : (

                  <p className="muted">
                    No specific skills detected.
                  </p>

                )}

              </div>

            </div>


            <div className="ai-advisor">

              <div className="ai-header">

                <div className="ai-logo">
                  ✦
                </div>

                <div>

                  <div className="ai-label">
                    AI CAREER ADVISOR
                  </div>

                  <h2>
                    Personalized AI Advice
                  </h2>

                </div>

              </div>


              <div className="ai-body">
                {showAIAdvice(result.ai_feedback)}
              </div>

            </div>


            <div className="report-card">

              <div className="card-heading">

                <div>

                  <div className="card-label">
                    ACTION PLAN
                  </div>

                  <h2>
                    Recommended Improvements
                  </h2>

                  <p>
                    Changes you can make to improve the resume.
                  </p>

                </div>

              </div>


              <div className="recommendations">

                {result.suggestions &&
                result.suggestions.length > 0 ? (

                  result.suggestions.map(
                    function (suggestion, index) {

                      return (
                        <div
                          className="recommendation"
                          key={index}
                        >

                          <div className="recommendation-number">
                            {index + 1}
                          </div>

                          <p>
                            {suggestion}
                          </p>

                        </div>
                      );
                    }
                  )

                ) : (

                  <p className="muted">
                    No additional recommendations.
                  </p>

                )}

              </div>

            </div>


            <footer className="report-footer">

              <span>
                ResumeAI • Intelligent Resume Analysis
              </span>

              <span>
                Generated from your uploaded resume
              </span>

            </footer>

          </section>

        </main>

      )}

    </div>
  );
}

export default App;