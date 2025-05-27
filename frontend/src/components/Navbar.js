"use client"
import { Link, useNavigate } from "react-router-dom"
import { useAuth } from "../contexts/AuthContext"

function Navbar() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()

  const handleLogout = () => {
    logout()
    navigate("/login")
  }

  return (
    <nav className="navbar">
      <div className="nav-container">
        <Link to="/" className="nav-logo">
          🇮🇹 CulturaLLM
        </Link>

        {user && (
          <div className="nav-menu">
            <Link to="/" className="nav-link">
              Dashboard
            </Link>
            <Link to="/create-question" className="nav-link">
              Crea Domanda
            </Link>
            <Link to="/answer-question" className="nav-link">
              Rispondi
            </Link>
            <Link to="/validate-answers" className="nav-link">
              Valida
            </Link>
            <Link to="/leaderboard" className="nav-link">
              Classifica
            </Link>

            <div className="nav-user">
              <span className="user-info">
                {user.username} ({user.score} punti)
              </span>
              <button onClick={handleLogout} className="logout-btn">
                Logout
              </button>
            </div>
          </div>
        )}
      </div>
    </nav>
  )
}

export default Navbar
