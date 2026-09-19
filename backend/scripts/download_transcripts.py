"""
Fetches (or reads locally-provided) Lenny's Podcast transcript files into
backend/data/raw/. Expects plain-text or markdown files, one per episode.

Usage:
    python scripts/download_transcripts.py --source-dir /path/to/transcripts
    python scripts/download_transcripts.py --source-dir ./sample_transcripts --copy-only
"""
import argparse
import shutil
from pathlib import Path

RAW_DIR = Path(__file__).resolve().parent.parent / "data" / "raw"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-dir", required=True, help="Directory of .txt/.md transcript files")
    parser.add_argument("--copy-only", action="store_true", help="Just copy files into data/raw/ (no fetching)")
    args = parser.parse_args()

    RAW_DIR.mkdir(parents=True, exist_ok=True)
    source = Path(args.source_dir)
    if not source.exists():
        raise SystemExit(f"Source directory not found: {source}")

    count = 0
    for f in source.glob("*"):
        if f.suffix.lower() in (".txt", ".md"):
            shutil.copy(f, RAW_DIR / f.name)
            count += 1

    print(f"Copied {count} transcript file(s) into {RAW_DIR}")
    print("Next: python scripts/ingest.py")


if __name__ == "__main__":
    main()
