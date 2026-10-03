import React, { useState, useEffect } from 'react'
import { X, Key, Sliders, Bell, Cpu, Check, AlertCircle } from 'lucide-react'
import { API_BASE } from './config'
import './App.css'

export default function SettingsDrawer({ isOpen, onClose }) {
  const [settings, setSettings] = useState({
    tau_bot: 0.25,
    tau_human: 1.80,
    delta_var: 0.08,
    groq_api_key: '',
    webhook_url: '',
    alert_email: '',
    email_alerts_enabled: false,
    offline_fallback_enabled: true
  })
  const [saving, setSaving] = useState(false)
  const [statusMsg, setStatusMsg] = useState('')
  const [groqStatus, setGroqStatus] = useState('UNKNOWN')
  const [testingGroq, setTestingGroq] = useState(false)
  const [testResult, setTestResult] = useState(null)

  useEffect(() => {
    if (isOpen) {
      const currentUserId = localStorage.getItem('chameleon_user') || 'default_user'
      fetch(`${API_BASE}/api/settings?user_id=${encodeURIComponent(currentUserId)}`)
        .then(res => res.json())
        .then(data => {
          setSettings(prev => ({ ...prev, ...data }))
          if (data.groq_api_key && !data.groq_api_key.includes('placeholder')) {
            setGroqStatus('CONNECTED')
          } else {
            setGroqStatus('OFFLINE_FALLBACK')
          }
        })
        .catch(() => setStatusMsg('Failed to load settings from server'))
    }
  }, [isOpen])

  const handleTestGroq = async () => {
    setTestingGroq(true)
    setTestResult(null)
    try {
      const res = await fetch(`${API_BASE}/api/groq/test`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ groq_api_key: settings.groq_api_key })
      })
      const data = await res.json()
      setTestResult(data)
      if (data.success) {
        setGroqStatus('CONNECTED')
      }
    } catch (e) {
      setTestResult({ success: false, error: 'Failed to reach API server' })
    } finally {
      setTestingGroq(false)
    }
  }

  const handleSave = async () => {
    setSaving(true)
    setStatusMsg('')
    const currentUserId = localStorage.getItem('chameleon_user') || 'default_user'

    try {
      const res = await fetch(`${API_BASE}/api/settings?user_id=${encodeURIComponent(currentUserId)}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(settings)
      })
      if (res.ok) {
        setStatusMsg('Settings successfully updated!')
        if (settings.groq_api_key && !settings.groq_api_key.includes('placeholder')) {
          setGroqStatus('CONNECTED')
        } else {
          setGroqStatus('OFFLINE_FALLBACK')
        }
      } else {
        setStatusMsg('Error saving settings')
      }
    } catch (e) {
      setStatusMsg('Network error saving settings')
    } finally {
      setSaving(false)
    }
  }

  if (!isOpen) return null

  return (
    <div className="drawer-overlay" onClick={onClose}>
      <div className="drawer-panel" onClick={(e) => e.stopPropagation()}>
        {/* Header */}
        <div className="drawer-header">
          <div className="drawer-title-group">
            <Sliders />
            <h3 className="drawer-title">System Configuration</h3>
          </div>
          <button className="drawer-close" onClick={onClose}>
            <X />
          </button>
        </div>

        {/* Body */}
        <div className="drawer-body">
          {statusMsg && (
            <div className={`config-alert ${statusMsg.includes('success') ? 'success' : 'error'}`}>
              {statusMsg.includes('success') ? <Check /> : <AlertCircle />}
              {statusMsg}
            </div>
          )}

          {/* Groq LLM Config */}
          <div className="config-card">
            <div className="config-head">
              <div className="config-head-left">
                <Key />
                <h4>Generative LLM Engine (Groq Llama-3)</h4>
              </div>
              <span className={`config-status ${groqStatus === 'CONNECTED' ? 'online' : 'fallback'}`}>
                {groqStatus === 'CONNECTED' ? 'Live API' : 'Fallback'}
              </span>
            </div>
            <p className="config-desc">
              Input your Groq API key for live generative honeytokens. If unconfigured, Chameleon uses high-fidelity synthetic fallback templates.
            </p>
            <div className="config-field">
              <label>Groq API Key</label>
              <div style={{ display: 'flex', gap: '8px' }}>
                <input
                  type="password"
                  value={settings.groq_api_key || ''}
                  onChange={e => setSettings({ ...settings, groq_api_key: e.target.value })}
                  placeholder="gsk_xxxxxxxxxxxxxxxxxxxxxxxx"
                  className="config-input"
                  style={{ flex: 1 }}
                />
                <button
                  type="button"
                  className="header-btn-secondary"
                  onClick={handleTestGroq}
                  disabled={testingGroq}
                  style={{ padding: '0 12px', fontSize: '12px', whiteSpace: 'nowrap' }}
                >
                  {testingGroq ? 'Testing...' : 'Test Connection'}
                </button>
              </div>
              {testResult && (
                <div style={{ marginTop: '6px', fontSize: '11px', color: testResult.success ? '#4fd1c5' : '#fc8181' }}>
                  {testResult.success ? testResult.message : `Error: ${testResult.error}`}
                </div>
              )}
            </div>
          </div>

          {/* Biometric Thresholds */}
          <div className="config-card">
            <div className="config-head">
              <div className="config-head-left">
                <Cpu />
                <h4>Biometric Timing Thresholds</h4>
              </div>
            </div>
            <p className="config-desc">
              Adjust classification boundaries for Mean Inter-Arrival Time (μ) and Jitter Variance (σ²).
            </p>
            <div className="config-grid">
              <div className="config-field">
                <label>Bot τ (sec)</label>
                <input
                  type="number"
                  step="0.05"
                  value={settings.tau_bot}
                  onChange={e => setSettings({ ...settings, tau_bot: parseFloat(e.target.value) })}
                  className="config-input"
                />
                <span className="config-hint">&lt; 0.25s = Bot</span>
              </div>
              <div className="config-field">
                <label>Human τ (sec)</label>
                <input
                  type="number"
                  step="0.1"
                  value={settings.tau_human}
                  onChange={e => setSettings({ ...settings, tau_human: parseFloat(e.target.value) })}
                  className="config-input"
                />
                <span className="config-hint">&gt; 1.80s = Human</span>
              </div>
              <div className="config-field">
                <label>Jitter δ (s²)</label>
                <input
                  type="number"
                  step="0.01"
                  value={settings.delta_var}
                  onChange={e => setSettings({ ...settings, delta_var: parseFloat(e.target.value) })}
                  className="config-input"
                />
                <span className="config-hint">&gt; 0.08 = Burst</span>
              </div>
            </div>
          </div>

          {/* Webhook & Email Alerting */}
          <div className="config-card">
            <div className="config-head">
              <div className="config-head-left">
                <Bell />
                <h4>SIEM & Email Alerting</h4>
              </div>
            </div>
            <p className="config-desc">
              Trigger Webhook & Email alerts when Tier 3 Humans or Tier 2 AI Agents are detected.
            </p>
            <div className="config-field" style={{ marginBottom: '12px' }}>
              <label>Webhook URL Endpoint</label>
              <input
                type="url"
                value={settings.webhook_url || ''}
                onChange={e => setSettings({ ...settings, webhook_url: e.target.value })}
                placeholder="https://hooks.slack.com/services/..."
                className="config-input"
              />
            </div>
            <div className="config-field">
              <label>SOC Alert Email Address</label>
              <input
                type="email"
                value={settings.alert_email || ''}
                onChange={e => setSettings({ ...settings, alert_email: e.target.value })}
                placeholder="soc-alerts@company.com"
                className="config-input"
              />
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="drawer-footer">
          <button className="drawer-btn drawer-btn-cancel" onClick={onClose}>Cancel</button>
          <button className="drawer-btn drawer-btn-save" onClick={handleSave} disabled={saving}>
            {saving ? 'Saving...' : 'Save Configuration'}
          </button>
        </div>
      </div>
    </div>
  )
}
