# -*- coding: utf-8 -*-
"""Génère la voix off du Volet 4 avec XTTS-v2 (réglages V7)."""
import time
from TTS.api import TTS
from TTS.utils.manage import ModelManager

ModelManager.ask_tos = staticmethod(lambda path: True)

TEXT = """Bonjour et bienvenue dans ce quatrième volet de notre série sur l'automatisation avec Hermes Agent.

Aujourd'hui, je vais vous montrer comment j'ai construit un pipeline vidéo complet, de la photo source jusqu'au montage final, en utilisant uniquement des outils open source et gratuits.

Le pipeline se décompose en quatre étapes.

Première étape : l'animation faciale. À partir d'une simple photo, j'utilise LivePortrait pour animer le visage avec des mouvements naturels. Les yeux clignent, la tête bouge, et les expressions sont fluides.

Deuxième étape : le clonage vocal. Avec XTTS-v2, je clone ma propre voix en français, sans abonnement, sans service cloud. Le résultat est naturel et stable.

Troisième étape : l'assemblage final. J'utilise FFmpeg pour combiner le visage animé avec un fond neutre, un logo Hermes, et la voix off. Le tout en 1080p, 60 images par seconde.

Quatrième étape : la publication. Le résultat est une vidéo prête pour YouTube, exportée en H.264 avec un son AAC de qualité.

Vous pouvez retrouver tous ces skills sur mon dépôt GitHub public : hermes-skills. Chaque skill contient sa propre documentation, ses scripts, et un fichier point env example pour configurer vos clés API.

Pour l'installer, rien de plus simple. Clonez le dépôt, copiez les skills dans votre dossier Hermes, et configurez vos variables d'environnement.

Le dépôt est sous licence MIT, donc vous pouvez l'utiliser, le modifier, et l'intégrer à vos propres projets librement.

Si cette vidéo vous a été utile, laissez un like, abonnez-vous à la chaîne, et activez la cloche pour ne pas rater la suite.

Tous les liens sont dans la description. On se retrouve très bientôt pour un nouveau volet. À très bientôt !"""

REF = r"C:\Users\searc\AppData\Local\hermes\data\xtts\voix_reference.wav"
OUT = r"C:\Users\searc\AppData\Local\hermes\data\video_youtube\volet4_voice.wav"

print("Texte:", len(TEXT), "caractères", flush=True)
print("Chargement XTTS-v2...", flush=True)
t0 = time.time()
tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2", gpu=True)
print(f"Chargé en {time.time()-t0:.1f}s", flush=True)

print("Génération de la voix off...", flush=True)
t1 = time.time()
tts.tts_to_file(
    text=TEXT,
    speaker_wav=REF,
    language="fr",
    temperature=0.75,
    file_path=OUT,
)
print(f"Généré en {time.time()-t1:.1f}s", flush=True)
print("Sortie:", OUT)
