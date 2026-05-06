#!/bin/bash
# =============================================================================
# Script d'installation de Codeproject.AI
# Configure : [A DETERMINER]
# Usage : sudo bash <(curl -fsSL https://raw.githubusercontent.com/cegepmatane/projet-automatisations-enderbird/main/bin/installation-codeproject-ai.sh)
# =============================================================================

set -e

if [ "$EUID" -ne 0 ]; then
  echo "Ce script doit etre execute avec sudo."
  echo "Exemple : sudo bash installation-codeproject-ai.sh"
  exit 1
fi

echo "============================================================"
echo "  Installation de Codeproject.AI"
echo "============================================================"
echo ""

# -----------------------------------------------------------------------------
# 1. 
# -----------------------------------------------------------------------------
echo ">>> Etape 1/X : Configuration du firewall UFW"

apt-get update
apt-get install -y ufw

ufw --force reset

ufw allow 80/tcp
ufw allow 32168/tcp

ufw --force enable
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
