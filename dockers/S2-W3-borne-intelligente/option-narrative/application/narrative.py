"""
Borne intelligente narrative - Aventure Pygame generee par LLM local
Zoo maritime du Bas-Saint-Laurent

Application kiosque qui propose au visiteur d'incarner un soigneur stagiaire
dans l'un des trois pavillons du zoo (marin, forestier, pollinisateurs).
A chaque etape, un modele de langage local (ollama, qwen2.5:0.5b) genere
une situation narrative et trois choix d'action. Le visiteur clique son
choix, l'IA poursuit. La derniere etape conclut l'aventure.

Architecture :
  - boucle Pygame classique (init / event / render / tick)
  - machine a etats : "choix-ecosysteme" -> "aventure" -> "aventure" ... -> "conclusion"
  - generation LLM dans un thread d'arriere-plan, l'UI affiche un spinner
    et reste reactive (au moins pour le clic ESC).
  - parsing tolerant de la sortie du modele : si le 0.5b echoue a fournir
    A/B/C, on retombe sur des choix generiques.
"""

import json
import math
import os
import queue
import random
import re
import sys
import threading
import time

import pygame
import requests

from prompts import (
    ECOSYSTEMES,
    construireMessageEtape,
    construireMessagePremiereEtape,
    construirePromptSysteme,
)

# -----------------------------------------------------------------------------
# Constantes generales
# -----------------------------------------------------------------------------

LARGEUR_ECRAN = 1280
HAUTEUR_ECRAN = 720

URL_OLLAMA = os.environ.get("URL_OLLAMA", "http://127.0.0.1:11434")
NOM_MODELE = os.environ.get("NOM_MODELE_LLM", "qwen2.5:0.5b")

NOMBRE_ETAPES = 6  # 5 a 7 selon le cahier de charges, 6 = sweet spot

COULEUR_FOND_HAUT = (250, 244, 226)
COULEUR_FOND_BAS = (236, 224, 196)
COULEUR_TEXTE_PRINCIPAL = (40, 40, 42)
COULEUR_TEXTE_DOUX = (98, 96, 88)
COULEUR_TEXTE_INVERSE = (255, 253, 246)
COULEUR_BANNIERE = (31, 77, 44)
COULEUR_CARTE = (255, 253, 246)
COULEUR_ACTION_SURVOL = (250, 240, 210)
COULEUR_ACTION_BORDURE = (210, 200, 175)
COULEUR_ACCENT = (210, 48, 48)

COULEURS_PAVILLON = {
    "marin": (61, 150, 189),
    "forestier": (130, 160, 76),
    "pollinisateurs": (189, 149, 58),
}

COULEURS_PAVILLON_DOUX = {
    "marin": (188, 220, 234),
    "forestier": (210, 224, 184),
    "pollinisateurs": (234, 218, 174),
}

CHOIX_FALLBACK = ["Continuer prudemment", "Observer la scene", "Demander conseil"]


# -----------------------------------------------------------------------------
# Banniere et polices
# -----------------------------------------------------------------------------

def lireBanniereEnvironnement():
    """Lit les variables d'environnement injectees au build (ARG du Dockerfile)."""
    return {
        "buildDate": os.environ.get("BUILD_DATE", "inconnu"),
        "nomEtudiant": os.environ.get("NOM_ETUDIANT", "anonyme"),
        "matricule": os.environ.get("MATRICULE", "000000"),
    }


def chargerPolices():
    """Charge des polices DejaVu installees dans l'image Docker."""
    return {
        "titre": pygame.font.SysFont("dejavusans", 60, bold=True),
        "sousTitre": pygame.font.SysFont("dejavusans", 26, bold=False),
        "narration": pygame.font.SysFont("dejavusans", 26, bold=False),
        "etiquette": pygame.font.SysFont("dejavusans", 22, bold=True),
        "action": pygame.font.SysFont("dejavusans", 24, bold=False),
        "spinner": pygame.font.SysFont("dejavusans", 30, bold=True),
        "banniere": pygame.font.SysFont("dejavusans", 18, bold=False),
    }


# -----------------------------------------------------------------------------
# Helpers texte
# -----------------------------------------------------------------------------

def afficherTexteCentre(surfaceCible, texte, police, couleur, positionY):
    """Dessine un texte centre horizontalement a la position Y donnee."""
    rendu = police.render(texte, True, couleur)
    rectangle = rendu.get_rect(center=(LARGEUR_ECRAN // 2, positionY))
    surfaceCible.blit(rendu, rectangle)
    return rectangle


def afficherTexteEncadre(surfaceCible, texte, police, couleur, positionX, positionY):
    """Dessine un texte aligne a gauche a la position donnee."""
    rendu = police.render(texte, True, couleur)
    surfaceCible.blit(rendu, (positionX, positionY))
    return rendu.get_rect(topleft=(positionX, positionY))


def couperTexteEnLignes(texte, police, largeurMaximum):
    """Decoupe un texte en plusieurs lignes pour qu'il rentre dans la largeur indiquee.

    Coupe au mot. Si un seul mot deborde (cas rare), on le laisse passer.
    """
    lignes = []
    for paragrapheCourant in texte.split("\n"):
        mots = paragrapheCourant.split(" ")
        ligneCourante = ""
        for unMot in mots:
            candidat = (ligneCourante + " " + unMot).strip()
            if police.size(candidat)[0] <= largeurMaximum:
                ligneCourante = candidat
            else:
                if ligneCourante:
                    lignes.append(ligneCourante)
                ligneCourante = unMot
        if ligneCourante:
            lignes.append(ligneCourante)
    return lignes


def retirerAccents(chaine):
    """Petit filtre defensif. Le prompt demande deja sans accents au LLM,
    mais qwen2.5:0.5b en glisse parfois. On normalise pour la police SDL2."""
    tableTraduction = str.maketrans({
        "a": "a", "a": "a", "a": "a", "a": "a",
        "e": "e", "e": "e", "e": "e", "e": "e",
        "i": "i", "i": "i",
        "o": "o", "o": "o", "o": "o",
        "u": "u", "u": "u", "u": "u",
        "y": "y",
        "c": "c",
        "n": "n",
        "A": "A", "E": "E", "I": "I", "O": "O", "U": "U",
        "C": "C",
    })
    # On cible les vraies diacritiques unicode courantes en francais.
    remplacements = {
        "é": "e", "è": "e", "ê": "e", "ë": "e",
        "à": "a", "â": "a", "ä": "a",
        "î": "i", "ï": "i",
        "ô": "o", "ö": "o",
        "ù": "u", "û": "u", "ü": "u",
        "ÿ": "y",
        "ç": "c",
        "ñ": "n",
        "É": "E", "È": "E", "Ê": "E", "Ë": "E",
        "À": "A", "Â": "A", "Ä": "A",
        "Î": "I", "Ï": "I",
        "Ô": "O", "Ö": "O",
        "Ù": "U", "Û": "U", "Ü": "U",
        "Ç": "C",
        "—": "-", "–": "-",
        "‘": "'", "’": "'",
        "“": '"', "”": '"',
    }
    resultat = []
    for caractere in chaine:
        resultat.append(remplacements.get(caractere, caractere))
    return "".join(resultat)


# -----------------------------------------------------------------------------
# Fond degrade
# -----------------------------------------------------------------------------

def fabriquerFondDegrade(couleurHaut, couleurBas):
    """Pre-rend un degrade vertical de couleurHaut a couleurBas sur la taille ecran."""
    surfaceFond = pygame.Surface((LARGEUR_ECRAN, HAUTEUR_ECRAN))
    for positionY in range(HAUTEUR_ECRAN):
        progression = positionY / (HAUTEUR_ECRAN - 1)
        rouge = int(couleurHaut[0] + (couleurBas[0] - couleurHaut[0]) * progression)
        vert = int(couleurHaut[1] + (couleurBas[1] - couleurHaut[1]) * progression)
        bleu = int(couleurHaut[2] + (couleurBas[2] - couleurHaut[2]) * progression)
        pygame.draw.line(surfaceFond, (rouge, vert, bleu), (0, positionY), (LARGEUR_ECRAN, positionY))
    return surfaceFond


# -----------------------------------------------------------------------------
# Banniere
# -----------------------------------------------------------------------------

def dessinerBanniere(surfaceCible, polices, banniere):
    """Banniere d'identification de la borne en haut de l'ecran."""
    hauteurBanniere = 40
    pygame.draw.rect(surfaceCible, COULEUR_BANNIERE, pygame.Rect(0, 0, LARGEUR_ECRAN, hauteurBanniere))
    texteGauche = "Borne intelligente narrative - Zoo maritime du Bas-Saint-Laurent"
    texteDroite = (
        f"{banniere['nomEtudiant']} - {banniere['matricule']} - build {banniere['buildDate']}"
    )
    afficherTexteEncadre(surfaceCible, texteGauche, polices["banniere"], COULEUR_TEXTE_INVERSE, 18, 10)
    largeurDroite = polices["banniere"].size(texteDroite)[0]
    afficherTexteEncadre(
        surfaceCible, texteDroite, polices["banniere"], COULEUR_TEXTE_INVERSE,
        LARGEUR_ECRAN - largeurDroite - 18, 10,
    )


# -----------------------------------------------------------------------------
# Communication avec ollama
# -----------------------------------------------------------------------------

def appelerLlm(historiqueMessages):
    """Appel synchrone a l'API ollama (non-streaming pour la simplicite).

    Retourne le texte de reponse ou une chaine d'erreur lisible.
    Timeout genereux car le modele 0.5b reste lent au premier prompt.
    """
    corpsRequete = {
        "model": NOM_MODELE,
        "messages": historiqueMessages,
        "stream": False,
        "options": {
            "temperature": 0.8,
            "num_predict": 320,
        },
    }
    try:
        reponse = requests.post(
            URL_OLLAMA + "/api/chat",
            json=corpsRequete,
            timeout=120,
        )
        reponse.raise_for_status()
        donnees = reponse.json()
        texteBrut = donnees.get("message", {}).get("content", "")
        return retirerAccents(texteBrut.strip())
    except requests.exceptions.RequestException as erreur:
        return (
            "[Erreur de communication avec le LLM]\n"
            "L'IA du zoo est temporairement indisponible. "
            "Touche ESC pour fermer ou patiente.\n"
            "Detail technique : " + str(erreur)
        )


def parserReponseLlm(texteBrut, doitContenirChoix):
    """Separe la narration des trois choix A/B/C dans le texte du LLM.

    Retourne (texteNarration, listeChoix). Si doitContenirChoix=False,
    listeChoix est vide. Si le parsing echoue, on remet des choix de fallback.
    """
    if not doitContenirChoix:
        return texteBrut.strip(), []

    # Cherche les lignes qui commencent par A) / B) / C) (eventuellement avec
    # variations : 'A. ', 'A : ', etc. - on tolere mais on extrait le contenu).
    motifChoix = re.compile(
        r"^\s*([ABC])\s*[\)\.\:\-]\s*(.+?)\s*$",
        re.IGNORECASE,
    )

    lignesTexte = texteBrut.split("\n")
    indexPremiereLigneChoix = None
    choixTrouves = {}
    for indexLigne, ligneCourante in enumerate(lignesTexte):
        correspondance = motifChoix.match(ligneCourante)
        if correspondance:
            lettre = correspondance.group(1).upper()
            contenu = correspondance.group(2).strip()
            if contenu and lettre in ("A", "B", "C"):
                choixTrouves[lettre] = contenu
                if indexPremiereLigneChoix is None:
                    indexPremiereLigneChoix = indexLigne

    if len(choixTrouves) == 3 and indexPremiereLigneChoix is not None:
        narration = "\n".join(lignesTexte[:indexPremiereLigneChoix]).strip()
        listeChoix = [choixTrouves["A"], choixTrouves["B"], choixTrouves["C"]]
        return narration, listeChoix

    # Parsing partiel : on garde ce qu'on a, on complete avec le fallback.
    narration = texteBrut.strip()
    listeChoix = []
    for lettre in ("A", "B", "C"):
        if lettre in choixTrouves:
            listeChoix.append(choixTrouves[lettre])
        else:
            listeChoix.append(CHOIX_FALLBACK[len(listeChoix)])
    # Si rien n'a ete trouve, narration = texteBrut entier; ca passe.
    return narration, listeChoix


# -----------------------------------------------------------------------------
# Generation en arriere-plan (thread)
# -----------------------------------------------------------------------------

class GenerateurAventure:
    """Encapsule l'historique de conversation et lance les appels LLM
    dans un thread pour ne pas bloquer la boucle Pygame."""

    def __init__(self):
        self.historiqueMessages = []
        self.fileResultats = queue.Queue()
        self.threadEnCours = None

    def reinitialiser(self, cleEcosysteme):
        """Repart de zero avec un nouveau system prompt."""
        self.historiqueMessages = [
            {
                "role": "system",
                "content": construirePromptSysteme(cleEcosysteme, NOMBRE_ETAPES),
            }
        ]

    def estOccupe(self):
        return self.threadEnCours is not None and self.threadEnCours.is_alive()

    def demanderEtape(self, numeroEtape):
        """Lance la generation d'une etape dans un thread.

        Le resultat (texte narratif + choix) est depose dans self.fileResultats
        que la boucle principale lit a chaque frame.
        """
        if self.estOccupe():
            return
        if numeroEtape == 1:
            messageUtilisateur = construireMessagePremiereEtape(NOMBRE_ETAPES)
        else:
            messageUtilisateur = construireMessageEtape(numeroEtape, NOMBRE_ETAPES)
        self.historiqueMessages.append({"role": "user", "content": messageUtilisateur})

        doitContenirChoix = numeroEtape < NOMBRE_ETAPES
        copieMessages = list(self.historiqueMessages)

        def travail():
            texteBrut = appelerLlm(copieMessages)
            narration, listeChoix = parserReponseLlm(texteBrut, doitContenirChoix)
            self.fileResultats.put({
                "numeroEtape": numeroEtape,
                "texteBrut": texteBrut,
                "narration": narration,
                "choix": listeChoix,
                "estConclusion": not doitContenirChoix,
            })

        self.threadEnCours = threading.Thread(target=travail, daemon=True)
        self.threadEnCours.start()

    def enregistrerReponseAssistant(self, texteBrut):
        """Apres affichage, on memorise la reponse pour l'historique."""
        self.historiqueMessages.append({"role": "assistant", "content": texteBrut})

    def enregistrerChoixUtilisateur(self, lettreChoix, texteChoix):
        """Apres clic du visiteur, on memorise son choix pour l'historique."""
        self.historiqueMessages.append({
            "role": "user",
            "content": f"Le visiteur choisit {lettreChoix}) {texteChoix}.",
        })

    def recupererResultatSiPret(self):
        """Retourne le dict de resultat ou None si rien n'est pret."""
        try:
            return self.fileResultats.get_nowait()
        except queue.Empty:
            return None


# -----------------------------------------------------------------------------
# Ecran : choix de l'ecosysteme
# -----------------------------------------------------------------------------

def calculerRectanglesEcosysteme():
    """Trois grandes cartes cliquables centrees verticalement."""
    largeurCarte = 360
    hauteurCarte = 380
    espace = 30
    largeurTotale = largeurCarte * 3 + espace * 2
    positionXDepart = (LARGEUR_ECRAN - largeurTotale) // 2
    positionY = 200
    rectangles = {}
    for indexCarte, cleEcosysteme in enumerate(("marin", "forestier", "pollinisateurs")):
        positionX = positionXDepart + indexCarte * (largeurCarte + espace)
        rectangles[cleEcosysteme] = pygame.Rect(positionX, positionY, largeurCarte, hauteurCarte)
    return rectangles


def dessinerEcranChoixEcosysteme(surfaceCible, fondPrerendu, polices, banniere,
                                  rectanglesEcosysteme, positionSouris):
    surfaceCible.blit(fondPrerendu["accueil"], (0, 0))
    dessinerBanniere(surfaceCible, polices, banniere)

    afficherTexteCentre(
        surfaceCible, "Quel pavillon veux-tu soigner ?",
        polices["titre"], COULEUR_TEXTE_PRINCIPAL, 120,
    )
    afficherTexteCentre(
        surfaceCible,
        "Une mini-aventure generee en direct par l'IA du zoo",
        polices["sousTitre"], COULEUR_TEXTE_DOUX, 170,
    )

    for cleEcosysteme, rectangleCarte in rectanglesEcosysteme.items():
        donneesEcosysteme = ECOSYSTEMES[cleEcosysteme]
        couleurAccent = COULEURS_PAVILLON[cleEcosysteme]
        couleurDouce = COULEURS_PAVILLON_DOUX[cleEcosysteme]

        couleurFond = couleurDouce
        if rectangleCarte.collidepoint(positionSouris):
            couleurFond = COULEUR_ACTION_SURVOL

        pygame.draw.rect(surfaceCible, couleurFond, rectangleCarte, border_radius=18)
        pygame.draw.rect(surfaceCible, couleurAccent, rectangleCarte, width=4, border_radius=18)

        # Bandeau colore en haut de la carte
        pygame.draw.rect(
            surfaceCible, couleurAccent,
            pygame.Rect(rectangleCarte.x, rectangleCarte.y, rectangleCarte.width, 60),
            border_top_left_radius=18, border_top_right_radius=18,
        )
        rendu = polices["etiquette"].render(
            donneesEcosysteme["titrePavillon"].upper(), True, COULEUR_TEXTE_INVERSE,
        )
        rectangleEtiquette = rendu.get_rect(
            center=(rectangleCarte.centerx, rectangleCarte.y + 30),
        )
        surfaceCible.blit(rendu, rectangleEtiquette)

        # Description courte
        lignesDescription = couperTexteEnLignes(
            donneesEcosysteme["descriptionCourte"],
            polices["sousTitre"],
            rectangleCarte.width - 40,
        )
        positionYTexte = rectangleCarte.y + 90
        for uneLigne in lignesDescription:
            rendu = polices["sousTitre"].render(uneLigne, True, COULEUR_TEXTE_PRINCIPAL)
            rectangleTexte = rendu.get_rect(
                center=(rectangleCarte.centerx, positionYTexte),
            )
            surfaceCible.blit(rendu, rectangleTexte)
            positionYTexte += 32

        # Liste des especes
        positionYTexte = rectangleCarte.y + 170
        for nomEspece in donneesEcosysteme["especes"]:
            rendu = polices["action"].render("- " + nomEspece, True, COULEUR_TEXTE_DOUX)
            surfaceCible.blit(rendu, (rectangleCarte.x + 30, positionYTexte))
            positionYTexte += 32

        afficherTexteCentre(
            surfaceCible, "Touche pour incarner",
            polices["banniere"], couleurAccent,
            rectangleCarte.bottom - 24,
        )

    afficherTexteCentre(
        surfaceCible,
        "ESC pour quitter - clic ou tactile pour choisir",
        polices["banniere"], COULEUR_TEXTE_DOUX,
        HAUTEUR_ECRAN - 30,
    )


# -----------------------------------------------------------------------------
# Ecran : aventure (etape narrative + 3 actions)
# -----------------------------------------------------------------------------

CARTE_LARGEUR = 1100
CARTE_POSITION_X = (LARGEUR_ECRAN - CARTE_LARGEUR) // 2
CARTE_POSITION_Y = 80
CARTE_HAUTEUR_NARRATION = 320

ACTION_HAUTEUR = 76
ACTION_ESPACE = 14
ACTION_LARGEUR = CARTE_LARGEUR


def calculerRectanglesActions():
    """Trois rectangles d'action sous la carte de narration."""
    rectangles = []
    positionYDebut = CARTE_POSITION_Y + CARTE_HAUTEUR_NARRATION + 30
    for indexAction in range(3):
        positionY = positionYDebut + indexAction * (ACTION_HAUTEUR + ACTION_ESPACE)
        rectangles.append(pygame.Rect(
            CARTE_POSITION_X, positionY, ACTION_LARGEUR, ACTION_HAUTEUR,
        ))
    return rectangles


def dessinerCarteNarration(surfaceCible, couleurAccent):
    """Carte centrale qui contient le texte narratif."""
    rectangleCarte = pygame.Rect(
        CARTE_POSITION_X, CARTE_POSITION_Y, CARTE_LARGEUR, CARTE_HAUTEUR_NARRATION,
    )
    # Ombre douce
    surfaceOmbre = pygame.Surface(
        (CARTE_LARGEUR + 20, CARTE_HAUTEUR_NARRATION + 20), pygame.SRCALPHA,
    )
    for indexCouche in range(6):
        decalage = indexCouche * 2
        opacite = 12 - indexCouche * 2
        pygame.draw.rect(
            surfaceOmbre, (0, 0, 0, max(0, opacite)),
            pygame.Rect(decalage, decalage,
                        CARTE_LARGEUR + 20 - decalage * 2,
                        CARTE_HAUTEUR_NARRATION + 20 - decalage * 2),
            border_radius=18,
        )
    surfaceCible.blit(surfaceOmbre, (CARTE_POSITION_X - 10, CARTE_POSITION_Y - 6))

    pygame.draw.rect(surfaceCible, COULEUR_CARTE, rectangleCarte, border_radius=16)
    # Bandeau colore vertical a gauche
    pygame.draw.rect(
        surfaceCible, couleurAccent,
        pygame.Rect(CARTE_POSITION_X, CARTE_POSITION_Y, 10, CARTE_HAUTEUR_NARRATION),
        border_top_left_radius=16, border_bottom_left_radius=16,
    )
    return rectangleCarte


def dessinerSpinner(surfaceCible, polices, tempsTotal):
    """Affiche 'L'IA reflechit...' avec un petit point qui pulse."""
    nombrePointsAnimes = int((tempsTotal * 2) % 4)
    suffixe = "." * nombrePointsAnimes
    afficherTexteCentre(
        surfaceCible,
        "L'IA reflechit" + suffixe,
        polices["spinner"], COULEUR_ACCENT,
        CARTE_POSITION_Y + CARTE_HAUTEUR_NARRATION // 2,
    )


def dessinerEcranAventure(surfaceCible, fondPrerendu, polices, banniere,
                           cleEcosysteme, numeroEtape, etatEtape,
                           rectanglesActions, positionSouris, tempsTotal):
    """etatEtape contient : narration, choix, enAttente (bool), estConclusion (bool)."""
    surfaceCible.blit(fondPrerendu[cleEcosysteme], (0, 0))
    dessinerBanniere(surfaceCible, polices, banniere)

    couleurAccent = COULEURS_PAVILLON[cleEcosysteme]

    # Indicateur d'etape
    titrePavillon = ECOSYSTEMES[cleEcosysteme]["titrePavillon"]
    afficherTexteEncadre(
        surfaceCible, titrePavillon,
        polices["etiquette"], couleurAccent,
        CARTE_POSITION_X, CARTE_POSITION_Y - 36,
    )
    texteEtape = "Etape " + str(numeroEtape) + " sur " + str(NOMBRE_ETAPES)
    rendu = polices["etiquette"].render(texteEtape, True, couleurAccent)
    surfaceCible.blit(
        rendu,
        (CARTE_POSITION_X + CARTE_LARGEUR - rendu.get_width(), CARTE_POSITION_Y - 36),
    )

    dessinerCarteNarration(surfaceCible, couleurAccent)

    if etatEtape["enAttente"]:
        dessinerSpinner(surfaceCible, polices, tempsTotal)
        return

    # Texte narratif
    lignesNarration = couperTexteEnLignes(
        etatEtape["narration"], polices["narration"], CARTE_LARGEUR - 80,
    )
    positionYTexte = CARTE_POSITION_Y + 30
    hauteurMaximumTexte = CARTE_HAUTEUR_NARRATION - 40
    hauteurLigne = 34
    nombreLignesAffichables = max(1, hauteurMaximumTexte // hauteurLigne)
    for uneLigne in lignesNarration[:nombreLignesAffichables]:
        rendu = polices["narration"].render(uneLigne, True, COULEUR_TEXTE_PRINCIPAL)
        surfaceCible.blit(rendu, (CARTE_POSITION_X + 40, positionYTexte))
        positionYTexte += hauteurLigne

    if etatEtape["estConclusion"]:
        # Pas de choix : un grand bouton "Recommencer" centre.
        largeurAction = 480
        rectangleAction = pygame.Rect(
            (LARGEUR_ECRAN - largeurAction) // 2,
            CARTE_POSITION_Y + CARTE_HAUTEUR_NARRATION + 60,
            largeurAction, 80,
        )
        couleurBouton = couleurAccent
        if rectangleAction.collidepoint(positionSouris):
            couleurBouton = COULEUR_ACCENT
        pygame.draw.rect(surfaceCible, couleurBouton, rectangleAction, border_radius=18)
        afficherTexteCentre(
            surfaceCible, "Recommencer une nouvelle aventure",
            polices["action"], COULEUR_TEXTE_INVERSE,
            rectangleAction.centery,
        )
        # On stocke le rectangle pour la detection de clic via etatEtape.
        etatEtape["rectangleRecommencer"] = rectangleAction
        return

    # Trois actions cliquables
    listeChoix = etatEtape["choix"]
    for indexAction, rectangleAction in enumerate(rectanglesActions):
        couleurFond = COULEUR_CARTE
        couleurBordure = COULEUR_ACTION_BORDURE
        if rectangleAction.collidepoint(positionSouris):
            couleurFond = COULEUR_ACTION_SURVOL
            couleurBordure = couleurAccent
        pygame.draw.rect(surfaceCible, couleurFond, rectangleAction, border_radius=14)
        pygame.draw.rect(surfaceCible, couleurBordure, rectangleAction, width=2, border_radius=14)

        lettreChoix = ("A", "B", "C")[indexAction]
        texteChoix = listeChoix[indexAction] if indexAction < len(listeChoix) else CHOIX_FALLBACK[indexAction]
        texteAffiche = lettreChoix + ")  " + texteChoix
        # Coupe en lignes pour les choix longs.
        lignesAction = couperTexteEnLignes(
            texteAffiche, polices["action"], rectangleAction.width - 40,
        )
        positionYAction = (
            rectangleAction.centery - (len(lignesAction) - 1) * 14
        )
        for uneLigne in lignesAction[:2]:
            rendu = polices["action"].render(uneLigne, True, COULEUR_TEXTE_PRINCIPAL)
            rectangleTexte = rendu.get_rect(
                midleft=(rectangleAction.x + 30, positionYAction),
            )
            surfaceCible.blit(rendu, rectangleTexte)
            positionYAction += 28


# -----------------------------------------------------------------------------
# Boucle principale
# -----------------------------------------------------------------------------

def boucleBorne():
    pygame.init()
    surfaceEcran = pygame.display.set_mode((LARGEUR_ECRAN, HAUTEUR_ECRAN))
    pygame.display.set_caption("Borne intelligente narrative - Zoo maritime")
    horloge = pygame.time.Clock()

    polices = chargerPolices()
    banniere = lireBanniereEnvironnement()
    rectanglesEcosysteme = calculerRectanglesEcosysteme()
    rectanglesActions = calculerRectanglesActions()

    fondPrerendu = {
        "accueil": fabriquerFondDegrade(COULEUR_FOND_HAUT, COULEUR_FOND_BAS),
    }
    for clePavillon, couleurDouce in COULEURS_PAVILLON_DOUX.items():
        fondPrerendu[clePavillon] = fabriquerFondDegrade(couleurDouce, COULEUR_FOND_BAS)

    generateur = GenerateurAventure()
    etatCourant = "choix-ecosysteme"
    cleEcosystemeChoisi = None
    numeroEtape = 0
    etatEtape = {
        "narration": "",
        "choix": [],
        "enAttente": False,
        "estConclusion": False,
        "rectangleRecommencer": None,
    }
    tempsTotal = 0.0

    def commencerAventure(cleEcosysteme):
        nonlocal etatCourant, cleEcosystemeChoisi, numeroEtape, etatEtape
        cleEcosystemeChoisi = cleEcosysteme
        numeroEtape = 1
        etatCourant = "aventure"
        etatEtape = {
            "narration": "",
            "choix": [],
            "enAttente": True,
            "estConclusion": False,
            "rectangleRecommencer": None,
        }
        generateur.reinitialiser(cleEcosysteme)
        generateur.demanderEtape(numeroEtape)

    def passerEtapeSuivante(lettreChoix, texteChoix):
        nonlocal numeroEtape, etatEtape
        if etatEtape["enAttente"]:
            return
        # Memorise le choix dans l'historique LLM.
        generateur.enregistrerChoixUtilisateur(lettreChoix, texteChoix)
        numeroEtape += 1
        etatEtape = {
            "narration": "",
            "choix": [],
            "enAttente": True,
            "estConclusion": False,
            "rectangleRecommencer": None,
        }
        generateur.demanderEtape(numeroEtape)

    def revenirAuChoixEcosysteme():
        nonlocal etatCourant, cleEcosystemeChoisi, numeroEtape, etatEtape
        etatCourant = "choix-ecosysteme"
        cleEcosystemeChoisi = None
        numeroEtape = 0
        etatEtape = {
            "narration": "",
            "choix": [],
            "enAttente": False,
            "estConclusion": False,
            "rectangleRecommencer": None,
        }

    while True:
        deltaTemps = horloge.tick(60) / 1000.0
        tempsTotal += deltaTemps

        # Recuperation des resultats de generation LLM.
        resultatPret = generateur.recupererResultatSiPret()
        if resultatPret is not None:
            generateur.enregistrerReponseAssistant(resultatPret["texteBrut"])
            etatEtape["narration"] = resultatPret["narration"]
            etatEtape["choix"] = resultatPret["choix"]
            etatEtape["estConclusion"] = resultatPret["estConclusion"]
            etatEtape["enAttente"] = False

        for evenement in pygame.event.get():
            if evenement.type == pygame.QUIT:
                pygame.quit()
                return
            if evenement.type == pygame.KEYDOWN:
                if evenement.key == pygame.K_ESCAPE:
                    pygame.quit()
                    return
                if etatCourant == "aventure" and not etatEtape["enAttente"]:
                    if etatEtape["estConclusion"]:
                        if evenement.key == pygame.K_SPACE:
                            revenirAuChoixEcosysteme()
                    else:
                        toucheVersIndex = {
                            pygame.K_a: 0, pygame.K_1: 0,
                            pygame.K_b: 1, pygame.K_2: 1,
                            pygame.K_c: 2, pygame.K_3: 2,
                        }
                        if evenement.key in toucheVersIndex:
                            indexChoixSelectionne = toucheVersIndex[evenement.key]
                            lettreChoix = ("A", "B", "C")[indexChoixSelectionne]
                            texteChoix = (
                                etatEtape["choix"][indexChoixSelectionne]
                                if indexChoixSelectionne < len(etatEtape["choix"])
                                else CHOIX_FALLBACK[indexChoixSelectionne]
                            )
                            passerEtapeSuivante(lettreChoix, texteChoix)
            if evenement.type == pygame.MOUSEBUTTONDOWN and evenement.button == 1:
                if etatCourant == "choix-ecosysteme":
                    for cleEcosysteme, rectangleCarte in rectanglesEcosysteme.items():
                        if rectangleCarte.collidepoint(evenement.pos):
                            commencerAventure(cleEcosysteme)
                            break
                elif etatCourant == "aventure" and not etatEtape["enAttente"]:
                    if etatEtape["estConclusion"]:
                        rectangleRecommencer = etatEtape.get("rectangleRecommencer")
                        if rectangleRecommencer is not None and rectangleRecommencer.collidepoint(evenement.pos):
                            revenirAuChoixEcosysteme()
                    else:
                        for indexAction, rectangleAction in enumerate(rectanglesActions):
                            if rectangleAction.collidepoint(evenement.pos):
                                lettreChoix = ("A", "B", "C")[indexAction]
                                texteChoix = (
                                    etatEtape["choix"][indexAction]
                                    if indexAction < len(etatEtape["choix"])
                                    else CHOIX_FALLBACK[indexAction]
                                )
                                passerEtapeSuivante(lettreChoix, texteChoix)
                                break

        positionSouris = pygame.mouse.get_pos()

        if etatCourant == "choix-ecosysteme":
            dessinerEcranChoixEcosysteme(
                surfaceEcran, fondPrerendu, polices, banniere,
                rectanglesEcosysteme, positionSouris,
            )
        elif etatCourant == "aventure":
            dessinerEcranAventure(
                surfaceEcran, fondPrerendu, polices, banniere,
                cleEcosystemeChoisi, numeroEtape, etatEtape,
                rectanglesActions, positionSouris, tempsTotal,
            )

        pygame.display.flip()


if __name__ == "__main__":
    try:
        boucleBorne()
    except pygame.error as erreur:
        print(
            "Pygame n'a pas pu demarrer. Verifie que DISPLAY est partage avec le container.\n"
            f"Detail : {erreur}",
            file=sys.stderr,
        )
        sys.exit(1)
