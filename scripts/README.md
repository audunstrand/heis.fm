# Transkripsjoner

Scriptet `scripts/transcribe.py` laster ned episoder fra heis.fm RSS-feeden, transkriberer dem med [whisperX](https://github.com/m-bain/whisperX) og legger til speaker diarization via [pyannote](https://github.com/pyannote/pyannote-audio).

Transkripsjoner lagres som markdown-filer i `src/content/transcripts/`.

## Oppsett

### 1. Installer systemavhengigheter

```bash
brew install ffmpeg python@3.13
```

### 2. Opprett Python virtualenv og installer pakker

```bash
python3.13 -m venv .venv
source .venv/bin/activate
pip install whisperx
```

### 3. Sett opp HuggingFace-tilgang

Pyannote-modellene som brukes til speaker diarization er "gated" og krever at du godtar bruksvilkarene:

1. Opprett konto pa [huggingface.co](https://huggingface.co)
2. Godta vilkarene for disse modellene:
   - [pyannote/speaker-diarization-community-1](https://huggingface.co/pyannote/speaker-diarization-community-1)
   - [pyannote/segmentation-3.0](https://huggingface.co/pyannote/segmentation-3.0)
3. Opprett en token med lesetilgang pa [huggingface.co/settings/tokens](https://huggingface.co/settings/tokens)
4. Eksporter tokenet:
   ```bash
   export HF_TOKEN="hf_din_token_her"
   ```

## Bruk

```bash
# Aktiver virtualenv
source .venv/bin/activate

# Transkriber alle episoder som mangler transkripsjon
./scripts/transcribe.sh

# Transkriber en spesifikk episode
./scripts/transcribe.sh 5

# Re-transkriber selv om transkripsjonen allerede finnes
./scripts/transcribe.sh --force 5

# Angi antall speakers (default: 3)
./scripts/transcribe.sh --speakers 2 0
```

Scriptet hopper automatisk over episoder som allerede har en transkripsjon i `src/content/transcripts/`. Bruk `--force` for a overskrive.

## Hva skjer under panseret

1. RSS-feeden fra Acast hentes og parses for a finne episoder og MP3-URLer
2. MP3-filer lastes ned til `.mp3-cache/` (gjenbrukes ved neste kjoring)
3. WhisperX transkriberer lyden med `medium`-modellen og norsk sprak
4. Transkripsjonen alignes pa ordniva for presise tidsstempler
5. Pyannote kjorer speaker diarization for a identifisere hvem som snakker
6. Resultatet lagres som markdown med `**SPEAKER_XX:**`-labels

## Tidsbruk

Pa en M3 Pro tar det ca. 5-15 minutter per episode, avhengig av lengde. Modeller caches lokalt etter forste kjoring.
