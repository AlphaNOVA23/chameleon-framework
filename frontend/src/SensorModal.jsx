import React, { useState } from 'react'
import { Terminal, Copy, Check, Server, X } from 'lucide-react'
import { API_BASE } from './config'
import './App.css'

export default function SensorModal({ isOpen, onClose }) {
  const [sensorName, setSensorName] = useState('AWS-EC2-Canary-Node')
  const [copied, setCopied] = useState(false)
  const [loading, setLoading] = useState(false)
  const [sensorData, setSensorData] = useState(null)

  if (!isOpen) return null

  const currentUserId = localStorage.getItem('chameleon_user') || 'analyst@company.com'

  const handleRegister = async () => {
    setLoading(true)
    try {
      const res = await fetch(`${API_BASE}/api/sensors/register`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: sensorName, user_id: currentUserId })
      })
      const data = await res.json()
      setSensorData(data.sensor)
    } catch (err) {
      console.error("Failed to generate sensor key:", err)
    } finally {
      setLoading(false)
    }
  }

  const defaultToken = `CHAM_SENS_${currentUserId.replace(/[^a-zA-Z0-9]/g, '_')}_KEY`
  const installCommand = sensorData
    ? sensorData.install_command
    : `curl -sSL ${API_BASE}/sensor/install.sh | sudo bash -s -- --token ${defaultToken} --server ${API_BASE}`

  const copyToClipboard = () => {
    navigator.clipboard.writeText(installCommand)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  return (
    <div className="login-overlay" style={{ zIndex: 1100 }}>
      <div className="login-card" style={{ maxWidth: '620px', width: '92%' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <Server style={{ color: '#7c3aed' }} />
            <h3 style={{ margin: 0, color: '#f0f4f8', fontSize: '18px', fontWeight: 700 }}>Deploy Customer Sensor Node</h3>
          </div>
          <button onClick={onClose} style={{ background: 'none', border: 'none', color: '#a0aec0', cursor: 'pointer' }}>
            <X size={20} />
          </button>
        </div>

        <p style={{ color: '#a0aec0', fontSize: '13px', margin: '0 0 20px', lineHeight: 1.5 }}>
          Deploy a zero-overhead SSH Honeypot Sensor on your target Linux server, AWS EC2 instance, or Virtual Machine. The installer shifts real SSH to Port 22222 and binds Cowrie Deception to Port 22.
        </p>

        {!sensorData ? (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            <div className="form-field">
              <label>Sensor Node Name / Target Server Label</label>
              <input
                type="text"
                value={sensorName}
                onChange={e => setSensorName(e.target.value)}
                placeholder="e.g. EC2-Production-Canary"
                className="form-input"
              />
            </div>
            <button
              onClick={handleRegister}
              disabled={loading}
              className="login-submit"
              style={{ background: 'linear-gradient(135deg, #7c3aed 0%, #06b6d4 100%)', marginTop: '8px' }}
            >
              {loading ? 'Generating Unique Key...' : 'Generate 1-Click Installer Script'}
            </button>
          </div>
        ) : (
          <div>
            <div style={{ background: 'rgba(124, 58, 237, 0.12)', border: '1px solid rgba(124, 58, 237, 0.3)', borderRadius: '8px', padding: '14px', marginBottom: '16px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '12px', color: '#c4b5fd', marginBottom: '6px' }}>
                <span>Your Unique Sensor Token:</span>
                <strong style={{ fontFamily: 'monospace', color: '#38bdf8' }}>{sensorData.token}</strong>
              </div>
              <div style={{ fontSize: '11px', color: '#a0aec0' }}>
                Assigned Tenant Account: <strong style={{ color: '#f0f4f8' }}>{currentUserId}</strong>
              </div>
            </div>

            <div className="form-field">
              <label style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                <Terminal size={14} /> 1-Line Installation Script (Paste into your Target Linux / AWS EC2 shell)
              </label>
              <div style={{ position: 'relative' }}>
                <textarea
                  readOnly
                  value={installCommand}
                  style={{
                    width: '100%',
                    height: '85px',
                    background: '#0d1117',
                    color: '#4fd1c5',
                    fontFamily: 'monospace',
                    fontSize: '11px',
                    padding: '12px 75px 12px 12px',
                    borderRadius: '8px',
                    border: '1px solid #30363d',
                    resize: 'none'
                  }}
                />
                <button
                  onClick={copyToClipboard}
                  style={{
                    position: 'absolute',
                    top: '12px',
                    right: '12px',
                    background: copied ? '#22c55e' : '#21262d',
                    color: '#ffffff',
                    border: '1px solid #30363d',
                    borderRadius: '6px',
                    padding: '6px 12px',
                    cursor: 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '4px',
                    fontSize: '11px',
                    fontWeight: 600
                  }}
                >
                  {copied ? <Check size={12} /> : <Copy size={12} />}
                  {copied ? 'Copied!' : 'Copy'}
                </button>
              </div>
            </div>

            <div style={{ marginTop: '16px', fontSize: '12px', color: '#a0aec0', background: 'rgba(255,255,255,0.03)', padding: '12px 16px', borderRadius: '8px' }}>
              <strong style={{ color: '#f0f4f8' }}>Installation Instructions:</strong>
              <ol style={{ margin: '8px 0 0 16px', padding: 0, lineHeight: 1.6 }}>
                <li>SSH into your target Linux / AWS EC2 server as <code>root</code> or <code>sudo</code>.</li>
                <li>Paste and run the 1-line command above.</li>
                <li>All incoming SSH attacks on Port 22 will automatically stream into your live SOC dashboard!</li>
              </ol>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
