# Chameleon Framework

An Adaptive Deception Framework for SSH Honeypots using Real-Time Behavioral Biometrics.

## Overview
Chameleon is an advanced honeypot orchestration framework designed to adapt its deception strategy based on the real-time behavioral timing signature of the attacker. By analyzing inter-command keystroke dynamics, Chameleon instantly classifies SSH sessions into three tiers:

- **Tier 1 (Legacy Bots):** Receives computationally cheap, static tarpit responses.
- **Tier 2 (AI Agents):** Receives poisoned data drops to corrupt autonomous learning loops.
- **Tier 3 (Human Attackers):** Triggers expensive, high-fidelity Large Language Model (LLM) deception generation to waste time and extract intelligence.

This architecture solves a critical gap in generative deception research: gating expensive LLM inference behind a mathematical behavioral classifier, ensuring computational resources are only spent on high-value human targets instead of the 99% automated bot noise.

## Architecture components
1. **Cowrie Honeypot (Ingestion Layer):** Captures raw SSH session data and logs commands in real-time.
2. **Python Backend (Orchestration Engine):** Computes inter-command timing metrics (Mean IAT, Jitter Variance), maps intent to the MITRE ATT&CK framework, and dynamically deploys deception payloads.
3. **React/Vite Frontend (SOC Threat Radar):** A live Security Operations Center dashboard that visualizes active attacks, classification tiers, and deployed deception measures in real-time.

## Quick Start
Ensure Docker Desktop is running before starting the framework.

1. **Start the Honeypot:**
   ```bash
   docker start -a cowrie
   ```
2. **Start the Backend Engine:**
   ```bash
   cd backend
   python main.py
   ```
3. **Start the Threat Radar Dashboard:**
   ```bash
   cd frontend
   npm run dev
   ```

## Academic Research Focus
This prototype was developed as a Final Year Project to validate the hypothesis that inter-command timing signatures (zero delay vs inference delay vs cognitive bursting) can be used to accurately distinguish legacy automation, LLM-driven offensive agents, and human attackers in real-time SSH sessions.
