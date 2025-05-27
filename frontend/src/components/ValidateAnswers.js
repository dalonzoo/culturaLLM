"use client"

import { useState, useEffect } from "react"
import api from "../services/api"

function ValidateAnswers() {
  const [pendingAnswers, setPendingAnswers] = useState([])
  const [currentAnswerIndex, setCurrentAnswerIndex] = useState(0)
  const [validation, setValidation] = useState({
    human_score: 5,
    human_is_correct: true,
    human_feedback: "",
    llm_score: 5,
    llm_is_correct: true,
    llm_feedback: "",
  })
  const [loading, setLoading] = useState(false)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState("")
  const [success, setSuccess] = useState("")

  useEffect(() => {
    fetchPendingValidations()
  }, [])

  const fetchPendingValidations = async () => {
    setLoading(true)
    try {
      const response = await api.get("/api/validate/pending")
      console.log("Risposta API:", response.data) // Debug log
      if (Array.isArray(response.data)) {
        setPendingAnswers(response.data)
        if (response.data.length === 0) {
          setError("Non ci sono risposte da validare al momento")
        }
      } else {
        setError("Formato risposta non valido")
      }
    } catch (error) {
      console.error("Errore API:", error) // Debug log
      setError(error.response?.data?.detail || "Errore nel caricamento delle risposte")
    }
    setLoading(false)
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setSubmitting(true)
    setError("")
    setSuccess("")

    try {
      const currentAnswer = pendingAnswers[currentAnswerIndex]
      if (!currentAnswer?.answer?.id) {
        throw new Error("ID risposta non valido")
      }

      // Validate human answer
      await api.post("/api/validate/", {
        answer_id: currentAnswer.answer.id,
        score: Number.parseFloat(validation.human_score),
        is_correct: validation.human_is_correct,
        feedback: validation.human_feedback,
      })

      // Validate LLM answer if exists
      if (currentAnswer.llm_answer) {
        await api.post("/api/validate/", {
          answer_id: currentAnswer.llm_answer.id,
          score: Number.parseFloat(validation.llm_score),
          is_correct: validation.llm_is_correct,
          feedback: validation.llm_feedback,
        })
      }

      setSuccess("Validazioni inviate con successo!")

      // Move to next answer or refresh list
      if (currentAnswerIndex < pendingAnswers.length - 1) {
        setCurrentAnswerIndex(currentAnswerIndex + 1)
      } else {
        fetchPendingValidations()
        setCurrentAnswerIndex(0)
      }

      // Reset validation form
      setValidation({
        human_score: 5,
        human_is_correct: true,
        human_feedback: "",
        llm_score: 5,
        llm_is_correct: true,
        llm_feedback: "",
      })

      setTimeout(() => setSuccess(""), 3000)
    } catch (error) {
      console.error("Errore validazione:", error)
      setError(error.response?.data?.detail || "Errore nell'invio della validazione")
    }

    setSubmitting(false)
  }

  const handleSkip = () => {
    if (currentAnswerIndex < pendingAnswers.length - 1) {
      setCurrentAnswerIndex(currentAnswerIndex + 1)
    } else {
      setCurrentAnswerIndex(0)
    }
    setValidation({
      human_score: 5,
      human_is_correct: true,
      human_feedback: "",
      llm_score: 5,
      llm_is_correct: true,
      llm_feedback: "",
    })
    setError("")
    setSuccess("")
  }

  if (loading) {
    return <div className="loading">Caricamento risposte...</div>
  }

  if (pendingAnswers.length === 0) {
    return (
      <div className="no-content">
        <h2>Nessuna risposta da validare</h2>
        <p>Non ci sono risposte da validare al momento. Torna più tardi!</p>
      </div>
    )
  }

  const currentAnswer = pendingAnswers[currentAnswerIndex]

  if (!currentAnswer?.answer || !currentAnswer?.question) {
    return <div className="error-message">Dati non validi per questa risposta</div>
  }

  return (
    <div className="validate-answers">
      <div className="page-header">
        <h1>Valida le Risposte ✅</h1>
        <p>
          Risposta {currentAnswerIndex + 1} di {pendingAnswers.length}
        </p>
      </div>

      <div className="validation-container">
        {error && <div className="error-message">{error}</div>}
        {success && <div className="success-message">{success}</div>}

        <div className="answer-card">
          <div className="question-section">
            <h3>Domanda:</h3>
            <p className="question-text">{currentAnswer.question.text}</p>
            <span className="theme-badge">{currentAnswer.question.theme?.name}</span>
          </div>

          <div className="answer-section">
            <h3>Risposta da validare:</h3>
            <div className="answer-content">
              <p>{currentAnswer.answer.text}</p>
              <div className="answer-meta">
                {currentAnswer.answer.is_llm_answer ? (
                  <span className="llm-badge">🤖 Risposta IA</span>
                ) : (
                  <span className="human-badge">👤 Risposta Umana</span>
                )}
              </div>
            </div>
          </div>

          {currentAnswer.llm_answer && (
            <div className="llm-answer-section">
              <h3>Risposta IA:</h3>
              <div className="answer-content">
                <p>{currentAnswer.llm_answer.text}</p>
                <div className="answer-meta">
                  <span className="llm-badge">🤖 Risposta IA</span>
                </div>
              </div>
            </div>
          )}
        </div>

        <form onSubmit={handleSubmit} className="validation-form">
          <div className="validation-section">
            <h3>Validazione Risposta Umana</h3>
            <div className="form-group">
              <label>Questa risposta è corretta?</label>
              <div className="radio-group">
                <label className="radio-label">
                  <input
                    type="radio"
                    name="human_is_correct"
                    checked={validation.human_is_correct === true}
                    onChange={() => setValidation({ ...validation, human_is_correct: true })}
                    disabled={submitting}
                  />
                  ✅ Corretta
                </label>
                <label className="radio-label">
                  <input
                    type="radio"
                    name="human_is_correct"
                    checked={validation.human_is_correct === false}
                    onChange={() => setValidation({ ...validation, human_is_correct: false })}
                    disabled={submitting}
                  />
                  ❌ Incorretta
                </label>
              </div>
            </div>

            <div className="form-group">
              <label htmlFor="human_score">Punteggio (1-10):</label>
              <input
                type="range"
                id="human_score"
                min="1"
                max="10"
                step="0.5"
                value={validation.human_score}
                onChange={(e) => setValidation({ ...validation, human_score: e.target.value })}
                disabled={submitting}
              />
              <div className="score-display">
                <span className="score-value">{validation.human_score}/10</span>
              </div>
            </div>

            <div className="form-group">
              <label htmlFor="human_feedback">Feedback (opzionale):</label>
              <textarea
                id="human_feedback"
                value={validation.human_feedback}
                onChange={(e) => setValidation({ ...validation, human_feedback: e.target.value })}
                placeholder="Aggiungi un commento sulla risposta umana..."
                rows="3"
                disabled={submitting}
              />
            </div>
          </div>

          {currentAnswer.llm_answer && (
            <div className="validation-section">
              <h3>Validazione Risposta IA</h3>
              <div className="form-group">
                <label>Questa risposta è corretta?</label>
                <div className="radio-group">
                  <label className="radio-label">
                    <input
                      type="radio"
                      name="llm_is_correct"
                      checked={validation.llm_is_correct === true}
                      onChange={() => setValidation({ ...validation, llm_is_correct: true })}
                      disabled={submitting}
                    />
                    ✅ Corretta
                  </label>
                  <label className="radio-label">
                    <input
                      type="radio"
                      name="llm_is_correct"
                      checked={validation.llm_is_correct === false}
                      onChange={() => setValidation({ ...validation, llm_is_correct: false })}
                      disabled={submitting}
                    />
                    ❌ Incorretta
                  </label>
                </div>
              </div>

              <div className="form-group">
                <label htmlFor="llm_score">Punteggio (1-10):</label>
                <input
                  type="range"
                  id="llm_score"
                  min="1"
                  max="10"
                  step="0.5"
                  value={validation.llm_score}
                  onChange={(e) => setValidation({ ...validation, llm_score: e.target.value })}
                  disabled={submitting}
                />
                <div className="score-display">
                  <span className="score-value">{validation.llm_score}/10</span>
                </div>
              </div>

              <div className="form-group">
                <label htmlFor="llm_feedback">Feedback (opzionale):</label>
                <textarea
                  id="llm_feedback"
                  value={validation.llm_feedback}
                  onChange={(e) => setValidation({ ...validation, llm_feedback: e.target.value })}
                  placeholder="Aggiungi un commento sulla risposta IA..."
                  rows="3"
                  disabled={submitting}
                />
              </div>
            </div>
          )}

          <div className="form-actions">
            <button type="button" onClick={handleSkip} className="btn btn-outline" disabled={submitting}>
              Salta
            </button>
            <button type="submit" className="btn btn-primary" disabled={submitting}>
              {submitting ? "Invio in corso..." : "Invia Validazioni"}
            </button>
          </div>
        </form>

        <div className="progress-bar">
          <div
            className="progress-fill"
            style={{ width: `${((currentAnswerIndex + 1) / pendingAnswers.length) * 100}%` }}
          ></div>
        </div>
      </div>
    </div>
  )
}

export default ValidateAnswers
