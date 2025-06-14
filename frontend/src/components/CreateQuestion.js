"use client"

import { useState, useEffect } from "react"
import { useNavigate } from "react-router-dom"
import api from "../services/api"

function CreateQuestion() {
  const [formData, setFormData] = useState({
    text: "",
    theme_id: "",
  })
  const [themes, setThemes] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState("")
  const [success, setSuccess] = useState("")
  const [generatingQuestion, setGeneratingQuestion] = useState(false)

  const navigate = useNavigate()

  useEffect(() => {
    fetchThemes()
  }, [])

  const fetchThemes = async () => {
    try {
      const response = await api.get("/api/questions/themes")
      setThemes(response.data)
    } catch (error) {
      setError("Errore nel caricamento dei temi")
    }
  }

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value,
    })
  }

  const generateQuestion = async () => {
    if (!formData.theme_id) {
      setError("Seleziona prima un tema")
      return
    }
    setGeneratingQuestion(true)
    setError("")
    setSuccess("")
    try {
      const response = await api.post(`/api/questions/generate/${formData.theme_id}`)
      setFormData(prev => ({
        ...prev,
        text: response.data.text
      }))
      setSuccess("Domanda generata! Puoi modificarla o rigenerarla, poi premi 'Crea Domanda' per confermare.")
    } catch (error) {
      setError(error.response?.data?.detail || "Errore nella generazione della domanda")
    }
    setGeneratingQuestion(false)
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    setError("")
    setSuccess("")

    try {
      await api.post("/api/questions/", {
        text: formData.text,
        theme_id: Number.parseInt(formData.theme_id),
      })

      setSuccess("Domanda creata con successo!")
      setTimeout(() => {
        navigate("/")
      }, 2000)
    } catch (error) {
      setError(error.response?.data?.detail || "Errore nella creazione della domanda")
    }

    setLoading(false)
  }

  return (
    <div className="create-question">
      <div className="page-header">
        <h1>Crea una Nuova Domanda 🎯</h1>
        <p>Crea una domanda culturalmente specifica sull'Italia</p>
      </div>

      <div className="form-container">
        {error && <div className="error-message">{error}</div>}
        {success && <div className="success-message">{success}</div>}

        <form onSubmit={handleSubmit} className="question-form">
          <div className="form-group">
            <label htmlFor="theme_id">Tema Culturale</label>
            <select
              id="theme_id"
              name="theme_id"
              value={formData.theme_id}
              onChange={handleChange}
              required
              disabled={loading}
            >
              <option value="">Seleziona un tema</option>
              {themes.map((theme) => (
                <option key={theme.id} value={theme.id}>
                  {theme.name}
                </option>
              ))}
            </select>
            {formData.theme_id && (
              <small className="theme-description">
                {themes.find((t) => t.id === Number.parseInt(formData.theme_id))?.description}
              </small>
            )}
          </div>

          <div className="form-group">
            <label htmlFor="text">Testo della Domanda</label>
            <div className="question-input-container">
              <textarea
                id="text"
                name="text"
                value={formData.text}
                onChange={handleChange}
                placeholder="Scrivi una domanda specifica sulla cultura italiana..."
                rows="4"
                required
                disabled={loading || generatingQuestion}
              />
              <button
                type="button"
                onClick={generateQuestion}
                className="btn btn-secondary generate-btn"
                disabled={!formData.theme_id || loading || generatingQuestion}
              >
                {generatingQuestion ? (
                  <span className="generating-text">
                    <span className="loading-dots">Generazione in corso</span>
                  </span>
                ) : (
                  <>
                    <span className="generate-icon">✨</span>
                    Genera Domanda
                  </>
                )}
              </button>
            </div>
            <small className="form-hint">
              Esempi: "Qual è il gesto italiano per dire 'delizioso'?", "Quale programma TV italiano era famoso negli
              anni '80?"
            </small>
          </div>

          <div className="form-actions">
            <button type="button" onClick={() => navigate("/")} className="btn btn-outline" disabled={loading}>
              Annulla
            </button>
            <button
              type="submit"
              className="btn btn-primary"
              disabled={loading || !formData.text || !formData.theme_id}
            >
              {loading ? "Creazione in corso..." : "Crea Domanda"}
            </button>
          </div>
        </form>

        <div className="tips">
          <h3>💡 Consigli per una buona domanda:</h3>
          <ul>
            <li>Sii specifico e culturalmente rilevante</li>
            <li>Evita domande troppo generiche o ovvie</li>
            <li>Pensa a qualcosa che solo chi conosce la cultura italiana saprebbe</li>
            <li>Considera dialetti, tradizioni locali, o riferimenti culturali specifici</li>
          </ul>
        </div>
      </div>
    </div>
  )
}

export default CreateQuestion
