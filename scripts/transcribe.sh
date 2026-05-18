#!/usr/bin/env bash
#
# Download episodes from heis.fm RSS feed and transcribe them with whisperX.
# Transcripts with speaker labels are saved as .md files in src/content/transcripts/.
#
# Prerequisites:
#   python3.13 -m venv .venv && source .venv/bin/activate && pip install whisperx
#   Export HF_TOKEN with your HuggingFace token (for pyannote diarization)
#
# Usage:
#   ./scripts/transcribe.sh              # transcribe all episodes
#   ./scripts/transcribe.sh 5            # transcribe only episode 5
#   ./scripts/transcribe.sh --force 5    # re-transcribe even if transcript exists
#
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

# Activate venv
source "$PROJECT_DIR/.venv/bin/activate"

exec python3 "$SCRIPT_DIR/transcribe.py" "$@"
