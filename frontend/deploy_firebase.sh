#!/usr/bin/env bash
# ==============================================================================
# Chameleon Frontend — Firebase Hosting Deployment Script
# Usage: ./deploy_firebase.sh
# ==============================================================================

set -e

echo "=========================================================================="
echo "          CHAMELEON FRONTEND — FIREBASE HOSTING DEPLOYMENT                "
echo "=========================================================================="

# 1. Build Production Bundle
echo "[+] Compiling production React bundle with Vite..."
npm run build

# 2. Deploy to Firebase Hosting
echo "[+] Deploying assets to Firebase Hosting..."
npx firebase-tools deploy --only hosting

echo "=========================================================================="
echo " [SUCCESS] CHAMELEON FRONTEND DEPLOYED TO FIREBASE HOSTING!               "
echo "=========================================================================="
