"use client"

import { useState, useEffect } from "react"
import { Link } from "react-router-dom"
import { useAuth } from "../contexts/AuthContext"
import api from "../services/api"

function Dashboard() {
  const { user } = useAuth()
  const [stats, setStats] = useState({
    pendingQuestions: 0,
    pendingValidations: 0,
    recentActivity: [],
  })
  const [randomTheme, setRandomTheme] = useState(null)

  useEffect(() => {
    fetchDashboardData()
    fetchRandomTheme()
  }, [])

  const fetchDashboardData = async () => {
    try {
      // This would be implemented with proper endpoints
      setStats({
        pendingQuestions: 5,
        pendingValidations: 3,
        recentActivity: [],
      })
    } catch (error) {
      console.error("Error fetching dashboard data:", error)
    }
  }

  const fetchRandomTheme = async () => {
    try {
      const response = await api.get("/api/questions/random-theme")
      setRandomTheme(response.data)
    } catch (error) {
      console.error("Error fetching random theme:", error)
    }
  }

  const formatBadges = (badgesString) => {
    if (!badgesString) return []
    return badgesString.split(",").filter((badge) => badge.trim())
  }

  return (
    <div className="dashboard">
      <div className="dashboard-header">
        <h1>
          <img src="/icons/italy.png" alt="Bandiera italiana" className="italy-flag-icon" />
          Benvenuto, {user.username}!
        </h1>
        <div className="user-stats">
          <div className="stat-card">
            <h3>Punteggio</h3>
            <p className="stat-value">{user.score}</p>
          </div>
          <div className="stat-card">
            <h3>Badge</h3>
            <div className="badges">
              {formatBadges(user.badges).map((badge, index) => (
                <span key={index} className="badge">
                  {badge}
                </span>
              ))}
              {formatBadges(user.badges).length === 0 && <span className="no-badges">Nessun badge ancora</span>}
            </div>
          </div>
        </div>
      </div>

      <div className="dashboard-content">
        <div className="action-cards">
          <div className="action-card">
            <h3>🎯 Tema Suggerito</h3>
            {randomTheme && (
              <div>
                <h4>{randomTheme.name}</h4>
                <p>{randomTheme.description}</p>
              </div>
            )}
            <Link to="/create-question" className="btn btn-primary">
              Crea una Domanda
            </Link>
          </div>

          <div className="action-card">
            <h3>💬 Rispondi alle Domande</h3>
            <p>Ci sono {stats.pendingQuestions} domande che aspettano una risposta</p>
            <Link to="/answer-question" className="btn btn-secondary">
              Inizia a Rispondere
            </Link>
          </div>

          <div className="action-card">
            <h3>✅ Valida le Risposte</h3>
            <p>Ci sono {stats.pendingValidations} risposte da validare</p>
            <Link to="/validate-answers" className="btn btn-accent">
              Inizia a Validare
            </Link>
          </div>

          <div className="action-card">
            <h3>🏆 Classifica</h3>
            <p>Vedi come ti posizioni rispetto agli altri utenti</p>
            <Link to="/leaderboard" className="btn btn-outline">
              Vedi Classifica
            </Link>
          </div>
        </div>

        <div className="game-flow">
          <h2>Come Funziona il Gioco</h2>
          <div className="flow-steps">
            <div className="flow-step">
              <div className="step-number">1</div>
              <h4>Crea una Domanda</h4>
              <p>Scegli un tema culturale e crea una domanda specifica sulla cultura italiana</p>
            </div>
            <div className="flow-step">
              <div className="step-number">2</div>
              <h4>Rispondi alle Domande</h4>
              <p>Rispondi alle domande di altri utenti. L'IA risponderà anche lei!</p>
            </div>
            <div className="flow-step">
              <div className="step-number">3</div>
              <h4>Valida le Risposte</h4>
              <p>Confronta le risposte umane con quelle dell'IA e assegna punteggi</p>
            </div>
            <div className="flow-step">
              <div className="step-number">4</div>
              <h4>Guadagna Punti</h4>
              <p>Accumula punti e badge per scalare la classifica!</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default Dashboard
