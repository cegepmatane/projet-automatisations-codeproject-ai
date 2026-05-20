#!/bin/bash
# entrypoint.sh - point d'entree du container de la borne narrative.
# Demarre ollama en arriere-plan, attend que l'API repond, tire le modele
# qwen2.5:0.5b si absent, puis lance l'application Pygame.

set -e

nomModele="qwen2.5:0.5b"
urlApi="http://127.0.0.1:11434"

echo "[entrypoint] demarrage du serveur ollama en arriere-plan..."
ollama serve &
pidServeurOllama=$!

# Attente active jusqu'a ce que l'API ollama reponde.
# 60 tentatives x 1s = 60s max au demarrage du serveur.
echo "[entrypoint] attente du port 11434..."
nombreEssais=0
while ! curl --silent --fail "${urlApi}/api/tags" > /dev/null 2>&1; do
    nombreEssais=$((nombreEssais + 1))
    if [ "$nombreEssais" -ge 60 ]; then
        echo "[entrypoint] erreur : ollama ne repond pas apres 60s." >&2
        kill "$pidServeurOllama" 2>/dev/null || true
        exit 1
    fi
    sleep 1
done
echo "[entrypoint] ollama est pret."

# Pull du modele si pas deja present dans le cache (volume persiste).
# Le grep ignore la casse et accepte le tag complet ou court.
modelePresent=$(curl --silent "${urlApi}/api/tags" | grep -c "${nomModele}" || true)
if [ "$modelePresent" -eq 0 ]; then
    echo "[entrypoint] modele ${nomModele} absent, telechargement (~400 Mo)..."
    ollama pull "${nomModele}"
    echo "[entrypoint] modele ${nomModele} pret."
else
    echo "[entrypoint] modele ${nomModele} deja en cache."
fi

# Lancement de l'app Pygame. Elle parle a ollama via HTTP localhost.
# Quand python sort, on coupe ollama proprement pour que le container s'arrete.
echo "[entrypoint] lancement de l'application narrative..."
python /borne/narrative.py
codeSortiePython=$?

echo "[entrypoint] application terminee (code ${codeSortiePython}). Arret d'ollama..."
kill "$pidServeurOllama" 2>/dev/null || true
wait "$pidServeurOllama" 2>/dev/null || true
exit "$codeSortiePython"
