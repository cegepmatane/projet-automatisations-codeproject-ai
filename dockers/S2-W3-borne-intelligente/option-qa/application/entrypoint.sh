#!/bin/bash
# entrypoint.sh - point d'entree du container de la borne intelligente Q&A.
# Sequence :
#   1. lance ollama serve en arriere-plan
#   2. attend que l'API ollama (port 11434) reponde
#   3. pull le modele LLM si absent du cache (volume /root/.ollama)
#   4. lance l'application Pygame
#
# Le pull n'est pas dans le Dockerfile : il prend du temps, il est meilleur
# de le faire au premier demarrage avec le volume monte pour que le modele
# persiste entre les redemarrages du container.

set -e

modeleLlm="${MODELE_LLM:-qwen2.5:0.5b}"

echo "[entrypoint] demarrage d'ollama serve en arriere-plan..."
ollama serve > /tmp/ollama.log 2>&1 &
pidOllama=$!

# Attente que l'API ollama reponde.
echo "[entrypoint] attente de l'API ollama sur 127.0.0.1:11434..."
tentativesMax=60
for tentativeCourante in $(seq 1 "$tentativesMax"); do
    if curl --silent --fail "http://127.0.0.1:11434/api/tags" > /dev/null 2>&1; then
        echo "[entrypoint] ollama est pret (tentative $tentativeCourante)."
        break
    fi
    if ! kill -0 "$pidOllama" 2>/dev/null; then
        echo "[entrypoint] ollama serve s'est arrete prematurement. Log :"
        cat /tmp/ollama.log
        exit 1
    fi
    sleep 1
done

if ! curl --silent --fail "http://127.0.0.1:11434/api/tags" > /dev/null 2>&1; then
    echo "[entrypoint] ollama ne repond toujours pas apres $tentativesMax secondes."
    exit 1
fi

# Pull du modele si absent. ollama list affiche tous les modeles caches.
if ollama list 2>/dev/null | awk 'NR > 1 {print $1}' | grep -q "^${modeleLlm}$"; then
    echo "[entrypoint] modele $modeleLlm deja present dans le cache."
else
    echo "[entrypoint] modele $modeleLlm absent. Telechargement en cours..."
    echo "[entrypoint] (premier lancement : 2 a 3 minutes selon la connexion)"
    ollama pull "$modeleLlm"
    echo "[entrypoint] modele $modeleLlm telecharge."
fi

# Lancement de l'application Pygame. Elle se connecte a ollama en localhost.
echo "[entrypoint] lancement de la borne Pygame."
exec python qa.py
