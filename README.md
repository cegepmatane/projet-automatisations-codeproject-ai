# Cédric Simard
projet-automatisations...

## Script d'installation de Codeproject.AI:
- Configure : [A DETERMINER]
- Usage : 
```bash
tmp=$(mktemp) && curl -fsSL -H "Cache-Control: no-cache" "https://raw.githubusercontent.com/cegepmatane/projet-automatisations-codeproject-ai/main/bin/installation-codeproject-ai.sh" -o "$tmp" && chmod +x "$tmp" && sudo "$tmp"; rm -f "$tmp"
```

## Script de desinstallation de Codeproject.AI
- Configure : [A DETERMINER]
- Usage : 
```bash
tmp=$(mktemp) && curl -fsSL -H "Cache-Control: no-cache" "https://raw.githubusercontent.com/cegepmatane/projet-automatisations-codeproject-ai/main/bin/desinstallation-codeproject-ai.sh" -o "$tmp" && chmod +x "$tmp" && sudo "$tmp"; rm -f "$tmp"
```