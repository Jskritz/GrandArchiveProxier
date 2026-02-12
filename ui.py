"""Command-line UI module for GrandArchiveProxier.

Separates argument parsing and user interaction from the core logic
in `generate_from_tts.py`.
"""
import argparse
from generate_from_tts import generate_from_source


def main():
    parser = argparse.ArgumentParser(description="Generate printable card PDF from TTS save or decklist URL")
    parser.add_argument("source", help="Path to TTS JSON file or decklist URL")
    parser.add_argument("--output", "-o", help="Output PDF filename", default=None)
    args = parser.parse_args()

    printer, out = generate_from_source(args.source, args.output)
    if printer is None:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
