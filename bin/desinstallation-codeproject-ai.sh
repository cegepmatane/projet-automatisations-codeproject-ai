#!/bin/bash
# =============================================================================
# Script d'desinstallation de Codeproject.AI
# Configure : [A DETERMINER]
# Usage : tmp=$(mktemp) && curl -fsSL https://raw.githubusercontent.com/cegepmatane/projet-automatisations-codeproject-ai/main/bin/desinstallation-codeproject-ai.sh -o "$tmp" && chmod +x "$tmp" && sudo "$tmp"; rm -f "$tmp"
# =============================================================================

set -e

if [ "$EUID" -ne 0 ]; then
  echo "Ce script doit etre execute avec sudo."
  echo "Exemple : sudo bash desinstallation-codeproject-ai.sh"
  exit 1
fi

echo "============================================================"
echo "  Desinstallation de Codeproject.AI"
echo "============================================================"
echo ""

# -----------------------------------------------------------------------------
# 1. 
# -----------------------------------------------------------------------------
echo ">>> Etape 1/X : Configuration du firewall UFW"

ufw delete allow 32168/tcp || true
read -p ">>> Voulez-vous supprimer le port 80 (HTTP) ? [y/N] " answer
if [[ "$answer" =~ ^[Yy]$ ]]; then
  ufw delete allow 80/tcp || true
  echo "Port 80 supprime"
else
  echo "Port 80 conserve"
fi

ufw status verbose

echo ""

# -----------------------------------------------------------------------------
# 2. 
# -----------------------------------------------------------------------------


# -----------------------------------------------------------------------------
# 3. 
# -----------------------------------------------------------------------------


# -----------------------------------------------------------------------------
# 4. 
# -----------------------------------------------------------------------------
