"""
Download episodes from heis.fm RSS feed and transcribe them with whisperX + diarization.
Transcripts with speaker labels are saved as .md files in src/content/transcripts/.
"""

import argparse
import os
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import requests
import whisperx
from whisperx.diarize import DiarizationPipeline

RSS_URL = "https://feeds.acast.com/public/shows/68d8f5fdacc34956e6156eec"
PROJECT_DIR = Path(__file__).resolve().parent.parent
TRANSCRIPTS_DIR = PROJECT_DIR / "src" / "content" / "transcripts"
DOWNLOADS_DIR = PROJECT_DIR / ".mp3-cache"

# Known number of speakers per episode.
# Episodes with 2 guests have 4 speakers (Truls + Audun + 2 guests).
# --speakers flag overrides this for a specific run.
EPISODE_SPEAKERS: dict[int, int] = {
    0: 2,   # Velkommen til Heis (bare Truls og Audun)
    1: 3,   # Torbjørn Larsen
    2: 3,   # Hans Christian Holte
    3: 3,   # Christin Gorman
    4: 3,   # Morten Eikeland
    5: 3,   # Vidar Moe
    6: 4,   # Catherine Janson og Kjerstin Wester
    7: 3,   # Stine Haugseth
    8: 3,   # Christian Printzell Halvorsen
    9: 3,   # Nils Brede Moe
    10: 3,  # Una Aamodt Mathisen
    11: 4,  # Vilde Opsal og Anders Sveen
    12: 3,  # Greger Teigre Wedel
    13: 3,  # Tobias K. Torrissen
    14: 3,  # Øystein Ulseth
    15: 3,  # Kari Olrud Moen
    16: 3,  # Inga Strümke
    17: 3,  # Jonas Slørdahl Skjærpe
}



def parse_episodes(rss_xml: str) -> list[dict]:
    root = ET.fromstring(rss_xml)
    items = list(reversed(root.findall(".//item")))
    episodes = []
    for i, item in enumerate(items):
        title_el = item.find("title")
        title = title_el.text if title_el is not None and title_el.text else ""
        title = re.sub(r"^\d+\)\s*", "", title)

        enclosure = item.find("enclosure")
        url = enclosure.get("url", "") if enclosure is not None else ""

        if url:
            episodes.append({"num": i, "title": title, "url": url})
    return episodes


def download_episode(episode: dict) -> Path:
    DOWNLOADS_DIR.mkdir(parents=True, exist_ok=True)
    mp3_path = DOWNLOADS_DIR / f"episode-{episode['num']}.mp3"
    if mp3_path.exists():
        print(f"  Using cached MP3")
        return mp3_path

    print(f"  Downloading...")
    resp = requests.get(episode["url"], stream=True, headers={"User-Agent": "Mozilla/5.0"})
    resp.raise_for_status()
    with open(mp3_path, "wb") as f:
        for chunk in resp.iter_content(chunk_size=8192):
            f.write(chunk)
    return mp3_path


def transcribe_episode(mp3_path: Path, hf_token: str, num_speakers: int = 2) -> str:
    device = "cpu"
    compute_type = "int8"

    # 1. Transcribe with whisperX
    print("  Loading model...")
    model = whisperx.load_model("medium", device, compute_type=compute_type, language="no")

    print("  Transcribing...")
    audio = whisperx.load_audio(str(mp3_path))
    result = model.transcribe(audio, batch_size=8, language="no")

    # 2. Align whisper output for word-level timestamps
    print("  Aligning...")
    model_a, metadata = whisperx.load_align_model(language_code="no", device=device)
    result = whisperx.align(result["segments"], model_a, metadata, audio, device, return_char_alignments=False)

    # 3. Diarize — assign speaker labels
    print("  Diarizing...")
    diarize_model = DiarizationPipeline(token=hf_token, device=device)
    diarize_segments = diarize_model(audio, min_speakers=num_speakers, max_speakers=num_speakers)
    result = whisperx.assign_word_speakers(diarize_segments, result)

    # 4. Format as markdown with speaker labels
    return format_transcript(result["segments"])


def format_transcript(segments: list[dict]) -> str:
    lines = []
    current_speaker = None

    for seg in segments:
        speaker = seg.get("speaker", "UNKNOWN")
        text = seg.get("text", "").strip()

        if not text:
            continue

        if speaker != current_speaker:
            current_speaker = speaker
            lines.append(f"\n**{speaker}:** {text}")
        else:
            lines.append(text)

    return "\n".join(lines).strip()


def main():
    parser = argparse.ArgumentParser(description="Transcribe heis.fm episodes")
    parser.add_argument("episode", nargs="?", type=int, help="Episode number to transcribe")
    parser.add_argument("--force", action="store_true", help="Re-transcribe even if transcript exists")
    parser.add_argument("--speakers", type=int, default=None, help="Override number of speakers (default: auto per episode)")
    args = parser.parse_args()

    hf_token = os.environ.get("HF_TOKEN", "")
    if not hf_token:
        print("Error: HF_TOKEN environment variable not set.")
        print("Get a token at https://huggingface.co/settings/tokens")
        sys.exit(1)

    TRANSCRIPTS_DIR.mkdir(parents=True, exist_ok=True)

    print("Fetching RSS feed...")
    rss_xml = requests.get(RSS_URL).text
    episodes = parse_episodes(rss_xml)
    print(f"Found {len(episodes)} episodes.")

    for ep in episodes:
        num = ep["num"]
        if args.episode is not None and num != args.episode:
            continue

        transcript_path = TRANSCRIPTS_DIR / f"{num}.md"

        if transcript_path.exists() and not args.force:
            print(f"[{num}/{len(episodes)-1}] Skipping episode {num} ({ep['title']}) - transcript exists")
            continue

        print(f"[{num}/{len(episodes)-1}] Processing episode {num}: {ep['title']}")

        mp3_path = download_episode(ep)
        num_speakers = args.speakers if args.speakers is not None else EPISODE_SPEAKERS.get(num)
        if num_speakers is None:
            print(f"  ERROR: Unknown number of speakers for episode {num}. Add it to EPISODE_SPEAKERS in transcribe.py or use --speakers N")
            sys.exit(1)
        print(f"  Speakers: {num_speakers}")
        transcript = transcribe_episode(mp3_path, hf_token, num_speakers=num_speakers)

        transcript_path.write_text(transcript, encoding="utf-8")
        print(f"  Saved: {transcript_path}")

    print("\nDone!")


if __name__ == "__main__":
    main()
