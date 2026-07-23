import { useState, useEffect, useRef } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Activity, ShieldAlert, Cpu, UserCheck, Terminal, Network, Shield, AlertTriangle, Fingerprint, Lock, Zap, Clock } from 'lucide-react'
import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts'
import './App.css'

function App() {
  const [sessions, setSessions] = useState({})
  const [events, setEvents] = useState([])
  const [connected, setConnected] = useState(false)
  const wsRef = useRef(null)
  const eventsEndRef = useRef(null)

  useEffect(() => {
    const connect = () => {
      const ws = new WebSocket('ws://localhost:8000/ws')
      wsRef.current = ws

      ws.onopen = () => setConnected(true)
      ws.onclose = () => {
        setConnected(false)
        setTimeout(connect, 2000)
      }

      ws.onmessage = (e) => {
        const data = JSON.parse(e.data)
        const sid = data.session_id

        // Filter out internal state updates from the visual event feed
        if (data.type !== 'SESSION_HISTORY' && data.type !== 'METRICS_UPDATE') {
          setEvents(prev => [...prev.slice(-100), { ...data, _time: new Date().toLocaleTimeString() }])
        }

        setSessions(prev => {
          const updated = { ...prev }

          if (data.type === 'SESSION_NEW') {
            updated[sid] = {
              src_ip: data.src_ip,
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
              commands: [...currentSession.commands, { text: data.command, intent: data.intent }],
              classification: data.classification,
              metrics: data.metrics
            }
          }
          
          if (data.type === 'METRICS_UPDATE') {
            if (updated[sid]) {
              updated[sid] = {
                ...updated[sid],
                classification: data.classification,
                metrics: {
                  ...updated[sid].metrics,
                  mean_iat: data.metrics.mean_iat,
                  variance_iat: data.metrics.variance_iat
                }
              }
            }
          }

          if (data.type === 'SESSION_HISTORY') {
            updated[sid] = {
              src_ip: data.src_ip,
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

  const tierLabel = (t) => {
    switch (t) {
      case 'TIER_1_BOT': return { text: 'BOT SCRIPT', cls: 'tier-bot', icon: <Cpu size={14} /> }
      case 'TIER_2_AGENT': return { text: 'AI AGENT', cls: 'tier-agent', icon: <Zap size={14} /> }
      case 'TIER_3_HUMAN': return { text: 'HUMAN', cls: 'tier-human', icon: <UserCheck size={14} /> }
      default: return { text: 'SCANNING', cls: 'tier-unknown', icon: <Activity size={14} /> }
    }
  }

  const sessionList = Object.entries(sessions)
    .sort(([, a], [, b]) => {
      // Active sessions first, then sort by timestamp descending
      if (a.closed !== b.closed) return a.closed ? 1 : -1
      const tA = a.connected_at || ''
      const tB = b.connected_at || ''
      return tB.localeCompare(tA)
    })

  const activeSessions = sessionList.filter(([, s]) => !s.closed)
  const closedSessions = sessionList.filter(([, s]) => s.closed)

  return (
    <div className="app">
      <header className="header">
        <div className="header-left">
          <div className="logo-container">
            <h1 className="logo">CHAMELEON</h1>
          </div>
        </div>
        <div className="header-right">
          <span className={`status-dot ${connected ? 'online' : 'offline'}`}></span>
          {!connected && <span className="status-text">CONNECTION LOST</span>}
        </div>
      </header>

      <div className="dashboard">
        {/* Stats Bar */}
        <div className="stats-bar">
          <motion.div initial={{ y: -20, opacity: 0 }} animate={{ y: 0, opacity: 1 }} className="stat-card">
            <div className="stat-header">
              <span className="stat-label">Active Connections</span>
              <Network size={16} color="#64748b" />
            </div>
            <div className="stat-value">{activeSessions.length}</div>
          </motion.div>
          <motion.div initial={{ y: -20, opacity: 0 }} animate={{ y: 0, opacity: 1 }} transition={{ delay: 0.1 }} className="stat-card">
            <div className="stat-header">
              <span className="stat-label">Bots Neutralized</span>
              <Cpu size={16} color="#94a3b8" />
            </div>
            <div className="stat-value">{sessionList.filter(([, s]) => s.classification === 'TIER_1_BOT').length}</div>
          </motion.div>
          <motion.div initial={{ y: -20, opacity: 0 }} animate={{ y: 0, opacity: 1 }} transition={{ delay: 0.2 }} className="stat-card accent">
            <div className="stat-header">
              <span className="stat-label">Humans Trapped</span>
              <UserCheck size={16} color="#f43f5e" />
            </div>
            <div className="stat-value">{sessionList.filter(([, s]) => s.classification === 'TIER_3_HUMAN').length}</div>
          </motion.div>
          <motion.div initial={{ y: -20, opacity: 0 }} animate={{ y: 0, opacity: 1 }} transition={{ delay: 0.3 }} className="stat-card warn">
            <div className="stat-header">
              <span className="stat-label">AI Agents Detected</span>
              <Zap size={16} color="#eab308" />
            </div>
            <div className="stat-value">{sessionList.filter(([, s]) => s.classification === 'TIER_2_AGENT').length}</div>
          </motion.div>
        </div>

        <div className="main-grid">
          {/* Sessions Panel */}
          <div className="panel sessions-panel">
            <div className="panel-header" style={{display: 'flex', justifyContent: 'space-between'}}>
              <div style={{display: 'flex', alignItems: 'center', gap: '0.75rem'}}>
                <ShieldAlert size={18} color="#0369a1" />
                <h2 className="panel-title">Threat Radar</h2>
              </div>
              <button 
                onClick={() => window.location.reload()} 
                style={{background: 'rgba(3, 105, 161, 0.1)', border: '1px solid rgba(3, 105, 161, 0.2)', color: '#0369a1', padding: '4px 12px', borderRadius: '4px', fontSize: '0.7rem', cursor: 'pointer', fontWeight: 600}}>
                REFRESH RADAR
              </button>
            </div>
            <div className="session-list">
              {sessionList.length === 0 && (
                <div className="empty-state">
                  <Activity size={48} opacity={0.2} />
                  <p>Awaiting incoming SSH attacks on Port 2222...</p>
                </div>
              )}
              <AnimatePresence>
                {sessionList.map(([sid, s]) => {
                  const tier = tierLabel(s.classification)
                  const chartData = (s.metrics?.recent_iats || []).map((val, idx) => ({ name: idx, iat: val }))
                  
                  return (
                    <motion.div 
                      key={sid} 
                      initial={{ opacity: 0, scale: 0.95 }}
                      animate={{ opacity: 1, scale: 1 }}
                      exit={{ opacity: 0, scale: 0.9 }}
                      className={`session-card ${s.closed ? 'closed' : ''}`}
                    >
                      <div className="session-header">
                        <span className="session-id">
                          <Fingerprint size={14} color="#0369a1" />
                          {sid.slice(0, 12)}
                        </span>
                        <span className={`tier-badge ${tier.cls}`}>
                          {tier.icon} {tier.text}
                        </span>
                      </div>
                      
                      <div className="session-meta">
                        <span className="meta-item"><Network size={12}/> {s.src_ip}</span>
                        <span className="meta-item"><Terminal size={12}/> {s.metrics?.num_commands || 0} cmds</span>
                        {s.connected_at && <span className="meta-item"><Clock size={12}/> {new Date(s.connected_at).toLocaleString()}</span>}
                        {s.closed 
                          ? <span className="meta-item" style={{color: '#94a3b8'}}>CLOSED</span>
                          : <span className="meta-item" style={{color: '#059669', fontWeight: 700}}>● LIVE</span>
                        }
                        {s.closed && <span className="meta-item"><Clock size={12}/> {(s.duration_ms / 1000).toFixed(1)}s</span>}
                      </div>

                      {s.metrics?.mean_iat > 0 && (
                        <div className="metrics-grid">
                          <div className="metric">
                            <span className="metric-label">Mean IAT</span>
                            <span className="metric-value">{s.metrics.mean_iat.toFixed(3)}s</span>
                          </div>
                          <div className="metric">
                            <span className="metric-label">Jitter Var</span>
                            <span className="metric-value">{s.metrics.variance_iat.toFixed(4)}</span>
                          </div>
                        </div>
                      )}

                      {/* Advanced Recharts IAT Graph */}
                      {chartData.length > 2 && (
                        <div className="chart-container">
                          <ResponsiveContainer width="100%" height="100%">
                            <AreaChart data={chartData}>
                              <defs>
                                <linearGradient id={`colorIat-${sid}`} x1="0" y1="0" x2="0" y2="1">
                                  <stop offset="5%" stopColor="#0369a1" stopOpacity={0.6}/>
                                  <stop offset="95%" stopColor="#0369a1" stopOpacity={0.05}/>
                                </linearGradient>
                              </defs>
                              <Tooltip 
                                contentStyle={{ backgroundColor: '#fff', border: '1px solid #e2e8f0', borderRadius: '6px', fontSize: '10px', boxShadow: '0 4px 12px rgba(0,0,0,0.1)' }}
                                itemStyle={{ color: '#0369a1' }}
                                formatter={(value) => [`${value.toFixed(3)}s`, 'IAT']}
                                labelFormatter={() => ''}
                              />
                              <Area type="monotone" dataKey="iat" stroke="#0369a1" strokeWidth={2} fillOpacity={1} fill={`url(#colorIat-${sid})`} />
                            </AreaChart>
                          </ResponsiveContainer>
                        </div>
                      )}

                      {s.commands.length > 0 && (
                        <div className="cmd-list">
                          {s.commands.slice(-4).map((cmd, i) => (
                            <div key={i} className="cmd-line">
                              <span className="prompt">$</span> {cmd.text || cmd}
                              {cmd.intent && cmd.intent.severity > 0 && (
                                <span style={{float: 'right', fontSize: '9px', color: '#eab308', background: 'rgba(234, 179, 8, 0.1)', padding: '1px 4px', borderRadius: '2px'}}>{cmd.intent.tactic}</span>
                              )}
                            </div>
                          ))}
                        </div>
                      )}

                      <div className={`response-mode ${s.classification === 'TIER_3_HUMAN' ? 'llm' : s.classification === 'TIER_2_AGENT' ? 'poison' : 'static'}`}>
                        {s.classification === 'TIER_3_HUMAN' ? <><Lock size={12}/> LLM DECEPTION ACTIVE</> :
                         s.classification === 'TIER_2_AGENT' ? <><AlertTriangle size={12}/> POISONED DATA INJECTED</> :
                         s.classification === 'TIER_1_BOT' ? <><Activity size={12}/> STATIC TARPIT</> :
                         <><Activity size={12}/> PROFILING KEYSTROKES...</>}
                      </div>
                    </motion.div>
                  )
                })}
              </AnimatePresence>
            </div>
          </div>

          {/* Live Feed */}
          <div className="panel feed-panel">
            <div className="panel-header">
              <Activity size={18} color="#0369a1" />
              <h2 className="panel-title">Global Event Stream</h2>
            </div>
            <div className="event-feed">
              {events.map((ev, i) => (
                <div key={i} className={`event-row event-${ev.type?.toLowerCase()}`}>
                  <span className="event-time">{ev._time}</span>
                  <span className="event-type">
                    {ev.type === 'COMMAND' && <Terminal size={14}/>}
                    {ev.type === 'SESSION_NEW' && <Network size={14}/>}
                    {ev.type === 'LOGIN_ATTEMPT' && <Lock size={14}/>}
                    {ev.type === 'SESSION_CLOSED' && <Clock size={14}/>}
                    {ev.type === 'DECEPTION_DEPLOYED' && <ShieldAlert size={14} color="#f43f5e" className="animate-pulse" />}
                    {ev.type !== 'DECEPTION_DEPLOYED' ? ev.type : 'COUNTER-MEASURE ENGAGED'}
                  </span>
                  <span className="event-detail">
                    {ev.type === 'COMMAND' && <><code>{ev.command}</code> {ev.intent && ev.intent.severity > 0 && <span style={{color: '#eab308', fontSize: '10px'}}>[{ev.intent.tactic}]</span>} <span className={tierLabel(ev.classification).cls} style={{padding: '2px 6px', fontSize: '10px'}}>{tierLabel(ev.classification).text}</span></>}
                    {ev.type === 'SESSION_NEW' && <>Connection established from {ev.src_ip}</>}
                    {ev.type === 'LOGIN_ATTEMPT' && <>{ev.success ? <UserCheck size={14} color="#10b981"/> : <AlertTriangle size={14} color="#ef4444"/>} {ev.username}:{ev.password}</>}
                    {ev.type === 'SESSION_CLOSED' && <>Session terminated ({(ev.duration_ms / 1000).toFixed(1)}s)</>}
                    {ev.type === 'DECEPTION_DEPLOYED' && <><span style={{color: '#f43f5e', fontWeight: 'bold'}}>{ev.action}</span> ➔ {ev.payload}</>}
                  </span>
                </div>
              ))}
              <div ref={eventsEndRef} />
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default App
