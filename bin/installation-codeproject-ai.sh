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

echo "============================================================"
echo "  Installation de Codeproject.AI"
echo "============================================================"
echo ""

# -----------------------------------------------------------------------------
# 1. Activation des ports requis
# -----------------------------------------------------------------------------
echo ">>> Etape 1/X : Configuration du firewall UFW"

apt-get update
apt-get install -y ufw

ufw allow 80/tcp
ufw allow 32168/tcp

ufw --force enable
ufw status verbose

echo ""

# -----------------------------------------------------------------------------
# 2. Installation .NET 9
# -----------------------------------------------------------------------------
echo ">>> Etape 2/X : Installation de .NET 9"

apt-get update
yes | add-apt-repository ppa:dotnet/backports
apt-get update
apt-get install -y dotnet-sdk-9.0

dotnet --version

echo ""

# -----------------------------------------------------------------------------
# 3. Installation unzip
# -----------------------------------------------------------------------------
echo ">>> Etape 3/X : Installation de unzip"

echo ">>> Installation de unzip"

apt-get update
apt install -y unzip

echo ""

# -----------------------------------------------------------------------------
# 4. Installation de CodeProject.AI-Server
# -----------------------------------------------------------------------------
echo ">>> Etape 3/X : Installation de CodeProject.AI-Server"

wget https://codeproject-ai-bunny.b-cdn.net/server/installers/linux/codeproject.ai-server_2.9.5_Ubuntu_x64.zip

unzip -o codeproject.ai-server_2.9.5_Ubuntu_x64.zip
dpkg -i codeproject.ai-server_2.9.5_Ubuntu_x64.deb || apt --fix-broken install -y

pushd "/usr/bin/codeproject.ai-server-2.9.5/" && bash setup.sh && popd
pushd "/usr/bin/codeproject.ai-server-2.9.5/server" && bash ../setup.sh && popd

rm -f codeproject.ai-server_2.9.5_Ubuntu_x64.zip
rm -f codeproject.ai-server_2.9.5_Ubuntu_x64.deb

echo "CodeProject.AI-Server installe (OK)"

echo ""

# -----------------------------------------------------------------------------
# 5. 
# -----------------------------------------------------------------------------
