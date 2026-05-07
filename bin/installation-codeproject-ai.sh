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

SERVER_IP=$(hostname -I | awk '{print $1}') # ip du server

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
echo ">>> Etape 4/X : Installation de CodeProject.AI-Server"

wget https://codeproject-ai-bunny.b-cdn.net/server/installers/linux/codeproject.ai-server_2.9.5_Ubuntu_x64.zip
unzip -o codeproject.ai-server_2.9.5_Ubuntu_x64.zip
rm -f codeproject.ai-server_2.9.5_Ubuntu_x64.zip
dpkg -i codeproject.ai-server_2.9.5_Ubuntu_x64.deb || apt --fix-broken install -y
rm -f codeproject.ai-server_2.9.5_Ubuntu_x64.deb

pushd "/usr/bin/codeproject.ai-server-2.9.5/" && bash setup.sh && popd
pushd "/usr/bin/codeproject.ai-server-2.9.5/server" && bash ../setup.sh && popd

echo "CodeProject.AI-Server installé (OK)"

systemctl start codeproject.ai-server
systemctl enable codeproject.ai-server

echo "service CodeProject.AI-Server ouvert sur http://localhost:32168 ou http://$SERVER_IP:32168"

echo ""

# -----------------------------------------------------------------------------
# 5. Ajout authentification HTTP
# -----------------------------------------------------------------------------
echo ">>> Etape 5/X : Ajout authentification HTTP"

apt-get update
apt install -y nginx apache2-utils

sudo mkdir -p /etc/nginx/codeproject-ai/
sudo touch /etc/nginx/codeproject-ai/.htpasswd

read -s -p ">>> Mot de passe pour l'utilisateur admin: " PASSWORD
echo
if [ ! -f /etc/nginx/codeproject-ai/.htpasswd ]; then
  htpasswd -b -c /etc/nginx/codeproject-ai/.htpasswd admin "$PASSWORD"
else
  htpasswd -b /etc/nginx/codeproject-ai/.htpasswd admin "$PASSWORD"
fi

echo "Authentification HTTP configuree (OK)"

echo ""

# -----------------------------------------------------------------------------
# 6. Ajout configurations Nginx
# -----------------------------------------------------------------------------
echo ">>> Etape 6/X : Ajout configurations Nginx"

cat > /etc/nginx/sites-available/codeproject-ai << EOF
limit_req_zone \$binary_remote_addr zone=limite_adresses:10m rate=10r/s;

server {
  listen 80;
  server_name $SERVER_IP;

  limit_req zone=limite_adresses burst=20 nodelay;

  client_max_body_size 20M;

  location / {
    root /var/www/html/codeproject-ai;
    index index.html;
  }

  location /codeproject/ {
    auth_basic "Restricted Access to the Project";
    auth_basic_user_file /etc/nginx/codeproject-ai/.htpasswd;

    proxy_pass http://$SERVER_IP:32168/;

    proxy_set_header Host \$host;
    proxy_set_header X-Real-IP \$remote_addr;
    proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto \$scheme;

    proxy_connect_timeout 300s;
    proxy_send_timeout 300s;
    proxy_read_timeout 300s;
  }
}
EOF

ln -s /etc/nginx/sites-available/codeproject-ai /etc/nginx/sites-enabled/codeproject-ai
nginx -t && systemctl reload nginx

echo "Configurations Nginx ajoutees (OK)"

echo ""

# -----------------------------------------------------------------------------
# 6. 
# -----------------------------------------------------------------------------
