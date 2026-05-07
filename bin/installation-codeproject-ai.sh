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

echo "service CodeProject.AI-Server installé sur http://localhost:32168 (OK)"

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
# Force CodeProject.AI à écouter seulement sur localhost
# -----------------------------------------------------------------------------
echo ">>> Configuration localhost pour CodeProject.AI"

mkdir -p /etc/systemd/system/codeproject.ai-server.service.d

cat > /etc/systemd/system/codeproject.ai-server.service.d/override.conf << EOF
[Service]
Environment=ASPNETCORE_URLS=http://127.0.0.1:32169
EOF

systemctl daemon-reload
systemctl restart codeproject.ai-server

echo "Verification du port :"
ss -tulpn | grep 32168 || true

echo ""
echo "Configuration localhost appliquee (OK)"


# -----------------------------------------------------------------------------
# 6. Ajout configurations Nginx
# -----------------------------------------------------------------------------
echo ">>> Etape 6/X : Ajout configurations Nginx"

cat > /etc/nginx/sites-available/codeproject-ai << 'EOF'

server {
    listen 80;
    server_name _;

    location / {
        root /var/www/html;
        index index.html;
    }
}

server {
    listen 32168;

    auth_basic "CodeProject AI Admin";
    auth_basic_user_file /etc/nginx/codeproject-ai/.htpasswd;

    location / {
        proxy_pass http://127.0.0.1:32169;

        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
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

echo "Fichier index.html ajoute (OK)"

echo ""

# -----------------------------------------------------------------------------
# 4. Firewall
# -----------------------------------------------------------------------------
#echo "NOTE: recommandé de fermer accès direct"
#echo "sudo ufw delete allow 32168/tcp"