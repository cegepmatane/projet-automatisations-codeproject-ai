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

mkdir -p /etc/nginx/codeproject-ai/

read -s -p ">>> Mot de passe pour l'utilisateur admin: " PASSWORD
echo

htpasswd -b -c /etc/nginx/codeproject-ai/.htpasswd admin "$PASSWORD"

chmod 640 /etc/nginx/codeproject-ai/.htpasswd
chown root:www-data /etc/nginx/codeproject-ai/.htpasswd

echo "Authentification HTTP configuree (OK)"

echo ""

# -----------------------------------------------------------------------------
# 6. Ajout configurations Nginx
# -----------------------------------------------------------------------------
echo ">>> Etape 6/X : Ajout configurations Nginx"

cat > /etc/nginx/sites-available/codeproject-ai << EOF
# Garde en mémoire l'IP de chaque client dans une zone de 10 Mo.
# Limite à 10 requêtes par seconde par IP.
limit_req_zone \$binary_remote_addr zone=limite_adresses:10m rate=10r/s;

server {
  listen 80;
  server_name ${SERVER_IP};

  # Autorise jusqu'à 20 requêtes en attente (burst).
  # nodelay = pas de délai artificiel sur ces 20 requêtes.
  limit_req zone=limite_adresses burst=20 nodelay;

  # Taille max d'un fichier envoyé (upload d'image, etc.)
  client_max_body_size 20M;

  # ── 1. Site public ────────────────────────────────────────────────
  # Toute URL qui ne commence pas par /codeproject/ arrive ici.
  # Nginx cherche le fichier correspondant dans /var/www/html.
  # Si l'URL est "/" il sert index.html.
  location / {
    root /var/www/html;
    index index.html;
  }

  # ── 2. App protégée ───────────────────────────────────────────────
  # Toute URL commençant par /codeproject/ déclenche ce bloc.
  location /codeproject/ {

    # Demande un mot de passe avant d'aller plus loin.
    # Le message "Restricted Access..." s'affiche dans la popup du navigateur.
    auth_basic "Restricted Access to the Project";
    auth_basic_user_file /etc/nginx/codeproject-ai/.htpasswd;

    # Redirige la requête vers CodeProject.AI qui tourne en local.
    # Le "/" final est important : il enlève /codeproject/ du chemin
    # avant de le transmettre à l'app (ex: /codeproject/v1/detect → /v1/detect).
    proxy_pass http://127.0.0.1:32168/;

    # Transmet les vraies informations du client à l'app.
    proxy_set_header Host \$host;
    proxy_set_header X-Real-IP \$remote_addr;
    proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto \$scheme;

    # Délais longs pour les requêtes d'IA (inférence peut prendre du temps).
    proxy_connect_timeout 300s;
    proxy_send_timeout 300s;
    proxy_read_timeout 300s;
  }
}
EOF

ln -sf /etc/nginx/sites-available/codeproject-ai /etc/nginx/sites-enabled/codeproject-ai
nginx -t && systemctl reload nginx
systemctl restart nginx

echo "Configurations Nginx ajoutees (OK)"

echo ""

# -----------------------------------------------------------------------------
# 7. Ajout fichier index.html
# -----------------------------------------------------------------------------
echo ">>> Etape 7/X : Ajout fichier index.html"

mkdir -p /var/www/html/codeproject-ai
cat > /var/www/html/codeproject-ai/index.html << EOF
test
EOF

echo ""