import React from 'react'
import { motion } from 'framer-motion'
import { Shield, Cpu, UserCheck, Zap, Activity, ArrowRight, Layers, Database } from 'lucide-react'
import './App.css'

const LandingPage = ({ onLaunch }) => {
  return (
    <div className="landing">
      {/* Ambient background glow */}
      <div className="landing-glow glow-1" />
      <div className="landing-glow glow-2" />

      <div className="landing-content">
        {/* Hero */}
        <motion.div
          className="hero"
          initial={{ opacity: 0, y: 24 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
        >
          <div className="hero-badge">
            <Shield /> Next-Generation Honeypot Architecture
          </div>

          <h1 className="hero-title">
            The <span>Chameleon</span> Framework
          </h1>

          <p className="hero-desc">
            An intelligent deception engine that dynamically classifies SSH attackers using
            biometric keystroke analysis, deploying tailored countermeasures to bots, AI agents,
            and human adversaries.
          </p>

          <div className="hero-buttons">
            <button className="hero-btn hero-btn-primary" onClick={() => onLaunch('live')}>
              <Activity /> Launch Threat Radar
            </button>
            <button className="hero-btn hero-btn-secondary" onClick={() => onLaunch('archive')}>
              <Database /> View Forensics Archive
            </button>
          </div>
        </motion.div>

        {/* Feature Cards */}
        <motion.div
          className="features"
          initial={{ opacity: 0, y: 32 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.15 }}
        >
          <div className="feature-card card-bot">
            <div className="feature-icon"><Cpu /></div>
            <h3>Tier 1: Bots</h3>
            <p>Automated scanners and brute-forcers (0ms IAT). Mitigated with static Cowrie tarpits, saving computational resources.</p>
          </div>

          <div className="feature-card card-agent">
            <div className="feature-icon"><Zap /></div>
            <h3>Tier 2: AI Agents</h3>
            <p>Autonomous LLM hacking scripts (~1s IAT). Countered with prompt injection payloads to break agent context windows.</p>
          </div>

          <div className="feature-card card-human">
            <div className="feature-icon"><UserCheck /></div>
            <h3>Tier 3: Humans</h3>
            <p>Manual adversaries (&gt;2s IAT). Engaged with dynamically hallucinated Groq LLM honeytokens tailored to their intent.</p>
          </div>
        </motion.div>

        {/* Architecture */}
        <motion.div
          className="architecture"
          initial={{ opacity: 0, y: 32 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.3 }}
        >
          <div className="arch-label">
            <Layers />
            <h2>System Architecture</h2>
          </div>

          <div className="arch-flow">
            <div className="arch-node">
              Cowrie Honeypot
              <span>Ingestion</span>
            </div>
            <div className="arch-arrow"><ArrowRight /></div>
            <div className="arch-node">
              Biometric Classifier
              <span>IAT Analysis</span>
            </div>
            <div className="arch-arrow"><ArrowRight /></div>
            <div className="arch-node">
              Deception Engine
              <span>Response</span>
            </div>
            <div className="arch-arrow"><ArrowRight /></div>
            <div className="arch-node">
              SOC Dashboard
              <span>React / Vite</span>
            </div>
          </div>
        </motion.div>
      </div>
    </div>
  )
}

export default LandingPage
