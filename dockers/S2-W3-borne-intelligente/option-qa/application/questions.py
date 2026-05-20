"""
Borne intelligente Q&A - Donnees du zoo
Zoo maritime du Bas-Saint-Laurent

Catalogue des especes (fiches breves) et liste des questions predefinies
proposees au visiteur. Le contenu sert de base de connaissance contextuelle
fournie au LLM local au moment de la generation de la reponse.

Aucun accent dans les chaines : les polices SDL2 utilisees par Pygame
gerent mal les caracteres accentues, et on garde la coherence avec les
autres bornes du zoo.
"""

# Ecosystemes affiches (cles canoniques utilisees pour le code couleur).
ECOSYSTEMES = ("marin", "forestier", "pollinisateurs")

# Couleurs d'accent par ecosysteme (RGB), reprises de la borne medias
# pour la coherence visuelle entre les bornes du zoo.
COULEURS_ECOSYSTEME = {
    "marin": (61, 150, 189),
    "forestier": (98, 142, 78),
    "pollinisateurs": (210, 150, 60),
}

NOMS_ECOSYSTEME = {
    "marin": "Ecosysteme marin",
    "forestier": "Foret boreale",
    "pollinisateurs": "Pollinisateurs et jardins",
}

# Fiches d'espece : description courte + fait marquant.
# Reprises de schema.sql, accents retires pour Pygame.
FICHES_ESPECE = {
    "beluga": {
        "nomCommun": "Beluga du Saint-Laurent",
        "nomLatin": "Delphinapterus leucas",
        "ecosysteme": "marin",
        "description": (
            "Petite baleine blanche emblematique de l'estuaire et du golfe "
            "du Saint-Laurent. Population isolee et menacee d'environ 900 "
            "individus. Communique par un large repertoire de sifflements "
            "et de claquements."
        ),
        "faitMarquant": (
            "Surnomme le canari des mers pour son chant audible a plusieurs "
            "kilometres sous l'eau."
        ),
    },
    "phoque": {
        "nomCommun": "Phoque commun",
        "nomLatin": "Phoca vitulina",
        "ecosysteme": "marin",
        "description": (
            "Plus petit des phoques du Saint-Laurent, present toute l'annee "
            "sur les rochers du Bas-Saint-Laurent et de la Gaspesie. Museau "
            "court, taches sombres irregulieres."
        ),
        "faitMarquant": (
            "Peut rester jusqu'a 30 minutes sous l'eau et plonger a 200 "
            "metres de profondeur."
        ),
    },
    "crabe": {
        "nomCommun": "Crabe des neiges",
        "nomLatin": "Chionoecetes opilio",
        "ecosysteme": "marin",
        "description": (
            "Crustace des fonds froids du golfe et de l'estuaire, a pattes "
            "longues et fines. Vit entre 50 et 300 metres de profondeur. "
            "Peche commerciale majeure de la Cote-Nord et de la Gaspesie."
        ),
        "faitMarquant": (
            "Migre verticalement dans la colonne d'eau au gre des saisons."
        ),
    },
    "etoile": {
        "nomCommun": "Etoile de mer commune",
        "nomLatin": "Asterias rubens",
        "ecosysteme": "marin",
        "description": (
            "Echinoderme a cinq bras radiaux, couleurs orangees a brunes, "
            "present sur les fonds rocheux du Saint-Laurent. Capable de "
            "regenerer un bras perdu."
        ),
        "faitMarquant": (
            "Mange ses proies en projetant son estomac a l'exterieur de son "
            "corps pour digerer une moule sur place."
        ),
    },
    "orignal": {
        "nomCommun": "Orignal",
        "nomLatin": "Alces americanus",
        "ecosysteme": "forestier",
        "description": (
            "Plus grand cervide du continent. Abondant dans la foret boreale "
            "du Bas-Saint-Laurent. Solitaire la majeure partie de l'annee, "
            "sauf en saison du brame en automne."
        ),
        "faitMarquant": (
            "Le male perd ses bois chaque hiver et en repousse une nouvelle "
            "paire au printemps."
        ),
    },
    "lievre": {
        "nomCommun": "Lievre d'Amerique",
        "nomLatin": "Lepus americanus",
        "ecosysteme": "forestier",
        "description": (
            "Petit lievre forestier qui change de couleur selon la saison : "
            "brun roux l'ete, blanc l'hiver pour se camoufler dans la neige. "
            "Pattes larges qui lui servent de raquettes naturelles."
        ),
        "faitMarquant": (
            "Sa population suit un cycle de 10 ans, lie a celui du lynx du "
            "Canada qui s'en nourrit."
        ),
    },
    "lynx": {
        "nomCommun": "Lynx du Canada",
        "nomLatin": "Lynx canadensis",
        "ecosysteme": "forestier",
        "description": (
            "Felin discret de la foret boreale, plus petit que le couguar. "
            "Oreilles surmontees de pinceaux noirs, pattes enormes qui lui "
            "servent de raquettes dans la neige profonde."
        ),
        "faitMarquant": (
            "Sa population suit fidelement celle du lievre d'Amerique avec "
            "un cycle de dix ans documente par les archives de fourrure."
        ),
    },
    "renard": {
        "nomCommun": "Renard roux",
        "nomLatin": "Vulpes vulpes",
        "ecosysteme": "forestier",
        "description": (
            "Petit canide adaptable, present en foret comme en milieu "
            "agricole. Pelage orange a blanc. Excellent chasseur grace a "
            "une ouie extraordinaire."
        ),
        "faitMarquant": (
            "Capable de localiser une souris sous la neige uniquement a "
            "l'oreille et de plonger pour la capturer tete premiere."
        ),
    },
    "monarque": {
        "nomCommun": "Papillon monarque",
        "nomLatin": "Danaus plexippus",
        "ecosysteme": "pollinisateurs",
        "description": (
            "Papillon orange et noir emblematique. Migration de plusieurs "
            "generations entre le Mexique et le sud du Quebec, en suivant "
            "la croissance de l'asclepiade, sa plante hote."
        ),
        "faitMarquant": (
            "Aucun individu ne fait le voyage aller-retour : ce sont les "
            "arriere-arriere-petits-enfants qui reviennent au point de "
            "depart de leurs ancetres."
        ),
    },
    "bourdon": {
        "nomCommun": "Bourdon febrile",
        "nomLatin": "Bombus impatiens",
        "ecosysteme": "pollinisateurs",
        "description": (
            "Bourdon indigene de l'Est canadien, tres bon pollinisateur des "
            "plantes a corolle tubulaire. Vole par temps frais. Niche au "
            "sol, dans des abris naturels."
        ),
        "faitMarquant": (
            "Sa langue mesure presque la longueur de son corps, lui "
            "permettant d'atteindre le nectar des trefles."
        ),
    },
    "asclepiade": {
        "nomCommun": "Asclepiade incarnate",
        "nomLatin": "Asclepias incarnata",
        "ecosysteme": "pollinisateurs",
        "description": (
            "Plante melifere vivace des prairies humides du Bas-Saint-"
            "Laurent. Fleurs roses regroupees en ombelles parfumees. Plante "
            "hote essentielle du papillon monarque."
        ),
        "faitMarquant": (
            "Sa seve blanche contient des cardenolides qui rendent les "
            "chenilles de monarque toxiques pour leurs predateurs."
        ),
    },
    "charpentiere": {
        "nomCommun": "Abeille charpentiere",
        "nomLatin": "Xylocopa virginica",
        "ecosysteme": "pollinisateurs",
        "description": (
            "Grosse abeille solitaire au corps noir et brillant, sans "
            "rayures. Creuse ses galeries de nidification dans le bois "
            "mort, sans degats structurels significatifs."
        ),
        "faitMarquant": (
            "Pratique parfois le vol-pollinisation : elle perce la base des "
            "fleurs trop profondes pour atteindre le nectar."
        ),
    },
}


# Liste de questions predefinies presentees au visiteur. Chaque entree
# pointe vers une fiche d'espece dont le contenu sera injecte au LLM en
# guise de contexte minimal lors de la generation.
QUESTIONS_PROPOSEES = [
    {
        "cleEspece": "beluga",
        "enonce": "Pourquoi le beluga est-il surnomme le canari des mers ?",
    },
    {
        "cleEspece": "phoque",
        "enonce": "Combien de temps un phoque commun reste-t-il sous l'eau ?",
    },
    {
        "cleEspece": "crabe",
        "enonce": "Comment le crabe des neiges se deplace-t-il dans le golfe ?",
    },
    {
        "cleEspece": "etoile",
        "enonce": "Comment une etoile de mer mange-t-elle une moule ?",
    },
    {
        "cleEspece": "orignal",
        "enonce": "Comment l'orignal se debarrasse-t-il de ses bois chaque annee ?",
    },
    {
        "cleEspece": "lievre",
        "enonce": "Pourquoi le lievre d'Amerique change-t-il de couleur l'hiver ?",
    },
    {
        "cleEspece": "lynx",
        "enonce": "Pourquoi la population du lynx du Canada suit-elle un cycle de dix ans ?",
    },
    {
        "cleEspece": "renard",
        "enonce": "Comment le renard roux chasse-t-il une souris cachee sous la neige ?",
    },
    {
        "cleEspece": "monarque",
        "enonce": "Comment le papillon monarque migre-t-il sur plusieurs generations ?",
    },
    {
        "cleEspece": "bourdon",
        "enonce": "Pourquoi le bourdon febrile peut-il voler par temps frais ?",
    },
    {
        "cleEspece": "asclepiade",
        "enonce": "Pourquoi l'asclepiade est-elle indispensable au monarque ?",
    },
    {
        "cleEspece": "charpentiere",
        "enonce": "Comment l'abeille charpentiere construit-elle son nid ?",
    },
]


def construireContexteEspece(cleEspece):
    """Compose un court paragraphe descriptif pour injecter au LLM."""
    fiche = FICHES_ESPECE[cleEspece]
    return (
        f"Espece : {fiche['nomCommun']} ({fiche['nomLatin']}). "
        f"Ecosysteme : {fiche['ecosysteme']}. "
        f"Description : {fiche['description']} "
        f"Fait marquant : {fiche['faitMarquant']}"
    )
