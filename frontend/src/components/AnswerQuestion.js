"use client"

import { useState, useEffect } from "react"
import api from "../services/api"

const getErrorMessage = (error, defaultMessage) => {
  if (error.response && error.response.data && error.response.data.detail) {
    const { detail } = error.response.data
    if (typeof detail === "string") {
      return detail
    }
    if (Array.isArray(detail)) {
      // Handle FastAPI validation errors
      return detail.map((err) => `${err.loc.join(" -> ")}: ${err.msg}`).join("; ")
    }
  }
  if (error.message) {
    return error.message
  }
  return defaultMessage
}

function AnswerQuestion() {
  const [questions, setQuestions] = useState([])
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0)
  const [answer, setAnswer] = useState("")
  const [loading, setLoading] = useState(false)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState("")
  const [success, setSuccess] = useState("")
  const [validationResult, setValidationResult] = useState(null)
  const [showValidation, setShowValidation] = useState(false)

  useEffect(() => {
    fetchPendingQuestions()
  }, [])

  const fetchPendingQuestions = async () => {
    setLoading(true)
    try {
      const response = await api.get("/api/questions/pending/answer")
      setQuestions(response.data)
      if (response.data.length === 0) {
        setError("Non ci sono domande disponibili al momento")
      }
    } catch (error) {
      setError(getErrorMessage(error, "Errore nel caricamento delle domande"))
    }
    setLoading(false)
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!answer.trim()) return

    setSubmitting(true)
    setError("")
    setSuccess("")
    setValidationResult(null)
    setShowValidation(false)

    try {
      const currentQuestion = questions[currentQuestionIndex]
      
      // First submit the answer
      await api.post("/api/answers/", {
        text: answer,
        question_id: currentQuestion.id,
      })

      // Then validate the answer
      const validationResponse = await api.post("/api/answers/validate", {
        answer_text: answer,
        question_id: currentQuestion.id,
      })

      setValidationResult(validationResponse.data)
      setShowValidation(true)
      
      if (validationResponse.data.is_correct) {
        setSuccess("Risposta corretta! Ben fatto!")
      } else {
        setError("La risposta non è completamente corretta. Controlla il feedback dell'AI.")
      }

      // Wait for user to see the validation result before moving to next question
      setTimeout(() => {
        if (currentQuestionIndex < questions.length - 1) {
          setCurrentQuestionIndex(currentQuestionIndex + 1)
          setAnswer("")
          setShowValidation(false)
          setValidationResult(null)
        } else {
          // Refresh questions list
          fetchPendingQuestions()
          setCurrentQuestionIndex(0)
          setAnswer("")
          setShowValidation(false)
          setValidationResult(null)
        }
      }, 5000)

    } catch (error) {
      setError(getErrorMessage(error, "Errore nell'invio della risposta"))
    }

    setSubmitting(false)
  }

  const handleSkip = () => {
    if (currentQuestionIndex < questions.length - 1) {
      setCurrentQuestionIndex(currentQuestionIndex + 1)
    } else {
      setCurrentQuestionIndex(0)
    }
    setAnswer("")
    setError("")
    setSuccess("")
  }

  if (loading) {
    return <div className="loading">Caricamento domande...</div>
  }

  if (questions.length === 0) {
    return (
      <div className="no-content">
        <h2>Nessuna domanda disponibile</h2>
        <p>Non ci sono domande da rispondere al momento. Torna più tardi!</p>
      </div>
    )
  }

  const currentQuestion = questions[currentQuestionIndex]

  return (
    <div className="answer-question">
      <div className="page-header">
        <h1>Rispondi alle Domande 💬</h1>
        <p>
          Domanda {currentQuestionIndex + 1} di {questions.length}
        </p>
      </div>

      <div className="question-container">
        {error && <div className="error-message">{error}</div>}
        {success && <div className="success-message">{success}</div>}

        <div className="question-card">
          <div className="question-theme">
            <span className="theme-badge">{currentQuestion.theme?.name}</span>
          </div>

          <h2 className="question-text">{currentQuestion.text}</h2>

          <form onSubmit={handleSubmit} className="answer-form">
            <div className="form-group">
              <label htmlFor="answer">La tua risposta:</label>
              <textarea
                id="answer"
                value={answer}
                onChange={(e) => setAnswer(e.target.value)}
                placeholder="Scrivi la tua risposta qui..."
                rows="4"
                required
                disabled={submitting}
              />
            </div>

            {showValidation && validationResult && (
              <div className={`validation-result ${validationResult.is_correct ? 'correct' : 'incorrect'}`}>
                <h3>{validationResult.is_correct ? '✅ Risposta Corretta!' : '❌ Risposta da Migliorare'}</h3>
                <p className="ai-feedback">{validationResult.feedback}</p>
                {!validationResult.is_correct && validationResult.correct_answer && (
                  <div className="correct-answer">
                    <strong>Risposta corretta:</strong>
                    <p>{validationResult.correct_answer}</p>
                  </div>
                )}
              </div>
            )}

            <div className="form-actions">
              <button type="button" onClick={handleSkip} className="btn btn-outline" disabled={submitting}>
                Salta
              </button>
              <button type="submit" className="btn btn-primary" disabled={submitting || !answer.trim()}>
                {submitting ? "Invio in corso..." : "Invia Risposta"}
              </button>
            </div>
          </form>
        </div>

        <div className="progress-bar">
          <div
            className="progress-fill"
            style={{ width: `${((currentQuestionIndex + 1) / questions.length) * 100}%` }}
          ></div>
        </div>
      </div>
    </div>
  )
}

export default AnswerQuestion
