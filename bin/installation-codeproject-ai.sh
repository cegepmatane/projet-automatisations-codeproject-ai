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
ufw allow 8080/tcp
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
# 5. Nginx + auth
# -----------------------------------------------------------------------------
echo ">>> Etape 5 : Nginx + auth"

apt-get update
apt install -y nginx apache2-utils

mkdir -p /etc/nginx/codeproject-ai/

read -s -p "Mot de passe admin: " PASSWORD
echo

htpasswd -b -c /etc/nginx/codeproject-ai/.htpasswd admin "$PASSWORD"

chmod 640 /etc/nginx/codeproject-ai/.htpasswd
chown root:www-data /etc/nginx/codeproject-ai/.htpasswd

echo ""

# -----------------------------------------------------------------------------
# 6. Nginx config CLEAN
# -----------------------------------------------------------------------------
echo ">>> Etape 6 : Nginx config"

cat > /etc/nginx/sites-available/codeproject-ai << EOF

# definit la rate limite
# conserve les IPs dans la variable \$binary_remote_addr de 10 megabytes
# limite a 10 requetes par secondes
limit_req_zone \$binary_remote_addr zone=limite_adresses:10m rate=10r/s;

server {
    listen 80;
    server_name $SERVER_IP;

    # 1 - Public site (no auth)
    location /codeproject-ai/ {
        root /var/www/html;
        index index.html;
    }
}   
    
server {
    listen 8080;
    server_name $SERVER_IP;
    
    # applique la rate limite
    # met jusqu'a 20 requetes dans la file d'attente
    # nodelay fait en sorte que les requetes dans la file d'attente n'aient pas de delais,
    # ce qui evite que l'application apparaisse lante
    limit_req zone=limite_adresses burst=20 nodelay;

    client_max_body_size 20M;
    
    auth_basic "Admin Only";
    auth_basic_user_file /etc/nginx/codeproject-ai/.htpasswd;

    # 2 - Protected app
    location / {
        proxy_pass http://127.0.0.1:32168/;

        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
    
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";

        proxy_connect_timeout 300s;
        proxy_send_timeout 300s;
        proxy_read_timeout 300s;
    }
}  

EOF

# rm -f /etc/nginx/sites-enabled/defaultk
ln -sf /etc/nginx/sites-available/codeproject-ai /etc/nginx/sites-enabled/codeproject-ai

nginx -t && systemctl restart nginx

echo "OK nginx configuré"

echo ""

# -----------------------------------------------------------------------------
# 7. index.html
# -----------------------------------------------------------------------------
echo ">>> Etape 7 : index.html"

mkdir -p /var/www/html/codeproject-ai

cat > /var/www/html/codeproject-ai/index.html << EOF
<html>
    <body>
    Detect the scene in this file: <input id="image" type="file" />
    <input type="button" value="Detect Scene" onclick="detectScene(image)" />

    <script>
    function detectScene(fileChooser) {
        var formData = new FormData();
        formData.append('image', fileChooser.files[0]);

        fetch('http://<votre adress ip>/codeproject/v1/vision/detection', {
            method: "POST",
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            console.log(data);

            const pred = data.predictions?.[0];

            if (pred) {
                console.log(pred.label, pred.confidence);
            }
        });
    }
    </script>
    </body>
</html>
EOF

echo "OK index.html"

echo ""

# -----------------------------------------------------------------------------
# 8. sécurité optionnelle
# -----------------------------------------------------------------------------
echo ">>> Etape 8 : recommandation sécurité"

echo "Optionnel: fermer accès direct"
echo "sudo ufw delete allow 32168/tcp"

echo ""
echo ""


# -----------------------------------------------------------------------------
# INSTALLATION TERMINÉE (on peut starter le service)
# -----------------------------------------------------------------------------
