#!/bin/bash
# =============================================================================
# Script d'installation de Codeproject.AI
# Configure : [A DETERMINER]
# Usage : tmp=$(mktemp) && curl -fsSL -H "Cache-Control: no-cache" "https://raw.githubusercontent.com/cegepmatane/projet-automatisations-codeproject-ai/main/bin/installation-codeproject-ai.sh" -o "$tmp" && chmod +x "$tmp" && sudo "$tmp"; rm -f "$tmp"
# =============================================================================

set -e

if [ "$EUID" -ne 0 ]; then
  echo "Ce script doit etre execute avec sudo."
  echo "Exemple : sudo bash installation-codeproject-ai.sh"
  exit 1
fi

SERVER_IP=$(hostname -I | awk '{print $1}') # ip du server

echo "============================================================"
echo "  Installation de Codeproject.AI"
echo "============================================================"

echo ""
# -----------------------------------------------------------------------------
# 1. Activation des ports requis
# -----------------------------------------------------------------------------
echo ">>> Etape 1/7 : Configuration du firewall UFW"
