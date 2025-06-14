"use client"
import { BrowserRouter as Router, Routes, Route, Navigate } from "react-router-dom"
import { AuthProvider, useAuth } from "./contexts/AuthContext"
import Navbar from "./components/Navbar"
import Login from "./components/Login"
import Register from "./components/Register"
import Dashboard from "./components/Dashboard"
import CreateQuestion from "./components/CreateQuestion"
import AnswerQuestion from "./components/AnswerQuestion"
import ValidateAnswers from "./components/ValidateAnswers"
import Leaderboard from "./components/Leaderboard"
import ValidatedTags from "./components/ValidatedTags"
import "./App.css"

function ProtectedRoute({ children }) {
  const { user } = useAuth()
  return user ? children : <Navigate to="/login" />
}

function App() {
  return (
    <AuthProvider>
      <Router>
        <div className="App">
          <Navbar />
          <main className="main-content">
            <Routes>
              <Route path="/login" element={<Login />} />
              <Route path="/register" element={<Register />} />
              <Route
                path="/"
                element={
                  <ProtectedRoute>
                    <Dashboard />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/create-question"
                element={
                  <ProtectedRoute>
                    <CreateQuestion />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/answer-question"
                element={
                  <ProtectedRoute>
                    <AnswerQuestion />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/validate-answers"
                element={
                  <ProtectedRoute>
                    <ValidateAnswers />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/leaderboard"
                element={
                  <ProtectedRoute>
                    <Leaderboard />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/validated-tags"
                element={
                  <ProtectedRoute>
                    <ValidatedTags />
                  </ProtectedRoute>
                }
              />
            </Routes>
          </main>
        </div>
      </Router>
    </AuthProvider>
  )
}

export default App
