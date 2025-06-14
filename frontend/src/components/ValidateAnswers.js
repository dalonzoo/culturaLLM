"use client"

import { useState, useEffect } from "react"
import api from "../services/api"

function formatLLMText(text) {
  if (!text) return '';
  // Sostituisci **testo** con <b>testo</b>
  let formatted = text.replace(/\*\*(.*?)\*\*/g, '<b>$1</b>');
  // Sostituisci \n con <br/>
  formatted = formatted.replace(/\n/g, '<br/>');
  return formatted;
}

function ValidateAnswers() {
  const [pendingAnswers, setPendingAnswers] = useState([])
  const [currentAnswerIndex, setCurrentAnswerIndex] = useState(0)
  const [validation, setValidation] = useState({
    human_score: 5.5,
    human_feedback: "",
    llm_score: 5.5,
    llm_feedback: "",
  })
  const [loading, setLoading] = useState(false)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState("")
  const [success, setSuccess] = useState("")
  const [llmValidation, setLlmValidation] = useState({
    human: null,
    llm: null
  })
  const [showLlmValidation, setShowLlmValidation] = useState(false)
  const [validationStep, setValidationStep] = useState('idle') // 'idle', 'submitting', 'llm_validating', 'completed'

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

  const getQualitativeScore = (score) => {
    if (score <= 2) return "Completamente sbagliata";
    if (score <= 4) return "Insufficiente";
    if (score <= 6) return "Parzialmente corretta";
    if (score <= 8) return "Buona risposta";
    return "Risposta eccellente";
  }

  const getScoreColor = (score) => {
    if (score <= 2) return '#ff1a1a';
    if (score <= 4) return '#ff4d4d';
    if (score <= 6) return '#ffa64d';
    if (score <= 8) return '#80cc33';
    return '#4CAF50';
  }

  const handleCloseValidation = () => {
    setShowLlmValidation(false)
    setLlmValidation({ human: null, llm: null })
    setValidationStep('idle')
    
    // Move to next answer or refresh list
    if (currentAnswerIndex < pendingAnswers.length - 1) {
      setCurrentAnswerIndex(currentAnswerIndex + 1)
    } else {
      fetchPendingValidations()
      setCurrentAnswerIndex(0)
    }

    // Reset validation form
    setValidation({
      human_score: 5.5,
      human_feedback: "",
      llm_score: 5.5,
      llm_feedback: "",
    })
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setSubmitting(true)
    setError("")
    setSuccess("")
    setValidationStep('submitting')

    try {
      const currentAnswer = pendingAnswers[currentAnswerIndex]
      if (!currentAnswer?.answer?.id) {
        throw new Error("ID risposta non valido")
      }

      // Prima invia la validazione umana
      await api.post("/api/validate/", {
        answer_id: currentAnswer.answer.id,
        score: Number.parseFloat(validation.human_score),
        is_correct: Number.parseFloat(validation.human_score) >= 6,
        feedback: validation.human_feedback,
      })

      setValidationStep('llm_validating')
      setSuccess("Validazione umana inviata. In attesa della validazione IA...")

      // Poi richiedi la validazione LLM
      const llmValidationResult = await api.post(`/api/validate/llm-validate?answer_id=${currentAnswer.answer.id}`)

      setLlmValidation({
        human: llmValidationResult.data[0],
        llm: llmValidationResult.data[1]
      })
      setShowLlmValidation(true)
      setValidationStep('completed')
      setSuccess("Validazioni completate!")

    } catch (error) {
      console.error("Errore validazione:", error)
      let errorMessage = "Errore nell'invio della validazione"
      
      if (error.response?.data?.detail) {
        if (Array.isArray(error.response.data.detail)) {
          errorMessage = error.response.data.detail.map(err => err.msg).join(", ")
        } else {
          errorMessage = error.response.data.detail
        }
      } else if (error.message) {
        errorMessage = error.message
      }
      
      setError(errorMessage)
      setValidationStep('idle')
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
      human_score: 5.5,
      human_feedback: "",
      llm_score: 5.5,
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

        {showLlmValidation && (llmValidation.human || llmValidation.llm) && (
          <div className="llm-validation-dialog">
            <div className="llm-validation-content">
              <button 
                className="close-button" 
                onClick={handleCloseValidation}
                aria-label="Chiudi validazione"
              >
                ×
              </button>
              <h3>Validazione IA 🤖</h3>
              <div className="validation-details">
                {llmValidation.human && (
                  <div className="validation-section">
                    <h4>Risposta 1</h4>
                    <div className="validation-score">
                      <span className="score-label">Punteggio:</span>
                      <span className={`score-value ${llmValidation.human.score >= 6 ? 'correct' : 'incorrect'}`}>
                        {llmValidation.human.score.toFixed(1)}/10
                      </span>
                    </div>
                    <div className="validation-feedback">
                      <span className="feedback-label">Feedback:</span>
                      <p className="feedback-text">{llmValidation.human.feedback}</p>
                    </div>
                  </div>
                )}
                
                {llmValidation.llm && (
                  <div className="validation-section">
                    <h4>Risposta 2</h4>
                    <div className="validation-score">
                      <span className="score-label">Punteggio:</span>
                      <span className={`score-value ${llmValidation.llm.score >= 6 ? 'correct' : 'incorrect'}`}>
                        {llmValidation.llm.score.toFixed(1)}/10
                      </span>
                    </div>
                    <div className="validation-feedback">
                      <span className="feedback-label">Feedback:</span>
                      <p className="feedback-text">{llmValidation.llm.feedback}</p>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

        <div className="answer-card">
          <div className="question-section">
            <h3>Domanda:</h3>
            <p className="question-text">{currentAnswer.question.text}</p>
            <span className="theme-badge">{currentAnswer.question.theme?.name}</span>
          </div>

          <div className="answer-section">
            <h3>Risposta 1:</h3>
            <div className="answer-content">
              <p>{currentAnswer.answer.text}</p>
            </div>
            {/* Validazione risposta umana */}
            <div className="validation-form">
              <div className="validation-section">
                <h3>Validazione</h3>
                <div className="form-group">
                  <label htmlFor="human_score">Valutazione:</label>
                  <div className="score-slider-container">
                    <input
                      type="range"
                      id="human_score"
                      min="1"
                      max="10"
                      step="2.25"
                      value={validation.human_score}
                      onChange={(e) => setValidation({ ...validation, human_score: e.target.value })}
                      disabled={submitting}
                      className="score-slider"
                      style={{
                        background: `linear-gradient(to right, 
                          ${getScoreColor(validation.human_score)} 
                          ${(validation.human_score - 1) * 11.11}%, 
                          #ddd ${(validation.human_score - 1) * 11.11}%)`
                      }}
                    />
                    <div className="score-display">
                      <div className={`validation-badge ${validation.human_score >= 6 ? 'correct' : 'incorrect'}`}
                           style={{ backgroundColor: `${getScoreColor(validation.human_score)}20`,
                                   color: getScoreColor(validation.human_score),
                                   borderColor: `${getScoreColor(validation.human_score)}40` }}>
                        {getQualitativeScore(validation.human_score)}
                      </div>
                    </div>
                  </div>
                </div>

                <div className="form-group">
                  <label htmlFor="human_feedback">Feedback (opzionale):</label>
                  <textarea
                    id="human_feedback"
                    value={validation.human_feedback}
                    onChange={(e) => setValidation({ ...validation, human_feedback: e.target.value })}
                    placeholder="Aggiungi un commento sulla risposta..."
                    rows="3"
                    disabled={submitting}
                  />
                </div>
              </div>
            </div>
          </div>

          {currentAnswer.llm_answer && (
            <div className="llm-answer-section">
              <h3>Risposta 2:</h3>
              <div className="answer-content">
                <div
                  dangerouslySetInnerHTML={{
                    __html: formatLLMText(currentAnswer.llm_answer.text),
                  }}
                />
              </div>
              {/* Validazione risposta IA */}
              <div className="validation-form">
                <div className="validation-section">
                  <h3>Validazione</h3>
                  <div className="form-group">
                    <label htmlFor="llm_score">Valutazione:</label>
                    <div className="score-slider-container">
                      <input
                        type="range"
                        id="llm_score"
                        min="1"
                        max="10"
                        step="2.25"
                        value={validation.llm_score}
                        onChange={(e) => setValidation({ ...validation, llm_score: e.target.value })}
                        disabled={submitting}
                        className="score-slider"
                        style={{
                          background: `linear-gradient(to right, 
                            ${getScoreColor(validation.llm_score)} 
                            ${(validation.llm_score - 1) * 11.11}%, 
                            #ddd ${(validation.llm_score - 1) * 11.11}%)`
                        }}
                      />
                      <div className="score-display">
                        <div className={`validation-badge ${validation.llm_score >= 6 ? 'correct' : 'incorrect'}`}
                             style={{ backgroundColor: `${getScoreColor(validation.llm_score)}20`,
                                     color: getScoreColor(validation.llm_score),
                                     borderColor: `${getScoreColor(validation.llm_score)}40` }}>
                          {getQualitativeScore(validation.llm_score)}
                        </div>
                      </div>
                    </div>
                  </div>

                  <div className="form-group">
                    <label htmlFor="llm_feedback">Feedback (opzionale):</label>
                    <textarea
                      id="llm_feedback"
                      value={validation.llm_feedback}
                      onChange={(e) => setValidation({ ...validation, llm_feedback: e.target.value })}
                      placeholder="Aggiungi un commento sulla risposta..."
                      rows="3"
                      disabled={submitting}
                    />
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
        <form onSubmit={handleSubmit} className="validation-form">
          <div className="form-actions">
            <button type="button" onClick={handleSkip} className="btn btn-outline" disabled={submitting}>
              Salta
            </button>
            <button type="submit" className="btn btn-primary" disabled={submitting}>
              {validationStep === 'submitting' ? "Invio validazione..." : 
               validationStep === 'llm_validating' ? "Validazione IA in corso..." :
               "Invia Validazioni"}
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

      <style jsx>{`
        .llm-validation-dialog {
          position: fixed;
          top: 0;
          left: 0;
          right: 0;
          bottom: 0;
          background-color: rgba(0, 0, 0, 0.5);
          display: flex;
          justify-content: center;
          align-items: center;
          z-index: 1000;
        }

        .llm-validation-content {
          background-color: white;
          padding: 2rem;
          border-radius: 8px;
          box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
          max-width: 600px;
          width: 90%;
          max-height: 90vh;
          overflow-y: auto;
          position: relative;
        }

        .close-button {
          position: absolute;
          top: 1rem;
          right: 1rem;
          background: none;
          border: none;
          font-size: 1.5rem;
          cursor: pointer;
          color: #666;
          padding: 0.5rem;
          line-height: 1;
        }

        .close-button:hover {
          color: #000;
        }

        .validation-section {
          margin-bottom: 1.5rem;
          padding: 1rem;
          border-radius: 4px;
          background-color: #f8f9fa;
        }

        .validation-section h4 {
          margin-top: 0;
          color: #333;
        }

        .validation-score {
          margin: 1rem 0;
        }

        .score-value {
          font-weight: bold;
          padding: 0.25rem 0.5rem;
          border-radius: 4px;
        }

        .score-value.correct {
          background-color: #e8f5e9;
          color: #2e7d32;
        }

        .score-value.incorrect {
          background-color: #ffebee;
          color: #c62828;
        }

        .feedback-text {
          margin: 0.5rem 0;
          line-height: 1.5;
        }
      `}</style>
    </div>
  )
}

export default ValidateAnswers
