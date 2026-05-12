# Cédric Simard
projet-automatisations...

## Script d'installation de CodeProject.AI
- Configure : installation complète du service (paquet, config nginx, service systemd, port, webclient)
- Usage : 
```bash
tmp=$(mktemp) && curl -fsSL "https://raw.githubusercontent.com/cegepmatane/projet-automatisations-codeproject-ai/main/bin/installation-codeproject-ai.sh" -o "$tmp" && chmod +x "$tmp" && sudo "$tmp"; rm -f "$tmp"
```

## BONUS : Script de desinstallation de Codeproject.AI
- Configure : suppression complète du service et nettoyage du système
- Usage : 
```bash
tmp=$(mktemp) && curl -fsSL "https://raw.githubusercontent.com/cegepmatane/projet-automatisations-codeproject-ai/main/bin/desinstallation-codeproject-ai.sh" -o "$tmp" && chmod +x "$tmp" && sudo "$tmp"; rm -f "$tmp"
```