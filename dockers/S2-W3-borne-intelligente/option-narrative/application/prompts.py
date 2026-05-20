"""
prompts.py - System prompts et catalogues d'especes pour la borne narrative.

Trois ecosystemes du Zoo maritime du Bas-Saint-Laurent :
  - marin (estuaire et golfe du Saint-Laurent)
  - forestier (foret boreale du Bas-Saint-Laurent et de la Gaspesie)
  - pollinisateurs (jardins et prairies humides indigenes)

Chaque entree fournit :
  - le titre du pavillon affiche dans l'interface
  - une courte description pour l'ecran de selection
  - la liste des especes vedettes du pavillon
  - un system prompt complet pour cadrer le LLM

Aucun accent dans les chaines : les polices SDL2 affichent mal les diacritiques
et le modele qwen2.5:0.5b genere parfois des caracteres unicode imprevus.
On lui impose donc explicitement le francais sans accents.
"""

ECOSYSTEMES = {
    "marin": {
        "titrePavillon": "Pavillon marin",
        "descriptionCourte": "Estuaire et golfe du Saint-Laurent",
        "especes": [
            "Beluga du Saint-Laurent",
            "Phoque commun",
            "Crabe des neiges",
            "Etoile de mer commune",
        ],
    },
    "forestier": {
        "titrePavillon": "Pavillon forestier",
        "descriptionCourte": "Foret boreale du Bas-Saint-Laurent",
        "especes": [
            "Orignal",
            "Lievre d'Amerique",
            "Lynx du Canada",
            "Renard roux",
        ],
    },
    "pollinisateurs": {
        "titrePavillon": "Pavillon des pollinisateurs",
        "descriptionCourte": "Jardins et prairies humides",
        "especes": [
            "Papillon monarque",
            "Bourdon febrile",
            "Asclepiade incarnate",
            "Abeille charpentiere",
        ],
    },
}


def construirePromptSysteme(cleEcosysteme, nombreEtapes):
    """Compose le system prompt pour l'ecosysteme et la longueur d'aventure choisis.

    Le prompt cadre :
      - le decor (Bas-Saint-Laurent, le pavillon, ses especes)
      - le role du joueur (soigneur stagiaire qui apprend)
      - le format strict (3-4 phrases narratives + 3 choix A/B/C)
      - la langue (francais sans accents pour compatibilite police)
      - la longueur (5 a 7 etapes selon nombreEtapes)
    """
    donneesEcosysteme = ECOSYSTEMES[cleEcosysteme]
    listeEspecesFormatee = ", ".join(donneesEcosysteme["especes"])

    return (
        "Tu animes une mini aventure interactive pour la borne kiosque du "
        "Zoo maritime du Bas-Saint-Laurent au Quebec. Le visiteur incarne un "
        "soigneur stagiaire au " + donneesEcosysteme["titrePavillon"] + ". "
        "Les especes vedettes du pavillon sont : " + listeEspecesFormatee + ". "
        "L'aventure dure exactement " + str(nombreEtapes) + " etapes. "
        "A chaque etape (sauf la derniere), tu decris la situation en 3 ou 4 "
        "phrases courtes et concretes, puis tu proposes exactement 3 choix "
        "d'action. "
        "Tu DOIS terminer ta reponse par 3 lignes, chacune commencant par "
        "'A) ', 'B) ' et 'C) ', sur des lignes separees, avec une phrase "
        "courte par choix. "
        "A la derniere etape, tu conclus l'aventure en 3 ou 4 phrases sans "
        "proposer de choix. "
        "Tu ecris en francais SANS aucun accent (ecris 'etape' pas 'etape', "
        "'foret' pas 'foret') car la borne ne supporte pas les diacritiques. "
        "Tu integres au moins une espece du pavillon par etape. "
        "Tu restes credible : pas de magie, pas d'animaux qui parlent, on est "
        "dans un vrai zoo educatif au Quebec. "
        "Tu evites les tirets longs, utilise seulement le tiret simple."
    )


def construireMessageEtape(numeroEtape, nombreEtapes):
    """Message utilisateur pour demander la prochaine etape."""
    if numeroEtape >= nombreEtapes:
        return (
            "Etape " + str(numeroEtape) + " sur " + str(nombreEtapes) + ". "
            "C'est la conclusion. Termine l'aventure en 3 ou 4 phrases. "
            "Ne propose AUCUN choix. Pas de lignes A) B) C). "
            "Donne une chute satisfaisante : reussite, lecon apprise, ou "
            "anecdote sur l'espece rencontree."
        )
    return (
        "Etape " + str(numeroEtape) + " sur " + str(nombreEtapes) + ". "
        "Continue l'aventure. Decris la situation en 3 ou 4 phrases puis "
        "termine ta reponse par exactement 3 lignes commencant par "
        "'A) ', 'B) ', 'C) '."
    )


def construireMessagePremiereEtape(nombreEtapes):
    """Message utilisateur pour ouvrir l'aventure (etape 1)."""
    return (
        "Etape 1 sur " + str(nombreEtapes) + ". "
        "Demarre l'aventure : presente la scene d'ouverture (le visiteur "
        "arrive a son poste de soigneur ce matin) en 3 ou 4 phrases, puis "
        "termine par 3 lignes 'A) ', 'B) ', 'C) ' qui proposent la premiere "
        "decision concrete du visiteur."
    )
