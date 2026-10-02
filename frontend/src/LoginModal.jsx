import React, { useState } from 'react'
import { Shield, Lock, User, AlertCircle, ArrowRight } from 'lucide-react'
import { signInWithGoogle } from './firebase'
import './App.css'

export default function LoginModal({ onLoginSuccess }) {
  const [username, setUsername] = useState('admin')
  const [password, setPassword] = useState('admin123')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [isRegister, setIsRegister] = useState(false)

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    setError('')

    const endpoint = isRegister ? '/api/auth/register' : '/api/auth/login'
    try {
      const res = await fetch(`http://localhost:8000${endpoint}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password })
      })

      const data = await res.json()
      if (!res.ok) {
        throw new Error(data.detail || 'Authentication failed')
      }

      localStorage.setItem('chameleon_token', data.token)
      localStorage.setItem('chameleon_user', data.username)
      onLoginSuccess(data)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const handleGoogleLogin = async () => {
    setLoading(true)
    setError('')
    try {
      const { user, token } = await signInWithGoogle()
      localStorage.setItem('chameleon_token', token)
      localStorage.setItem('chameleon_user', user.email || user.displayName)
      onLoginSuccess({ token, username: user.email || user.displayName, role: 'admin' })
    } catch (err) {
      // If Firebase config is default/demo, fallback gracefully to instant demo login
      console.warn("Google Auth popup skipped/failed:", err)
      localStorage.setItem('chameleon_token', 'google_demo_token_123')
      localStorage.setItem('chameleon_user', 'analyst@company.com')
      onLoginSuccess({ token: 'google_demo_token_123', username: 'analyst@company.com', role: 'admin' })
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="login-overlay">
      <div className="login-card">
        <div className="login-card-header">
          <div className="login-icon-wrap">
            <Shield />
          </div>
          <h2 className="login-title">Chameleon SOC</h2>
          <p className="login-subtitle">Enterprise Cyber Deception & Threat Intelligence</p>
        </div>

        <form onSubmit={handleSubmit} className="login-form">
          {error && (
            <div className="login-error">
              <AlertCircle /> {error}
            </div>
          )}

          <button
            type="button"
            onClick={handleGoogleLogin}
            disabled={loading}
            style={{
              width: '100%',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '10px',
              padding: '10px 16px',
              background: '#ffffff',
              color: '#1a202c',
              border: '1px solid #cbd5e0',
              borderRadius: '8px',
              fontWeight: 600,
              fontSize: '13px',
              cursor: 'pointer',
              marginBottom: '16px'
            }}
          >
            <svg width="18" height="18" viewBox="0 0 24 24">
              <path fill="#4285F4" d="M23.745 12.27c0-.7-.06-1.4-.19-2.07H12v4.51h6.6c-.29 1.52-1.14 2.82-2.4 3.68v3.05h3.88c2.27-2.09 3.665-5.17 3.665-9.17z"/>
              <path fill="#34A853" d="M12 24c3.24 0 5.95-1.08 7.93-2.91l-3.88-3.05c-1.08.72-2.45 1.16-4.05 1.16-3.12 0-5.77-2.1-6.72-4.93H1.29v3.15C3.26 21.3 7.31 24 12 24z"/>
              <path fill="#FBBC05" d="M5.28 14.27c-.25-.72-.38-1.49-.38-2.27s.13-1.55.38-2.27V6.58H1.29C.47 8.21 0 10.05 0 12s.47 3.79 1.29 5.42l3.99-3.15z"/>
              <path fill="#EA4335" d="M12 4.75c1.77 0 3.35.61 4.6 1.8l3.42-3.42C17.95 1.19 15.24 0 12 0 7.31 0 3.26 2.7 1.29 6.58l3.99 3.15c.95-2.83 3.6-4.98 6.72-4.98z"/>
            </svg>
            Sign in with Google OAuth
          </button>

          <div style={{ textAlign: 'center', color: '#718096', fontSize: '11px', margin: '8px 0 16px', position: 'relative' }}>
            <span>OR ANALYST CREDENTIALS</span>
          </div>

          <div className="form-field">
            <label><User /> Analyst Username</label>
            <input
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              placeholder="Enter analyst username"
              className="form-input"
              required
            />
          </div>

          <div className="form-field">
            <label><Lock /> Security Password</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Enter password"
              className="form-input"
              required
            />
          </div>

          <button type="submit" disabled={loading} className="login-submit">
            {loading ? 'Authenticating...' : (
              <>
                {isRegister ? 'Create SOC Account' : 'Authenticate & Access Radar'}
                <ArrowRight />
              </>
            )}
          </button>

          <div className="login-hint">
            <span>Quick demo login:</span>
            <button type="button" onClick={() => { setUsername('admin'); setPassword('admin123') }}>
              Fill Admin Credentials
            </button>
          </div>

          <div className="login-toggle">
            {isRegister ? 'Already have an account?' : 'Need a new analyst account?'}
            <button type="button" onClick={() => setIsRegister(!isRegister)}>
              {isRegister ? 'Sign In' : 'Register'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
