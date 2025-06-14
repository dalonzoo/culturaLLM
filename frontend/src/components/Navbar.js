"use client"
import { Link, useNavigate } from "react-router-dom"
import { useAuth } from "../contexts/AuthContext"
import React from "react"

function Navbar() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  const [showMenu, setShowMenu] = React.useState(false)
  const [mobileMenuOpen, setMobileMenuOpen] = React.useState(false)

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
        <button className="nav-hamburger" onClick={() => setMobileMenuOpen(!mobileMenuOpen)} aria-label="Apri menu">
          <span className="hamburger-bar"></span>
          <span className="hamburger-bar"></span>
          <span className="hamburger-bar"></span>
        </button>
        {user && (
          <div className={`nav-menu${mobileMenuOpen ? " open" : ""}`}>
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
            <Link to="/validated-tags" className="nav-link">
              Archivio Punteggi
            </Link>
            <Link to="/leaderboard" className="nav-link">
              Classifica
            </Link>

            <div className="nav-user">
              <span className="user-info" onClick={() => setShowMenu(!showMenu)} style={{ cursor: 'pointer', position: 'relative' }}>
                {user.username} ({user.score} punti)
                {showMenu && (
                  <div className="user-menu">
                    <button onClick={handleLogout} className="logout-btn">Logout</button>
                  </div>
                )}
              </span>
            </div>
          </div>
        )}
      </div>
      <style>{`
        .navbar .nav-link {
          padding: 0.5em 1.4em;
          font-size: 1.2vw;
          white-space: nowrap;
          display: inline-block;
        }
        .nav-hamburger {
          display: none;
          flex-direction: column;
          justify-content: center;
          align-items: center;
          width: 40px;
          height: 40px;
          background: none;
          border: none;
          cursor: pointer;
          margin-left: auto;
          z-index: 20;
        }
        .hamburger-bar {
          width: 28px;
          height: 3px;
          background: white;
          margin: 3px 0;
          border-radius: 2px;
          transition: 0.3s;
        }
        @media (max-width: 900px) {
          .nav-menu {
            gap: 1rem;
          }
        }
        @media (max-width: 768px) {
          .nav-container {
            flex-direction: row;
            gap: 0;
            padding-right: 10px;
            margin: 0 5px;
          }
          .nav-logo {
            min-width: unset;
            font-size: 1.2rem;
          }
          .nav-hamburger {
            display: flex;
          }
          .nav-menu {
            position: absolute;
            top: 60px;
            left: 0;
            right: 0;
            background: linear-gradient(135deg, #822433, #6d1e2a);
            flex-direction: column;
            align-items: flex-start;
            gap: 0;
            padding: 1rem 0.5rem;
            z-index: 15;
            display: none;
            box-shadow: 0 4px 16px #0002;
          }
          .nav-menu.open {
            display: flex;
          }
          .nav-link {
            width: 100%;
            padding: 1rem 0.5rem;
            font-size: 1.1em;
            border-radius: 0;
            text-align: left;
          }
          .nav-user {
            width: 100%;
            justify-content: flex-start;
            margin-top: 0.5rem;
          }
          .user-info {
            width: 100%;
            justify-content: flex-start;
          }
        }
        .user-menu {
          position: absolute;
          top: 100%;
          left: 0;
          background: white;
          color: #822433;
          border: 1px solid #ddd;
          border-radius: 6px;
          box-shadow: 0 2px 8px rgba(0,0,0,0.08);
          min-width: 120px;
          z-index: 10;
        }
        .user-menu .logout-btn {
          width: 100%;
          background: none;
          color: #822433;
          border: none;
          padding: 0.7em 1em;
          text-align: left;
          cursor: pointer;
        }
        .user-menu .logout-btn:hover {
          background: #f5f5f5;
        }
      `}</style>
    </nav>
  )
}

export default Navbar
