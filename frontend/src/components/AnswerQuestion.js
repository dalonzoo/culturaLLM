"use client"

import { useState, useEffect } from "react"
import api from "../services/api"

function AnswerQuestion() {
  const [questions, setQuestions] = useState([])
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0)
  const [answer, setAnswer] = useState("")
  const [loading, setLoading] = useState(false)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState("")
  const [success, setSuccess] = useState("")
  const [validationResult, setValidationResult] = useState(null)

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
      setError("Errore nel caricamento delle domande")
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

    try {
      const currentQuestion = questions[currentQuestionIndex]
      
      // Prima invia la risposta
      const answerResponse = await api.post("/api/answers/", {
        text: answer,
        question_id: currentQuestion.id,
      })

      // Poi valuta la risposta
      const validationResponse = await api.post("/api/cultural-questions/evaluate-answer", {
        question_id: currentQuestion.id,
        answer_text: answer
      })

      setValidationResult({
        score: validationResponse.data.score,
        evaluation: validationResponse.data.evaluation
      })
      setSuccess("Risposta inviata e valutata con successo!")
      setAnswer("")

      // Move to next question or refresh list
      if (currentQuestionIndex < questions.length - 1) {
        setCurrentQuestionIndex(currentQuestionIndex + 1)
      } else {
        // Refresh questions list
        fetchPendingQuestions()
        setCurrentQuestionIndex(0)
      }

      setTimeout(() => {
        setSuccess("")
        setValidationResult(null)
      }, 5000)
    } catch (error) {
      setError(error.response?.data?.detail || "Errore nell'invio della risposta")
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
    setValidationResult(null)
  }

  const getScoreColor = (score) => {
    if (score <= 2) return '#ff1a1a';
    if (score <= 4) return '#ff4d4d';
    if (score <= 6) return '#ffa64d';
    if (score <= 8) return '#80cc33';
    return '#4CAF50';
  }

  const getQualitativeScore = (score) => {
    if (score <= 2) return "Completamente sbagliata";
    if (score <= 4) return "Insufficiente";
    if (score <= 6) return "Parzialmente corretta";
    if (score <= 8) return "Buona risposta";
    return "Risposta eccellente";
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

            {validationResult && (
              <div className="validation-result" style={{ marginTop: '1rem' }}>
                <h4>Valutazione della risposta:</h4>
                <div className="validation-badge" style={{
                  backgroundColor: `${getScoreColor(validationResult.score)}20`,
                  color: getScoreColor(validationResult.score),
                  borderColor: `${getScoreColor(validationResult.score)}40`
                }}>
                  {getQualitativeScore(validationResult.score)}
                </div>
                <p className="validation-feedback">{validationResult.evaluation}</p>
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
