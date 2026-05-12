#!/usr/bin/env bash
set -euo pipefail

readonly NOM_SERVICE="codeproject.ai-server"

readonly DOSSIER_AUDIT="/root/audit"
readonly SUFFIXE="$(tr -dc 'a-z0-9' < /dev/urandom | head -c 4)"
readonly FICHIER_AUDIT="${DOSSIER_AUDIT}/audit-$(date +%Y-%m-%d)-${SUFFIXE}.txt"

mkdir -p "${DOSSIER_AUDIT}"

echo "===== AUDIT ${NOM_SERVICE} $(date) =====" | tee -a "${FICHIER_AUDIT}"

echo ""
echo ">>> 1. Service systemd" | tee -a "${FICHIER_AUDIT}"
systemctl is-active "${NOM_SERVICE}" | tee -a "${FICHIER_AUDIT}"

echo ""
echo ">>> 2. Port 8080 (nginx)" | tee -a "${FICHIER_AUDIT}"
ss -tlnp | grep ":8080" | tee -a "${FICHIER_AUDIT}" || echo "PORT 8080 ABSENT" | tee -a "${FICHIER_AUDIT}"

echo ""
echo ">>> 3. RAM" | tee -a "${FICHIER_AUDIT}"
free -h | awk '/Mem:/ {print "RAM libre:", $7}' | tee -a "${FICHIER_AUDIT}"

echo ""
echo ">>> 4. Disque" | tee -a "${FICHIER_AUDIT}"
df -h / | awk 'NR==2 {print "Disque libre:", $4, "utilisé:", $5}' | tee -a "${FICHIER_AUDIT}"

echo ""
echo ">>> 5. Nginx status" | tee -a "${FICHIER_AUDIT}"
systemctl is-active nginx | tee -a "${FICHIER_AUDIT}"

echo ""
echo ">>> 6. Test API" | tee -a "${FICHIER_AUDIT}"
curl -fsS http://localhost:8080/ > /dev/null && echo "API OK" | tee -a "${FICHIER_AUDIT}" || echo "API FAIL" | tee -a "${FICHIER_AUDIT}"

echo ""
echo "AUDIT TERMINÉ"