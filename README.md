# Hermes Skills

Collection de skills Hermes Agent pour l'automatisation vidéo, l'IA gratuite et l'optimisation système.

## À propos

Ce dépôt contient des skills prêts à l'emploi pour Hermes Agent. Chaque skill est autonome et documenté.

<a href="https://www.youtube.com/watch?v=7CbnMTcFTO0" target="_blank">
  <img src="https://youtube.com" alt="Hermes Agent — Télécharge Les Skills : 7 automatisations IA prêtes à l'emploi (Volet 3)" width="560" height="315" />
</a>




## Skills disponibles

| Skill | Description | Catégorie |
|-------|-------------|-----------|
| [omniroute-auto-update](skills/omniroute-auto-update/) | Veille automatique + ajout des nouvelles IA gratuites avec notification Telegram | IA |
| [liveportrait-pipeline](skills/liveportrait-pipeline/) | Animation faciale réaliste avec LivePortrait, optimisation GPU, assemblage fond/logo | Vidéo |
| [talking-head-video](skills/talking-head-video/) | Pipeline complet SadTalker + LivePortrait + assemblage | Vidéo |
| [video-youtube-assembly](skills/video-youtube-assembly/) | Assemblage final : fond animé + logo + audio + titre | Vidéo |
| [nvidia-nim-vision](skills/nvidia-nim-vision/) | Vision par NVIDIA NIM (proxy local + API) | IA |
| [tts-voice-cloning](skills/tts-voice-cloning/) | Clonage vocal en français avec XTTS-v2 | Audio |
| [windows-optimization](skills/windows-optimization/) | Nettoyage temp, gestion des tâches planifiées, optimisation Windows | Système |

## Installation

1. **Cloner le dépôt**
   ```bash
   git clone https://github.com/Antoine-Thomas/hermes-skills.git
   cd hermes-skills
   ```

2. **Copier un skill dans Hermes**
   ```bash
   cp -r skills/<nom-du-skill> ~/AppData/Local/hermes/skills/
   ```

3. **Configurer les variables d'environnement**
   ```bash
   # Copier le fichier .env.example et le remplir
   cp skills/<nom-du-skill>/.env.example skills/<nom-du-skill>/.env
   # Éditer .env avec vos clés API
   ```

## Prérequis globaux

- **Hermes Agent** v0.21+ (https://github.com/NousResearch/hermes-agent)
- **Python 3.11+**
- **FFmpeg** (pour le traitement vidéo)
- **GPU** (RTX 3070 Ti recommandé pour les tâches vidéo/IA)

## Variables d'environnement

Chaque skill peut nécessiter des variables d'environnement spécifiques. Voir le fichier `.env.example` de chaque skill.

```env
# Exemple global
OMNIROUTE_API_KEY=your_omni_route_key
NVIDIA_API_KEY=your_nvidia_api_key
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
```

## Structure d'un skill

```
skills/<nom-du-skill>/
├── SKILL.md              # Documentation principale
├── scripts/              # Scripts Python/Bash
├── references/           # Documentation complémentaire
├── .env.example          # Template des variables d'environnement
└── README.md             # README spécifique au skill (optionnel)
```

## Créer un nouveau skill

Utiliser le template dans `templates/skill-template/`.

## Licence

MIT License — voir le fichier LICENSE pour plus de détails.

## Auteur

Thomas Leroyer — [searching-murphy.com](https://searching-murphy.com)

## Liens

- [Hermes Agent](https://github.com/NousResearch/hermes-agent)
- [Documentation Hermes](https://hermes-agent.nousresearch.com/docs)
- [Searching Murphy](https://searching-murphy.com)
