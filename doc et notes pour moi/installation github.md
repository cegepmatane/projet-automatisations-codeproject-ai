# Pour installation et réinstallation facile 
>[!NOTE] NOTES :
>
>- Github: `git@github.com:cegepmatane/projet-automatisations-enderbird.git`
>- Besoin...
>   - d'un serveur linux (linode)
>   - d'un PC avec linux
> - Initialiser le serveur avec le script de la prof:
>```
>curl -fsSL https://raw.githubusercontent.com/nadineprofesseur/vps/refs/heads/main/bin/initialiser-serveur.sh -o /tmp/init.sh && sudo bash /tmp/init.sh cedri
>```

---
---
---
---
---

## Get la clée de départ (à réutiliser)...
- Faire ça sur un ordi random ou sur le serveur (on a juste besoin de la clée). Copier et garder pour les prochaines étapes :
```bash
ssh-keygen -t ed25519 -C "vps-serveur-temporaire"
cat ~/.ssh/id_ed25519.pub
```

<a id="clee_publique"></a>

>[!IMPORTANT] CLÉE PUBLIQUE :
>
>```
>ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIMw07CkipoP8zhwWyFWVxaQHr/991HPuVLq7+HThpksZ vps-serveur-temporaire
>```

```bash
cat ~/.ssh/id_ed25519
```

<a id="clee_privee"></a>

>[!IMPORTANT] CLÉE PRIVÉE :
>```
>-----BEGIN OPENSSH PRIVATE KEY-----
>b3BlbnNzaC1rZXktdjEAAAAABG5vbmUAAAAEbm9uZQAAAAAAAAABAAAAMwAAAAtzc2gtZW
>QyNTUxOQAAACDMNOwpIqaD/M4cFshVlcWkB6//fdRz7lS6u/h04aZLGQAAAKBOs5wxTrOc
>MQAAAAtzc2gtZWQyNTUxOQAAACDMNOwpIqaD/M4cFshVlcWkB6//fdRz7lS6u/h04aZLGQ
>AAAEARRdxt0VqZ0Izw5vNLeBzGx3NO6zzz9M8KeuSPwfzYGsw07CkipoP8zhwWyFWVxaQH
>r/991HPuVLq7+HThpksZAAAAFnZwcy1zZXJ2ZXVyLXRlbXBvcmFpcmUBAgMEBQYH
>-----END OPENSSH PRIVATE KEY-----
>```

---
---
---

### Utiliser la clée sur le github...
- https://github.com/settings/keys
- Faire `New SSH key` :
> ---
>#### Title
>```
>vps-serveur-temporaire
>```
>
>#### Key type
>`Authentication Key`
>
>#### Key
>[<- coller la clé publique](#clee_publique)
> 
>`Add SSH key`
> ---

---
---
---

### Utiliser la clée dans l'installation...

#### 1. Installation de git
```bash
sudo apt update && sudo apt install -y git openssh-client
```

#### 2. Création du dossier SSH
```bash
sudo mkdir -p ~/.ssh
sudo chown -R $USER:$USER ~/.ssh
sudo chmod 700 ~/.ssh

ls -l ~/.ssh
```

#### 3. Installation de la clé GitHub
```bash
sudo nano ~/.ssh/id_ed25519
```
[^^^ coller la clé privée ^^^](#clee_privee)

#### 4. Permissions clé SSH
```bash
sudo chmod 600 ~/.ssh/id_ed25519
```

#### 5. Ajout GitHub config
```bash
sudo ssh-keyscan github.com >> ~/.ssh/known_hosts
```

#### 5. Test GitHub
```bash
sudo ssh -T git@github.com
```

#### 6. Préparation dossier repo
```bash
sudo mkdir -p ~/github
sudo chown -R $USER:$USER ~/github
sudo chmod 755 ~/github
sudo chgrp -R $USER ~/github
chmod g+s ~/github
cd ~/github
```

#### 7. Clonage du repo
```bash
cd 
REPO="git@github.com:cegepmatane/projet-automatisations-enderbird.git"
DIR="$HOME/github/projet-automatisations-enderbird"

mkdir -p "$HOME/github"

if [ -d "$DIR/.git" ]; then
  echo "Repo déjà présent -> git pull"
  cd "$DIR" && git pull
else
  sudo git clone "$REPO" "$DIR"
fi
cd "$DIR"

unset REPO
unset DIR
```
