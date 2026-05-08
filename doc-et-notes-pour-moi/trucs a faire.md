# 3.1 — Variables
Chemins et valeurs stockés dans des variables nommées
```bash
BACKUP_DIR="/var/backups/app"
LOG_FILE="/var/log/surveillance.log"
DATE=$(date +%Y-%m-%d)
DISK_USAGE=$(df -h / | grep / | awk '{print $5}')
echo "Sauvegarde dans : $BACKUP_DIR"
```

# 3.2 — Conditions (if)
Rotation : supprimer l'ancienne archive si elle existe
```bash
if [ -f "$BACKUP_DIR/backup_old.tgz" ]; then
    rm "$BACKUP_DIR/backup_old.tgz"
    echo "Ancienne archive supprimée"
else
    echo "Pas d'ancienne archive à supprimer"
fi
```

# 3.3 — Succession conditionnelle (&& et ||)
Créer le dossier ET zipper, sinon afficher l'erreur
```bash
mkdir -p "$BACKUP_DIR" && \
    tar -czf "$BACKUP_DIR/backup_$DATE.tgz" /etc/app || \
    echo "ERREUR : la sauvegarde a échoué"
```

# 3.4 — Tableaux et boucles (facultatif)
Sauvegarder plusieurs répertoires en boucle
```bash
DIRS=("/etc/app" "/var/www" "/home/user")
for dir in "${DIRS[@]}"; do
    tar -czf "$BACKUP_DIR/$(basename $dir)_$DATE.tgz" "$dir"
done
```

# 3.5 — Fonctions (facultatif)
Fonction réutilisable pour logger un message
```bash
log_message() {
    echo "[$(date +%H:%M:%S)] $1" >> "$LOG_FILE"
}
log_message "Sauvegarde démarrée"
```

# 4.1 — Chaînage avec pipe (|)
Extraire la date depuis le nom d'un fichier
```bash
ls "$BACKUP_DIR" | grep "backup_" | cut -d'_' -f2 | cut -d'.' -f1
Surveiller l'utilisation CPU via pipe
top -bn1 | grep "Cpu" | cut -d',' -f1 | cut -d':' -f2
```

# 4.2 — Compression .tgz avec tar
Créer et vérifier une archive .tgz
## Créer l'archive
```bash
tar -czf "$BACKUP_DIR/backup_$DATE.tgz" /etc/app
```

## Vérifier le contenu sans extraire
```bash
tar -tzf "$BACKUP_DIR/backup_$DATE.tgz"
```

# 4.3 — Redirections (> et >>) + tee
Écrire dans un log ET afficher dans le terminal
## > écrase, >> ajoute
```bash
echo "Début surveillance : $DATE" >> "$LOG_FILE"
```

## tee : affiche ET écrit dans le fichier protégé en même temps
```bash
echo "CPU : $CPU_USAGE" | tee -a "/var/log/audit.log"
```

# 4.4 — Paramètres de script (facultatif)
Passer l'utilisateur et le mot de passe en argument
## Appel : ./install.sh admin monMotDePasse
```bash
DB_USER="$1"
DB_PASS="$2"
mysql -u "$DB_USER" -p"$DB_PASS" -e "SHOW DATABASES;"
```

# 5.1 — grep + cut
Isoler le nom de fichier et une valeur dans un log
## Nom du dernier backup
```bash
ls "$BACKUP_DIR" | grep "\.tgz$" | tail -1
```

## Extraire l'usage disque (champ 5) dans df
```bash
df -h / | grep "/$" | cut -d' ' -f9
```

# 5.2 — Regex avec grep et sed
grep : filtrer les lignes ERROR dans un log
```bash
grep -E "^[0-9]{4}-[0-9]{2}-[0-9]{2}.*ERROR" /var/log/app.log
sed : remplacer automatiquement une valeur dans un fichier de config
sed -i 's/^max_connections=.*/max_connections=200/' /etc/app/app.conf
```

# 5.3 — awk (facultatif, alternative à grep+cut)
Extraire le 3e champ d'un fichier séparé par ':'
```bash
awk -F':' '{print $3}' /etc/passwd | head -5
```

# 6.1 — Lancement automatique avec cron
Ajouter une tâche cron (chaque jour à 2h du matin)
## Éditer avec : crontab -e
```bash
0 2 * * * /bin/bash /opt/scripts/backup.sh >> /var/log/backup.log 2>&1
```

# 6.2 — Commandes non-interactives
Installer un paquet sans confirmation utilisateur
## -y répond "oui" automatiquement
```bash
apt-get install -y nginx
```

## Création de l'utilisateur sans prompt
```bash
useradd -m -s /bin/bash appuser
```

# 6.3 — Édition automatique de fichiers
Modifier une config sans ouvrir d'éditeur
## sed remplace la ligne de config en place
```bash
sed -i 's/^#Port 22/Port 2222/' /etc/ssh/sshd_config
```

# 6.4 — Chemins absolus (mkdir, mv, chmod, chown)
Créer, déplacer, protéger un fichier de sauvegarde
```bash
mkdir -p /var/backups/app
mv /tmp/backup_$DATE.tgz /var/backups/app/backup_$DATE.tgz
chmod 640 /var/backups/app/backup_$DATE.tgz
chown root:backup /var/backups/app/backup_$DATE.tgz¸
```
