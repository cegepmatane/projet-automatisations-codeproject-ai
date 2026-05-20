"""
Borne intelligente Q&A - Pygame + LLM local (ollama)
Zoo maritime du Bas-Saint-Laurent

Application kiosque qui propose une liste de questions predefinies sur les
especes du zoo. Au clic, un thread interroge le LLM local (ollama, modele
qwen2.5:0.5b) en mode streaming. Les jetons recus sont accumules dans un
buffer partage que la boucle Pygame redessine 30 fois par seconde, donnant
un effet de reponse qui s'ecrit sous les yeux du visiteur.

Aucun port reseau n'est expose : ollama tourne en localhost dans le meme
container que Pygame. La fenetre s'affiche sur le DISPLAY X11 de l'hote.
"""

import json
import os
import sys
import threading
import time

import pygame
import requests

from questions import (
    COULEURS_ECOSYSTEME,
    FICHES_ESPECE,
    NOMS_ECOSYSTEME,
    QUESTIONS_PROPOSEES,
    construireContexteEspece,
)

# -----------------------------------------------------------------------------
# Constantes d'affichage
# -----------------------------------------------------------------------------

LARGEUR_ECRAN = 1280
HAUTEUR_ECRAN = 720

COULEUR_FOND_HAUT = (250, 244, 226)
COULEUR_FOND_BAS = (236, 224, 196)
COULEUR_TEXTE_PRINCIPAL = (40, 40, 42)
COULEUR_TEXTE_DOUX = (98, 96, 88)
COULEUR_TEXTE_INVERSE = (255, 253, 246)
COULEUR_BANNIERE = (31, 77, 44)
COULEUR_CARTE = (255, 253, 246)
COULEUR_CARTE_BORDURE = (210, 200, 175)
COULEUR_CARTE_SURVOL = (250, 240, 210)
COULEUR_ACCENT = (210, 48, 48)

# -----------------------------------------------------------------------------
# Configuration LLM ollama
# -----------------------------------------------------------------------------

URL_API_OLLAMA = "http://127.0.0.1:11434"
MODELE_LLM = os.environ.get("MODELE_LLM", "qwen2.5:0.5b")
DUREE_MAXIMUM_REPONSE_SECONDES = 60
SYSTEM_PROMPT = (
    "Tu es la borne intelligente du Zoo maritime du Bas-Saint-Laurent. "
    "Tu reponds aux visiteurs (familles, enfants) en francais sans accents. "
    "Reponds en 2 a 3 phrases courtes, ton accessible et chaleureux. "
    "Ne fais pas de listes, pas de titres, pas de markdown. "
    "Si l'information n'est pas dans le contexte fourni, dis-le simplement."
)


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
        "titre": pygame.font.SysFont("dejavusans", 56, bold=True),
        "sousTitre": pygame.font.SysFont("dejavusans", 26, bold=False),
        "question": pygame.font.SysFont("dejavusans", 22, bold=True),
        "questionLarge": pygame.font.SysFont("dejavusans", 28, bold=True),
        "reponse": pygame.font.SysFont("dejavusans", 26, bold=False),
        "etiquette": pygame.font.SysFont("dejavusans", 16, bold=True),
        "banniere": pygame.font.SysFont("dejavusans", 18, bold=False),
        "action": pygame.font.SysFont("dejavusans", 24, bold=True),
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
    """Decoupe un texte en plusieurs lignes pour qu'il rentre dans la largeur indiquee."""
    lignes = []
    for paragraphe in texte.split("\n"):
        mots = paragraphe.split(" ")
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
        if not mots:
            lignes.append("")
    return lignes


# -----------------------------------------------------------------------------
# Fond
# -----------------------------------------------------------------------------

def fabriquerFondDegrade(couleurHaut, couleurBas):
    """Pre-rend un degrade vertical de couleurHaut a couleurBas sur la taille ecran."""
    surfaceFond = pygame.Surface((LARGEUR_ECRAN, HAUTEUR_ECRAN))
    for positionY in range(HAUTEUR_ECRAN):
        progression = positionY / (HAUTEUR_ECRAN - 1)
        rouge = int(couleurHaut[0] + (couleurBas[0] - couleurHaut[0]) * progression)
        vert = int(couleurHaut[1] + (couleurBas[1] - couleurHaut[1]) * progression)
        bleu = int(couleurHaut[2] + (couleurBas[2] - couleurHaut[2]) * progression)
        pygame.draw.line(
            surfaceFond, (rouge, vert, bleu), (0, positionY), (LARGEUR_ECRAN, positionY)
        )
    return surfaceFond


# -----------------------------------------------------------------------------
# Banniere
# -----------------------------------------------------------------------------

def dessinerBanniere(surfaceCible, polices, banniere):
    """Banniere d'identification en haut de l'ecran."""
    hauteurBanniere = 40
    pygame.draw.rect(
        surfaceCible, COULEUR_BANNIERE, pygame.Rect(0, 0, LARGEUR_ECRAN, hauteurBanniere)
    )
    texteGauche = "Borne intelligente - Q&A du Zoo maritime du Bas-Saint-Laurent"
    texteDroite = (
        f"{banniere['nomEtudiant']} - {banniere['matricule']} - build {banniere['buildDate']}"
    )
    afficherTexteEncadre(
        surfaceCible, texteGauche, polices["banniere"],
        COULEUR_TEXTE_INVERSE, 18, 10,
    )
    largeurDroite = polices["banniere"].size(texteDroite)[0]
    afficherTexteEncadre(
        surfaceCible, texteDroite, polices["banniere"],
        COULEUR_TEXTE_INVERSE, LARGEUR_ECRAN - largeurDroite - 18, 10,
    )


# -----------------------------------------------------------------------------
# Communication LLM (ollama) en streaming
# -----------------------------------------------------------------------------

def modeleEstPret():
    """Verifie via /api/tags si le modele cible est deja pull dans ollama."""
    try:
        reponseHttp = requests.get(f"{URL_API_OLLAMA}/api/tags", timeout=2)
        if reponseHttp.status_code != 200:
            return False
        donnees = reponseHttp.json()
        for unModele in donnees.get("models", []):
            nomModele = unModele.get("name", "")
            if nomModele.startswith(MODELE_LLM):
                return True
        return False
    except (requests.RequestException, ValueError):
        return False


class GenerationLlm:
    """
    Encapsule un appel streaming a ollama. Le buffer de texte est protege
    par un verrou pour permettre a la boucle Pygame de le lire sans risquer
    une concurrence avec le thread de generation.
    """

    def __init__(self, question, contexteEspece):
        self.question = question
        self.contexteEspece = contexteEspece
        self._verrou = threading.Lock()
        self._tampon = ""
        self._terminee = False
        self._erreur = None
        self._thread = threading.Thread(target=self._executer, daemon=True)

    def demarrer(self):
        self._thread.start()

    def _executer(self):
        contenuUtilisateur = (
            f"Contexte fourni : {self.contexteEspece}\n\n"
            f"Question du visiteur : {self.question}"
        )
        corpsRequete = {
            "model": MODELE_LLM,
            "stream": True,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": contenuUtilisateur},
            ],
            "options": {
                "temperature": 0.4,
                "num_predict": 220,
            },
        }
        try:
            reponseHttp = requests.post(
                f"{URL_API_OLLAMA}/api/chat",
                json=corpsRequete,
                stream=True,
                timeout=DUREE_MAXIMUM_REPONSE_SECONDES,
            )
            if reponseHttp.status_code != 200:
                self._signalerErreur(
                    f"ollama a repondu code {reponseHttp.status_code}"
                )
                return
            for ligneBrute in reponseHttp.iter_lines(decode_unicode=True):
                if not ligneBrute:
                    continue
                try:
                    paquet = json.loads(ligneBrute)
                except ValueError:
                    continue
                jeton = paquet.get("message", {}).get("content", "")
                if jeton:
                    with self._verrou:
                        self._tampon += jeton
                if paquet.get("done"):
                    break
        except requests.RequestException as erreurReseau:
            self._signalerErreur(f"erreur reseau ollama : {erreurReseau}")
            return
        finally:
            with self._verrou:
                self._terminee = True

    def _signalerErreur(self, message):
        with self._verrou:
            self._erreur = message
            self._terminee = True

    def lireTampon(self):
        with self._verrou:
            return self._tampon

    def estTerminee(self):
        with self._verrou:
            return self._terminee

    def lireErreur(self):
        with self._verrou:
            return self._erreur


# -----------------------------------------------------------------------------
# Layout : cartes de questions
# -----------------------------------------------------------------------------

CARTE_LARGEUR = 580
CARTE_HAUTEUR = 78
CARTE_ESPACE_HORIZONTAL = 30
CARTE_ESPACE_VERTICAL = 14
CARTE_DEPART_Y = 130


def calculerRectanglesQuestions():
    """Place les 12 questions en deux colonnes de six cartes."""
    rectangles = []
    largeurDeuxColonnes = CARTE_LARGEUR * 2 + CARTE_ESPACE_HORIZONTAL
    positionXGauche = (LARGEUR_ECRAN - largeurDeuxColonnes) // 2
    positionXDroite = positionXGauche + CARTE_LARGEUR + CARTE_ESPACE_HORIZONTAL
    for indexQuestion in range(len(QUESTIONS_PROPOSEES)):
        colonne = indexQuestion % 2
        ligne = indexQuestion // 2
        positionX = positionXGauche if colonne == 0 else positionXDroite
        positionY = CARTE_DEPART_Y + ligne * (CARTE_HAUTEUR + CARTE_ESPACE_VERTICAL)
        rectangles.append(
            pygame.Rect(positionX, positionY, CARTE_LARGEUR, CARTE_HAUTEUR)
        )
    return rectangles


# -----------------------------------------------------------------------------
# Ecran : liste de questions
# -----------------------------------------------------------------------------

def dessinerEcranListeQuestions(
    surfaceCible,
    fondPrerendu,
    polices,
    banniere,
    rectanglesQuestions,
    positionSouris,
    modeleDisponible,
):
    surfaceCible.blit(fondPrerendu, (0, 0))
    dessinerBanniere(surfaceCible, polices, banniere)

    afficherTexteCentre(
        surfaceCible,
        "Pose une question sur la faune du Saint-Laurent",
        polices["sousTitre"],
        COULEUR_TEXTE_PRINCIPAL,
        80,
    )

    if not modeleDisponible:
        rectangleAttente = pygame.Rect(
            (LARGEUR_ECRAN - 720) // 2, HAUTEUR_ECRAN - 80, 720, 50,
        )
        pygame.draw.rect(
            surfaceCible, COULEUR_ACCENT, rectangleAttente, border_radius=12,
        )
        afficherTexteCentre(
            surfaceCible,
            "Modele en cours de chargement, merci de patienter...",
            polices["action"],
            COULEUR_TEXTE_INVERSE,
            rectangleAttente.centery,
        )

    for indexQuestion, unRectangle in enumerate(rectanglesQuestions):
        questionCourante = QUESTIONS_PROPOSEES[indexQuestion]
        cleEspece = questionCourante["cleEspece"]
        ecosysteme = FICHES_ESPECE[cleEspece]["ecosysteme"]
        couleurAccent = COULEURS_ECOSYSTEME[ecosysteme]

        survol = unRectangle.collidepoint(positionSouris) and modeleDisponible
        couleurFond = COULEUR_CARTE_SURVOL if survol else COULEUR_CARTE
        couleurBordure = couleurAccent if survol else COULEUR_CARTE_BORDURE

        pygame.draw.rect(surfaceCible, couleurFond, unRectangle, border_radius=12)
        pygame.draw.rect(
            surfaceCible, couleurBordure, unRectangle, width=2, border_radius=12,
        )
        # Bandeau d'ecosysteme a gauche.
        pygame.draw.rect(
            surfaceCible,
            couleurAccent,
            pygame.Rect(unRectangle.left, unRectangle.top, 8, unRectangle.height),
            border_top_left_radius=12,
            border_bottom_left_radius=12,
        )
        # Etiquette d'ecosysteme.
        afficherTexteEncadre(
            surfaceCible,
            NOMS_ECOSYSTEME[ecosysteme].upper(),
            polices["etiquette"],
            couleurAccent,
            unRectangle.left + 24,
            unRectangle.top + 12,
        )
        # Texte de la question (eventuellement coupe sur deux lignes).
        lignesQuestion = couperTexteEnLignes(
            questionCourante["enonce"],
            polices["question"],
            CARTE_LARGEUR - 48,
        )
        positionYTexte = unRectangle.top + 36
        for uneLigne in lignesQuestion[:2]:
            afficherTexteEncadre(
                surfaceCible,
                uneLigne,
                polices["question"],
                COULEUR_TEXTE_PRINCIPAL,
                unRectangle.left + 24,
                positionYTexte,
            )
            positionYTexte += 22

    afficherTexteCentre(
        surfaceCible,
        "Touche une carte pour interroger l'IA. ESC pour quitter.",
        polices["banniere"],
        COULEUR_TEXTE_DOUX,
        HAUTEUR_ECRAN - 18,
    )


# -----------------------------------------------------------------------------
# Ecran : reponse en streaming
# -----------------------------------------------------------------------------

RECTANGLE_RETOUR = pygame.Rect(
    (LARGEUR_ECRAN - 360) // 2, HAUTEUR_ECRAN - 80, 360, 56,
)


def dessinerEcranReponse(
    surfaceCible,
    fondPrerendu,
    polices,
    banniere,
    questionAffichee,
    cleEspece,
    texteReponse,
    generationTerminee,
    messageErreur,
    positionSouris,
):
    surfaceCible.blit(fondPrerendu, (0, 0))
    dessinerBanniere(surfaceCible, polices, banniere)

    ecosysteme = FICHES_ESPECE[cleEspece]["ecosysteme"]
    couleurAccent = COULEURS_ECOSYSTEME[ecosysteme]

    # Carte d'en-tete : etiquette ecosysteme + question.
    rectangleEntete = pygame.Rect(60, 70, LARGEUR_ECRAN - 120, 110)
    pygame.draw.rect(surfaceCible, COULEUR_CARTE, rectangleEntete, border_radius=14)
    pygame.draw.rect(
        surfaceCible, COULEUR_CARTE_BORDURE, rectangleEntete, width=2, border_radius=14,
    )
    pygame.draw.rect(
        surfaceCible,
        couleurAccent,
        pygame.Rect(rectangleEntete.left, rectangleEntete.top, 10, rectangleEntete.height),
        border_top_left_radius=14,
        border_bottom_left_radius=14,
    )
    afficherTexteEncadre(
        surfaceCible,
        NOMS_ECOSYSTEME[ecosysteme].upper(),
        polices["etiquette"],
        couleurAccent,
        rectangleEntete.left + 28,
        rectangleEntete.top + 14,
    )
    lignesQuestion = couperTexteEnLignes(
        questionAffichee, polices["questionLarge"], rectangleEntete.width - 56
    )
    positionYQuestion = rectangleEntete.top + 40
    for uneLigne in lignesQuestion[:3]:
        afficherTexteEncadre(
            surfaceCible,
            uneLigne,
            polices["questionLarge"],
            COULEUR_TEXTE_PRINCIPAL,
            rectangleEntete.left + 28,
            positionYQuestion,
        )
        positionYQuestion += 30

    # Carte de reponse : texte streaming.
    rectangleReponse = pygame.Rect(60, 200, LARGEUR_ECRAN - 120, 380)
    pygame.draw.rect(surfaceCible, COULEUR_CARTE, rectangleReponse, border_radius=14)
    pygame.draw.rect(
        surfaceCible, COULEUR_CARTE_BORDURE, rectangleReponse, width=2, border_radius=14,
    )

    if messageErreur:
        texteAffiche = (
            "Desole, l'assistant n'a pas pu repondre. Reessaie dans un instant.\n"
            f"Detail technique : {messageErreur}"
        )
        couleurTexteReponse = COULEUR_ACCENT
    elif texteReponse.strip():
        texteAffiche = texteReponse
        couleurTexteReponse = COULEUR_TEXTE_PRINCIPAL
    else:
        texteAffiche = "L'IA reflechit..."
        couleurTexteReponse = COULEUR_TEXTE_DOUX

    lignesReponse = couperTexteEnLignes(
        texteAffiche, polices["reponse"], rectangleReponse.width - 56,
    )
    positionYReponse = rectangleReponse.top + 30
    hauteurLigne = 32
    nombreLignesMax = (rectangleReponse.height - 60) // hauteurLigne
    # Si la reponse depasse, on garde les dernieres lignes (effet console qui defile).
    lignesAffichables = lignesReponse[-nombreLignesMax:]
    for uneLigne in lignesAffichables:
        afficherTexteEncadre(
            surfaceCible,
            uneLigne,
            polices["reponse"],
            couleurTexteReponse,
            rectangleReponse.left + 28,
            positionYReponse,
        )
        positionYReponse += hauteurLigne

    # Curseur clignotant pendant la generation.
    if not generationTerminee and not messageErreur and texteReponse.strip():
        clignote = int(time.time() * 2) % 2 == 0
        if clignote and lignesAffichables:
            largeurDerniere = polices["reponse"].size(lignesAffichables[-1])[0]
            curseurX = rectangleReponse.left + 28 + largeurDerniere + 4
            curseurY = positionYReponse - hauteurLigne
            pygame.draw.rect(
                surfaceCible,
                COULEUR_TEXTE_PRINCIPAL,
                pygame.Rect(curseurX, curseurY + 4, 12, 22),
            )

    # Action de retour.
    survolRetour = RECTANGLE_RETOUR.collidepoint(positionSouris)
    couleurRetour = COULEUR_ACCENT if survolRetour else COULEUR_BANNIERE
    pygame.draw.rect(
        surfaceCible, couleurRetour, RECTANGLE_RETOUR, border_radius=14,
    )
    afficherTexteCentre(
        surfaceCible,
        "Retour aux questions",
        polices["action"],
        COULEUR_TEXTE_INVERSE,
        RECTANGLE_RETOUR.centery,
    )

    afficherTexteCentre(
        surfaceCible,
        "ESC pour quitter la borne.",
        polices["banniere"],
        COULEUR_TEXTE_DOUX,
        HAUTEUR_ECRAN - 18,
    )


# -----------------------------------------------------------------------------
# Boucle principale
# -----------------------------------------------------------------------------

def boucleBorne():
    pygame.init()
    surfaceEcran = pygame.display.set_mode((LARGEUR_ECRAN, HAUTEUR_ECRAN))
    pygame.display.set_caption("Borne intelligente - Q&A du zoo maritime")
    horloge = pygame.time.Clock()

    polices = chargerPolices()
    banniere = lireBanniereEnvironnement()
    rectanglesQuestions = calculerRectanglesQuestions()
    fondPrerendu = fabriquerFondDegrade(COULEUR_FOND_HAUT, COULEUR_FOND_BAS)

    etatCourant = "liste"
    generationCourante = None
    indexQuestionActive = None
    modeleDisponible = False
    dernierVerificationModele = 0.0

    while True:
        deltaTemps = horloge.tick(30) / 1000.0
        tempsCourant = time.time()

        # Verifie periodiquement si le modele est pret (toutes les 2 s tant
        # qu'il ne l'est pas, sinon plus rarement pour eviter de spammer).
        intervalleCheck = 2.0 if not modeleDisponible else 15.0
        if tempsCourant - dernierVerificationModele > intervalleCheck:
            modeleDisponible = modeleEstPret()
            dernierVerificationModele = tempsCourant

        for evenement in pygame.event.get():
            if evenement.type == pygame.QUIT:
                pygame.quit()
                return
            if evenement.type == pygame.KEYDOWN:
                if evenement.key == pygame.K_ESCAPE:
                    pygame.quit()
                    return
            if evenement.type == pygame.MOUSEBUTTONDOWN and evenement.button == 1:
                if etatCourant == "liste":
                    if not modeleDisponible:
                        continue
                    for indexCarte, unRectangle in enumerate(rectanglesQuestions):
                        if unRectangle.collidepoint(evenement.pos):
                            indexQuestionActive = indexCarte
                            questionDeclenchee = QUESTIONS_PROPOSEES[indexCarte]
                            generationCourante = GenerationLlm(
                                questionDeclenchee["enonce"],
                                construireContexteEspece(
                                    questionDeclenchee["cleEspece"]
                                ),
                            )
                            generationCourante.demarrer()
                            etatCourant = "reponse"
                            break
                elif etatCourant == "reponse":
                    if RECTANGLE_RETOUR.collidepoint(evenement.pos):
                        etatCourant = "liste"
                        generationCourante = None
                        indexQuestionActive = None

        positionSouris = pygame.mouse.get_pos()

        if etatCourant == "liste":
            dessinerEcranListeQuestions(
                surfaceEcran,
                fondPrerendu,
                polices,
                banniere,
                rectanglesQuestions,
                positionSouris,
                modeleDisponible,
            )
        elif etatCourant == "reponse" and generationCourante is not None:
            questionDeclenchee = QUESTIONS_PROPOSEES[indexQuestionActive]
            dessinerEcranReponse(
                surfaceEcran,
                fondPrerendu,
                polices,
                banniere,
                questionDeclenchee["enonce"],
                questionDeclenchee["cleEspece"],
                generationCourante.lireTampon(),
                generationCourante.estTerminee(),
                generationCourante.lireErreur(),
                positionSouris,
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
