"use client"

import { useState, useEffect } from "react"
import { useAuth } from "../contexts/AuthContext"
import api from "../services/api"

function Leaderboard() {
  const [leaderboard, setLeaderboard] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState("")
  const { user } = useAuth()

  useEffect(() => {
    fetchLeaderboard()
  }, [])

  const fetchLeaderboard = async () => {
    setLoading(true)
    try {
      const response = await api.get("/api/leaderboard/")
      setLeaderboard(response.data)
    } catch (error) {
      setError("Errore nel caricamento della classifica")
    }
    setLoading(false)
  }

  const formatBadges = (badgesString) => {
    if (!badgesString) return []
    return badgesString.split(",").filter((badge) => badge.trim())
  }

  const getRankIcon = (rank) => {
    switch (rank) {
      case 1:
        return "🥇"
      case 2:
        return "🥈"
      case 3:
        return "🥉"
      default:
        return `#${rank}`
    }
  }

  if (loading) {
    return <div className="loading">Caricamento classifica...</div>
  }

  return (
    <div className="leaderboard">
      <div className="page-header">
        <h1>Classifica 🏆</h1>
        <p>I migliori esperti di cultura italiana</p>
      </div>

      {error && <div className="error-message">{error}</div>}

      <div className="leaderboard-container">
        {leaderboard.length === 0 ? (
          <div className="no-content">
            <p>Nessun utente in classifica ancora</p>
          </div>
        ) : (
          <div className="leaderboard-list">
            {leaderboard.map((entry, index) => (
              <div
                key={entry.username}
                className={`leaderboard-item ${entry.username === user?.username ? "current-user" : ""}`}
              >
                <div className="rank">
                  <span className="rank-icon">{getRankIcon(entry.rank)}</span>
                </div>

                <div className="user-info">
                  <h3 className="username">
                    {entry.username}
                    {entry.username === user?.username && <span className="you-badge">Tu</span>}
                  </h3>
                  <div className="badges">
                    {formatBadges(entry.badges).map((badge, badgeIndex) => (
                      <span key={badgeIndex} className="badge">
                        {badge}
                      </span>
                    ))}
                  </div>
                </div>

                <div className="score">
                  <span className="score-value">{entry.score}</span>
                  <span className="score-label">punti</span>
                </div>
              </div>
            ))}
          </div>
        )}

        {user && (
          <div className="user-stats-summary">
            <h3>Le tue statistiche</h3>
            <div className="stats-grid">
              <div className="stat-item">
                <span className="stat-label">Punteggio</span>
                <span className="stat-value">{user.score}</span>
              </div>
              <div className="stat-item">
                <span className="stat-label">Posizione</span>
                <span className="stat-value">
                  {leaderboard.find((entry) => entry.username === user.username)?.rank || "N/A"}
                </span>
              </div>
              <div className="stat-item">
                <span className="stat-label">Badge</span>
                <span className="stat-value">{formatBadges(user.badges).length}</span>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

export default Leaderboard
