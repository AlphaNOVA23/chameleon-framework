import React, { useState, useEffect, useRef } from 'react'
import { motion } from 'framer-motion'
import {
  Activity, ShieldAlert, Cpu, UserCheck, Terminal, Network, Shield,
  AlertTriangle, Fingerprint, Lock, Zap, ChevronDown, ChevronRight,
  Layers, Sliders, Download, LogOut, Sun, Moon, FileText, Trash2, Server
} from 'lucide-react'
import {
  AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer,
  BarChart, Bar, Cell, ComposedChart, Line, CartesianGrid
} from 'recharts'
import LandingPage from './LandingPage'
import LoginModal from './LoginModal'
import SettingsDrawer from './SettingsDrawer'
import SensorModal from './SensorModal'
import { API_BASE, WS_BASE } from './config'
import './App.css'

function App() {
  const [sessions, setSessions] = useState({})
  const [events, setEvents] = useState([])
  const [connected, setConnected] = useState(false)
  const [activeTab, setActiveTab] = useState(() => localStorage.getItem('chameleon_active_tab') || 'landing')
  const [expandedSession, setExpandedSession] = useState(null)

  useEffect(() => {
    localStorage.setItem('chameleon_active_tab', activeTab)
  }, [activeTab])

  // Commercial SaaS state
  const [isAuthenticated, setIsAuthenticated] = useState(() => !!localStorage.getItem('chameleon_token'))
  const [currentUser, setCurrentUser] = useState(() => localStorage.getItem('chameleon_user') || 'analyst')
  const [isSettingsOpen, setIsSettingsOpen] = useState(false)
  const [isSensorModalOpen, setIsSensorModalOpen] = useState(false)
  const [selectedSensor, setSelectedSensor] = useState('ALL')
  const [theme, setTheme] = useState(() => localStorage.getItem('chameleon_theme') || 'dark')
  const [settings, setSettings] = useState({ tau_bot: 0.25, tau_human: 1.80, delta_var: 0.08 })

  const wsRef = useRef(null)
  const eventsEndRef = useRef(null)

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme)
    localStorage.setItem('chameleon_theme', theme)
  }, [theme])

  useEffect(() => {
    fetch(`${API_BASE}/api/settings`)
      .then(res => res.json())
      .then(data => setSettings(prev => ({ ...prev, ...data })))
      .catch(() => {})
  }, [isSettingsOpen])

  useEffect(() => {
    const connect = () => {
      const ws = new WebSocket(`${WS_BASE}/ws`)
      wsRef.current = ws

      ws.onopen = () => setConnected(true)
      ws.onclose = () => {
        setConnected(false)
        setTimeout(connect, 2000)
      }

      ws.onmessage = (e) => {
        const data = JSON.parse(e.data)
        const sid = data.session_id

        if (data.type !== 'SESSION_HISTORY' && data.type !== 'METRICS_UPDATE') {
          setEvents(prev => [...prev.slice(-100), { ...data, _time: new Date().toLocaleTimeString() }])
        }

        setSessions(prev => {
          const updated = { ...prev }

          if (data.type === 'SESSION_NEW') {
            updated[sid] = {
              src_ip: data.src_ip,
              ip_intel: data.ip_intel || { flag: '🌐', country: 'Unknown', risk: 'Moderate', threat_score: 50, isp: 'Unresolved' },
              commands: [],
              classification: 'UNKNOWN',
              metrics: { mean_iat: 0, variance_iat: 0, num_commands: 0, recent_iats: [] },
              logins: [],
              connected_at: data.timestamp || new Date().toISOString(),
              closed: false,
            }
          }

          if (data.type === 'LOGIN_ATTEMPT') {
            if (!updated[sid]) updated[sid] = { src_ip: '?', commands: [], classification: 'UNKNOWN', metrics: {}, logins: [] }
            updated[sid].logins = [...(updated[sid].logins || []), { u: data.username, p: data.password, ok: data.success }]
          }

          if (data.type === 'COMMAND') {
            const currentSession = updated[sid] || { src_ip: '?', commands: [], classification: 'UNKNOWN', metrics: { mean_iat: 0, variance_iat: 0, num_commands: 0, recent_iats: [] }, logins: [], connected_at: new Date().toISOString(), closed: false }
            updated[sid] = {
              ...currentSession,
              ip_intel: data.ip_intel || currentSession.ip_intel,
              commands: [...currentSession.commands, { text: data.command, intent: data.intent }],
              classification: data.classification,
              metrics: data.metrics
            }
          }

          if (data.type === 'SESSION_HISTORY') {
            updated[sid] = {
              src_ip: data.src_ip,
              ip_intel: data.ip_intel || { flag: '🌐', country: 'Unknown', risk: 'Moderate', threat_score: 50, isp: 'Unresolved' },
              commands: data.commands,
              classification: data.classification,
              metrics: data.metrics,
              logins: [],
              closed: data.closed ?? true,
              duration_ms: data.duration_ms || 0,
              connected_at: data.connected_at || '',
            }
          }

          if (data.type === 'SESSION_CLOSED') {
            if (updated[sid]) {
              updated[sid].closed = true
              updated[sid].duration_ms = data.duration_ms
            }
          }

          return updated
        })
      }
    }

    connect()
    return () => wsRef.current?.close()
  }, [])

  useEffect(() => {
    eventsEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [events])

  const handleLogout = () => {
    localStorage.removeItem('chameleon_token')
    localStorage.removeItem('chameleon_user')
    setIsAuthenticated(false)
  }

  const handleExportCSV = () => {
    window.open(`${API_BASE}/api/reports/export?format=csv`, '_blank')
  }

  const handleExportPDF = () => {
    window.open(`${API_BASE}/api/reports/pdf`, '_blank')
  }

  // ── Derived Data ──
  const sessionList = Object.entries(sessions)
    .sort(([, a], [, b]) => {
      if (a.closed !== b.closed) return a.closed ? 1 : -1
      const tA = a.connected_at || ''
      const tB = b.connected_at || ''
      return tB.localeCompare(tA)
    })

  const activeSessions = sessionList.filter(([, s]) => !s.closed)
  const closedSessions = sessionList.filter(([, s]) => s.closed)
  const displaySessions = activeTab === 'live' ? sessionList : closedSessions

  const tierInfo = (t) => {
    switch (t) {
      case 'TIER_1_BOT': return { text: 'BOT', cls: 'tier-bot', icon: <Cpu /> }
      case 'TIER_2_AGENT': return { text: 'AI AGENT', cls: 'tier-agent', icon: <Zap /> }
      case 'TIER_3_HUMAN': return { text: 'HUMAN', cls: 'tier-human', icon: <UserCheck /> }
      default: return { text: 'SCANNING', cls: 'tier-unknown', icon: <Activity /> }
    }
  }

  const modeLabel = (classification) => {
    switch (classification) {
      case 'TIER_3_HUMAN': return { text: 'LLM DECEPTION', cls: 'mode-llm' }
      case 'TIER_2_AGENT': return { text: 'POISON INJECT', cls: 'mode-poison' }
      case 'TIER_1_BOT': return { text: 'STATIC TARPIT', cls: 'mode-tarpit' }
      default: return { text: 'PROFILING...', cls: 'mode-profiling' }
    }
  }

  const riskClass = (risk) => {
    if (!risk) return 'risk-low'
    if (risk.includes('High')) return 'risk-high'
    if (risk.includes('Mod')) return 'risk-mod'
    return 'risk-low'
  }

  // ── Chart Data ──
  const biometricsData = sessionList
    .map(([sid, s]) => ({
      sid: sid.slice(0, 8),
      mean_iat: parseFloat((s.metrics?.mean_iat || 0).toFixed(3)),
      variance: parseFloat((s.metrics?.variance_iat || 0).toFixed(4)),
      classification: s.classification,
    }))
    .filter(d => d.mean_iat > 0)

  const barColor = (cls) => {
    if (cls === 'TIER_1_BOT') return '#4fd1c5'
    if (cls === 'TIER_2_AGENT') return '#ecc94b'
    if (cls === 'TIER_3_HUMAN') return '#fc8181'
    return '#a0aec0'
  }

  const handleDeleteSession = async (sid, e) => {
    if (e) e.stopPropagation()
    try {
      await fetch(`${API_BASE}/api/sessions/${sid}`, { method: 'DELETE' })
      setSessions(prev => {
        const next = { ...prev }
        delete next[sid]
        return next
      })
      if (expandedSession === sid) setExpandedSession(null)
    } catch (err) {
      console.error("Delete session failed:", err)
    }
  }

  const handleClearAllSessions = async () => {
    if (!window.confirm("Are you sure you want to clear all session history?")) return
    try {
      await fetch(`${API_BASE}/api/sessions/clear`, { method: 'POST' })
      setSessions({})
      setExpandedSession(null)
    } catch (err) {
      console.error("Clear sessions failed:", err)
    }
  }

  return (
    <div className="app-shell">
      {/* ── Login Gate ── */}
      {!isAuthenticated && (
        <LoginModal
          onLoginSuccess={(data) => {
            setIsAuthenticated(true)
            setCurrentUser(data.username)
            setActiveTab('live')
          }}
        />
      )}

      {/* ── Settings Drawer ── */}
      <SettingsDrawer
        isOpen={isSettingsOpen}
        onClose={() => setIsSettingsOpen(false)}
      />

      {/* ── Sensor Deployment Modal ── */}
      <SensorModal
        isOpen={isSensorModalOpen}
        onClose={() => setIsSensorModalOpen(false)}
      />

      {/* ═══════════ HEADER ═══════════ */}
      <header className="app-header">
        <div className="header-left">
          <div className="brand">
            <h1 className="brand-name">Chameleon</h1>
            <span className="brand-tag">SOC</span>
          </div>

          <nav className="nav-pills">
            <button
              className={`nav-pill ${activeTab === 'landing' ? 'active' : ''}`}
              onClick={() => { setActiveTab('landing'); setExpandedSession(null) }}
            >
              <Layers /> Overview
            </button>
            <button
              className={`nav-pill ${activeTab === 'live' ? 'active' : ''}`}
              onClick={() => { setActiveTab('live'); setExpandedSession(null) }}
            >
              <Activity /> Threat Radar
            </button>
            <button
              className={`nav-pill ${activeTab === 'archive' ? 'active' : ''}`}
              onClick={() => { setActiveTab('archive'); setExpandedSession(null) }}
            >
              <Shield /> Forensics Archive
            </button>
          </nav>
        </div>

        <div className="header-right">
          <button
            className="header-btn"
            style={{ background: 'rgba(124, 58, 237, 0.15)', color: '#c4b5fd', border: '1px solid rgba(124, 58, 237, 0.3)', fontWeight: 600 }}
            onClick={() => setIsSensorModalOpen(true)}
          >
            <Server size={14} /> + Deploy Sensor
          </button>

          <select
            className="header-select"
            value={selectedSensor}
            onChange={(e) => setSelectedSensor(e.target.value)}
          >
            <option value="ALL">All Sensors (3 Active)</option>
            <option value="sensor-01">AWS-US-East-Sensor</option>
            <option value="sensor-02">Azure-EU-West-Canary</option>
            <option value="sensor-03">Internal-DMZ-Trap</option>
          </select>

          <button
            className="header-btn"
            onClick={() => setTheme(prev => prev === 'dark' ? 'light' : 'dark')}
            title="Toggle Light / Dark Mode"
          >
            {theme === 'dark' ? <Sun /> : <Moon />} {theme === 'dark' ? 'Light Mode' : 'Dark Mode'}
          </button>

          <button className="header-btn" onClick={() => setIsSettingsOpen(true)}>
            <Sliders /> Settings
          </button>

          <button className="header-btn" onClick={handleExportCSV}>
            <Download /> CSV
          </button>

          <button className="header-btn header-btn-primary" onClick={handleExportPDF}>
            <FileText /> Report PDF
          </button>

          <div className="user-chip">
            <UserCheck size={14} />
            <span className="user-email-text">{currentUser}</span>
            {isAuthenticated && (
              <button className="logout-btn" onClick={handleLogout} title="Log Out">
                <LogOut size={12} />
              </button>
            )}
            <div className="user-chip-tooltip">
              Logged in: <strong>{currentUser}</strong>
            </div>
          </div>
        </div>
      </header>

      {/* ═══════════ CONTENT ═══════════ */}
      {activeTab === 'landing' ? (
        <LandingPage onLaunch={setActiveTab} />
      ) : (
        <main className="dashboard">
          {/* ── Stats Row ── */}
          <div className="stats-row">
            <motion.div className="stat-card accent-violet" initial={{ y: -8, opacity: 0 }} animate={{ y: 0, opacity: 1 }}>
              <div className="stat-card-head">
                <span className="stat-label">Active Connections</span>
                <Network />
              </div>
              <span className="stat-value">{activeSessions.length}</span>
            </motion.div>

            <motion.div className="stat-card accent-cyan" initial={{ y: -8, opacity: 0 }} animate={{ y: 0, opacity: 1 }} transition={{ delay: 0.06 }}>
              <div className="stat-card-head">
                <span className="stat-label">Bots Neutralized</span>
                <Cpu />
              </div>
              <span className="stat-value">{sessionList.filter(([, s]) => s.classification === 'TIER_1_BOT').length}</span>
            </motion.div>

            <motion.div className="stat-card accent-rose" initial={{ y: -8, opacity: 0 }} animate={{ y: 0, opacity: 1 }} transition={{ delay: 0.12 }}>
              <div className="stat-card-head">
                <span className="stat-label">Humans Trapped</span>
                <UserCheck />
              </div>
              <span className="stat-value">{sessionList.filter(([, s]) => s.classification === 'TIER_3_HUMAN').length}</span>
            </motion.div>

            <motion.div className="stat-card accent-amber" initial={{ y: -8, opacity: 0 }} animate={{ y: 0, opacity: 1 }} transition={{ delay: 0.18 }}>
              <div className="stat-card-head">
                <span className="stat-label">AI Agents Detected</span>
                <Zap />
              </div>
              <span className="stat-value">{sessionList.filter(([, s]) => s.classification === 'TIER_2_AGENT').length}</span>
            </motion.div>
          </div>

          {/* ── Biometrics Chart ── */}
          <div className="chart-section">
            <div className="chart-header">
              <div className="chart-title-group">
                <Activity />
                <h2 className="chart-title">Real-Time Behavioral Biometrics — Mean IAT vs Jitter Variance</h2>
              </div>
              <div className="chart-legend">
                <span className="legend-item bot"><span className="legend-dot" /> Bot (&lt;{settings.tau_bot || 0.25}s)</span>
                <span className="legend-item agent"><span className="legend-dot" /> AI Agent ({settings.tau_bot || 0.25}–{settings.tau_human || 1.80}s)</span>
                <span className="legend-item human"><span className="legend-dot" /> Human (&gt;{settings.tau_human || 1.80}s)</span>
              </div>
            </div>
            <div className="chart-area">
              <ResponsiveContainer width="100%" height="100%">
                <ComposedChart data={biometricsData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" />
                  <XAxis dataKey="sid" tick={{ fontSize: 10, fill: '#718096' }} axisLine={false} tickLine={false} />
                  <YAxis yAxisId="left" tick={{ fontSize: 10, fill: '#718096' }} unit="s" width={36} axisLine={false} tickLine={false} />
                  <YAxis yAxisId="right" orientation="right" tick={{ fontSize: 10, fill: '#718096' }} width={36} axisLine={false} tickLine={false} />
                  <Tooltip
                    contentStyle={{
                      background: '#111827',
                      border: '1px solid rgba(255,255,255,0.08)',
                      borderRadius: '8px',
                      fontSize: '11px',
                      color: '#f0f4f8',
                      boxShadow: '0 8px 24px rgba(0,0,0,0.4)',
                    }}
                    itemStyle={{ color: '#e2e8f0' }}
                    labelStyle={{ color: '#a0aec0', fontWeight: 600 }}
                  />
                  <Bar yAxisId="left" dataKey="mean_iat" name="Mean IAT (sec)" radius={[4, 4, 0, 0]}>
                    {biometricsData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={barColor(entry.classification)} />
                    ))}
                  </Bar>
                  <Line yAxisId="right" type="monotone" dataKey="variance" name="Jitter Variance (s²)" stroke="#b794f4" strokeWidth={2} dot={{ r: 3, fill: '#b794f4' }} />
                </ComposedChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* ── Main Grid: Sessions + Events ── */}
          <div className="main-grid">
            {/* Sessions Panel */}
            <div className="panel">
              <div className="panel-header">
                <div className="panel-title-group">
                  <ShieldAlert />
                  <h2 className="panel-title">{activeTab === 'live' ? 'Live Threat Radar' : 'Forensics Archive'}</h2>
                  <span className="panel-count">{displaySessions.length}</span>
                </div>
                <div style={{ display: 'flex', gap: '8px' }}>
                  <button className="refresh-btn" style={{ background: 'rgba(239, 68, 68, 0.1)', color: '#f87171', border: '1px solid rgba(239, 68, 68, 0.2)', display: 'flex', alignItems: 'center', gap: '4px' }} onClick={handleClearAllSessions}>
                    <Trash2 size={12} /> CLEAR
                  </button>
                  <button className="refresh-btn" onClick={() => window.location.reload()}>REFRESH</button>
                </div>
              </div>

              <div style={{ overflowX: 'auto' }}>
                <table className="session-table">
                  <thead>
                    <tr>
                      <th className="col-chevron"></th>
                      <th className="col-status">Status</th>
                      <th className="col-id">Session ID</th>
                      <th className="col-source">Source Telemetry</th>
                      <th className="col-class">Classification</th>
                      <th className="col-cmds center">Cmds</th>
                      <th className="col-iat">Mean IAT</th>
                      <th className="col-mode">Response Mode</th>
                      <th style={{ width: '30px' }}></th>
                    </tr>
                  </thead>
                  <tbody>
                    {displaySessions.length === 0 && (
                      <tr>
                        <td colSpan="8">
                          <div className="empty-state">
                            <Activity />
                            <span className="empty-state-text">
                              {activeTab === 'live' ? 'Awaiting incoming SSH attacks...' : 'No archived sessions.'}
                            </span>
                          </div>
                        </td>
                      </tr>
                    )}

                    {displaySessions.map(([sid, s]) => {
                      const tier = tierInfo(s.classification)
                      const mode = modeLabel(s.classification)
                      const isExpanded = expandedSession === sid
                      const intel = s.ip_intel || { flag: '🌐', country: 'Unknown', risk: 'Moderate', threat_score: 50, isp: 'Unresolved' }
                      const chartData = (s.metrics?.recent_iats || []).map((val, idx) => ({ name: `Cmd ${idx + 1}`, iat: val }))

                      return (
                        <React.Fragment key={sid}>
                          {/* Session Row */}
                          <tr onClick={() => setExpandedSession(prev => prev === sid ? null : sid)}>
                            <td>
                              <div className="chevron-cell">
                                {isExpanded ? <ChevronDown /> : <ChevronRight />}
                              </div>
                            </td>
                            <td>
                              {s.closed
                                ? <span className="badge badge-closed">CLOSED</span>
                                : <span className="badge badge-live">LIVE</span>
                              }
                            </td>
                            <td>
                              <div className="session-id-cell">
                                <Fingerprint />
                                <span className="session-id-text">{sid.slice(0, 10)}</span>
                              </div>
                            </td>
                            <td>
                              <div className="source-cell">
                                <span className="source-flag">{intel.flag}</span>
                                <span className="source-ip">{s.src_ip}</span>
                                <span className={`risk-badge ${riskClass(intel.risk)}`}>{intel.risk}</span>
                              </div>
                            </td>
                            <td>
                              <span className={`tier-badge ${tier.cls}`}>
                                {tier.icon} {tier.text}
                              </span>
                            </td>
                            <td className="center">
                              <span className="cmds-cell">{s.metrics?.num_commands || s.commands?.length || 0}</span>
                            </td>
                            <td>
                              <span className="iat-cell">
                                {s.metrics?.mean_iat > 0 ? `${s.metrics.mean_iat.toFixed(3)}s` : '—'}
                              </span>
                            </td>
                            <td>
                              <span className={`mode-badge ${mode.cls}`}>{mode.text}</span>
                            </td>
                            <td onClick={(e) => handleDeleteSession(sid, e)} title="Delete Session">
                              <Trash2 size={13} style={{ color: '#718096', cursor: 'pointer', transition: 'color 0.2s' }} onMouseEnter={(e) => e.target.style.color = '#ef4444'} onMouseLeave={(e) => e.target.style.color = '#718096'} />
                            </td>
                          </tr>

                          {/* Expanded Detail */}
                          {isExpanded && (
                            <tr className="session-detail-row">
                              <td colSpan="9">
                                <div className="detail-inner">
                                  {/* Left Column */}
                                  <div className="detail-col">
                                    {/* Meta Grid */}
                                    <div className="detail-meta">
                                      <div className="meta-item">
                                        <span className="meta-label">Origin / ISP</span>
                                        <span className="meta-value">{intel.country} ({intel.isp})</span>
                                      </div>
                                      <div className="meta-item">
                                        <span className="meta-label">Threat Score</span>
                                        <span className="meta-value accent">{intel.threat_score}/100</span>
                                      </div>
                                      <div className="meta-item">
                                        <span className="meta-label">Mean IAT</span>
                                        <span className="meta-value accent">{s.metrics?.mean_iat > 0 ? `${s.metrics.mean_iat.toFixed(4)}s` : '—'}</span>
                                      </div>
                                      <div className="meta-item">
                                        <span className="meta-label">Jitter Var</span>
                                        <span className="meta-value accent">{s.metrics?.variance_iat > 0 ? s.metrics.variance_iat.toFixed(5) : '—'}</span>
                                      </div>
                                    </div>

                                    {/* Terminal */}
                                    {s.commands.length > 0 && (
                                      <div className="terminal-block">
                                        <div className="terminal-toolbar">
                                          <Terminal /> Command History ({s.commands.length})
                                        </div>
                                        <div className="terminal-body">
                                          {s.commands.map((cmd, i) => (
                                            <div key={i} className="terminal-line">
                                              <span className="terminal-prompt">$</span>
                                              <span className="terminal-cmd">{cmd.text || cmd}</span>
                                              {cmd.intent && cmd.intent.severity > 0 && (
                                                <span className="terminal-tag">{cmd.intent.tactic}</span>
                                              )}
                                            </div>
                                          ))}
                                        </div>
                                      </div>
                                    )}
                                  </div>

                                  {/* Right Column */}
                                  <div className="detail-col">
                                    {/* IAT Chart */}
                                    {chartData.length > 1 && (
                                      <div className="detail-chart-block">
                                        <div className="detail-chart-title">Inter-Command Arrival Time Sequence</div>
                                        <div className="detail-chart-area">
                                          <ResponsiveContainer width="100%" height="100%">
                                            <AreaChart data={chartData}>
                                              <defs>
                                                <linearGradient id={`grad-${sid}`} x1="0" y1="0" x2="0" y2="1">
                                                  <stop offset="5%" stopColor="#63b3ed" stopOpacity={0.4} />
                                                  <stop offset="95%" stopColor="#63b3ed" stopOpacity={0.02} />
                                                </linearGradient>
                                              </defs>
                                              <XAxis dataKey="name" tick={{ fontSize: 9, fill: '#4a5568' }} axisLine={false} tickLine={false} />
                                              <YAxis tick={{ fontSize: 9, fill: '#4a5568' }} axisLine={false} tickLine={false} unit="s" width={30} />
                                              <Tooltip
                                                contentStyle={{
                                                  background: '#111827',
                                                  border: '1px solid rgba(255,255,255,0.08)',
                                                  borderRadius: 6,
                                                  fontSize: 10,
                                                  color: '#f0f4f8'
                                                }}
                                              />
                                              <Area type="monotone" dataKey="iat" stroke="#63b3ed" strokeWidth={2} fill={`url(#grad-${sid})`} dot={{ r: 2, fill: '#63b3ed' }} />
                                            </AreaChart>
                                          </ResponsiveContainer>
                                        </div>
                                      </div>
                                    )}

                                    {/* Response Indicator */}
                                    <div className={`response-indicator ${
                                      s.classification === 'TIER_3_HUMAN' ? 'ri-human' :
                                      s.classification === 'TIER_2_AGENT' ? 'ri-agent' : 'ri-bot'
                                    }`}>
                                      {s.classification === 'TIER_3_HUMAN' && <><Lock /> LLM DECEPTION ACTIVE — Dynamic honeytokens hallucinated for human adversary</>}
                                      {s.classification === 'TIER_2_AGENT' && <><AlertTriangle /> AGENT POISONING — Prompt injection payloads deployed to corrupt LLM context</>}
                                      {s.classification === 'TIER_1_BOT' && <><Cpu /> STATIC TARPIT — Low-cost default Cowrie responses served</>}
                                      {!['TIER_1_BOT', 'TIER_2_AGENT', 'TIER_3_HUMAN'].includes(s.classification) && <><Activity /> PROFILING — Collecting behavioral biometrics...</>}
                                    </div>
                                  </div>
                                </div>
                              </td>
                            </tr>
                          )}
                        </React.Fragment>
                      )
                    })}
                  </tbody>
                </table>
              </div>
            </div>

            {/* Event Stream Panel */}
            <div className="panel">
              <div className="panel-header">
                <div className="panel-title-group">
                  <Activity />
                  <h2 className="panel-title">Event Stream</h2>
                </div>
                <span className="panel-count">{events.length}</span>
              </div>

              <div className="event-stream">
                {events.map((ev, i) => (
                  <div key={i} className="event-item">
                    <span className="event-time">{ev._time}</span>
                    <span className="event-type">
                      {ev.type === 'COMMAND' ? '[CMD]' :
                       ev.type === 'SESSION_NEW' ? '[CONN]' :
                       ev.type === 'LOGIN_ATTEMPT' ? '[AUTH]' : '[EVT]'}
                    </span>
                    <div className="event-body">
                      {ev.type === 'COMMAND' && (
                        <span>
                          Executed: <code>{ev.command}</code>
                          {ev.intent && ev.intent.severity > 0 && (
                            <span className="event-tactic">[{ev.intent.tactic}]</span>
                          )}
                        </span>
                      )}
                      {ev.type === 'SESSION_NEW' && (
                        <span>
                          New connection from <code>{ev.src_ip}</code> {ev.ip_intel?.flag} ({ev.ip_intel?.country})
                        </span>
                      )}
                      {ev.type === 'LOGIN_ATTEMPT' && (
                        <span>
                          Auth attempt: <code>{ev.username}:{ev.password}</code> {ev.success ? '✓' : '✗'}
                        </span>
                      )}
                      {ev.type === 'DECEPTION_DEPLOYED' && (
                        <span className="event-deception">{ev.action}: {ev.payload}</span>
                      )}
                    </div>
                  </div>
                ))}
                <div ref={eventsEndRef} />
              </div>
            </div>
          </div>
        </main>
      )}
    </div>
  )
}

export default App
