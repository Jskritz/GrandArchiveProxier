"""
Generate PDF from a Tabletop Simulator deck file or from a decklist URL.

Usage:
  python generate_from_tts.py <path_or_url> [--output OUTPUT]

If a URL is provided, the script will try to convert known decklist page URLs
into JSON endpoints (same sites handled by the TTS Lua importer) and then
extract card image URLs and quantities to build the printable PDF.
"""

import argparse
import json
import requests
from pathlib import Path
from printerGA import GADeckPrinter
from urllib.parse import urlparse


# Create output directory
output_dir = Path("./output")
output_dir.mkdir(exist_ok=True)


def transform_deck_url(deck_url: str) -> str:
    """Apply known-site transformations to get a JSON endpoint (mimics Lua logic)."""
    u = deck_url
    # ensure scheme
    if not u.startswith("http"):
        u = "https://" + u

    if "dungeongui.de" in u:
        u = u.replace("/deck/", "/json/")
    elif "silvie.org" in u or "silv.ie" in u:
        if "format=json" not in u:
            u += ("?format=json" if "?" not in u else "&format=json")
    elif "shoutatyourdecks.com" in u:
        u = u.replace("/decks/", "/api/")
    elif "silvie.gg" in u:
        u = u.replace("silvie.gg/decklist?deck=", "silvie.gg/api/tts/export")
        u = u.replace("silvie.gg/decklist/", "silvie.gg/api/tts/export")
    elif "jsonblob.com" in u:
        u = u.replace("jsonblob.com/", "jsonblob.com/api/jsonBlob/")
    elif "tcgarchitect.com" in u:
        u = u.replace("tcgarchitect.com/grand-archive/decks/", "api.tcgarchitect.com/tts/grand-archive/deck/")
        u = u.replace("tcgarchitect.com/grand-archive/tournaments/decklists/", "api.tcgarchitect.com/tts/grand-archive/tournament-deck/")
    elif "fractalofin.site" in u:
        # Try to match expected patterns and build a JSON URL; keep best-effort approach
        import re
        patterns = [
            (r"/player/(\d+).html#deck_(\d+)", True, ""),
            (r"#deck_(\d+)_(\d+)", False, ""),
            (r"/\w+/(\d+).html#deck_(\d+)_topcut", False, "_topcut"),
            (r"/\w+/(\d+).html#deck_(\d+)", False, ""),
        ]
        m_event = None
        for pat, swap, suffix in patterns:
            m = re.search(pat, u)
            if m:
                a, b = m.groups()
                player_id = int(a) if swap else int(b)
                event_id = int(b) if swap else int(a)
                u = f"https://fractalofin.site/tts/event_{event_id}/{player_id}{suffix}.json"
                break
    return u


def fetch_json_from_url(url: str):
    try:
        r = requests.get(url, timeout=15)
        r.raise_for_status()
        return r.json()
    except Exception:
        # Not JSON or failed; return None
        return None


def build_printer_from_deck_json(data: dict, preferred_deck: str = None) -> GADeckPrinter:
    """Convert a variety of deck JSON shapes into a GADeckPrinter instance."""
    printer = GADeckPrinter()

    # If the JSON is already in printer format
    if isinstance(data, dict) and data.get("cards") and isinstance(data.get("cards"), list):
        # assume data is { deck_name, cards: [...] }
        printer.deck_name = data.get("deck_name", printer.deck_name)
        for c in data.get("cards", []):
            printer.add_card(name=c.get("name", "Unknown"), card_type=c.get("type", "Card"), quantity=c.get("quantity", 1), image_url=c.get("image_url", ""))
        return printer

    # If data has a 'cards' mapping (site exports)
    cards_root = None
    if isinstance(data, dict) and "cards" in data:
        cards_root = data["cards"]

    if cards_root is None:
        # Try to treat root as a single deck (list or dict)
        cards_root = data

    # If cards_root is a mapping of decks (main, material, sideboard, ...),
    # aggregate selected decks into the printer so the PDF contains all cards.
    entries = []
    if isinstance(cards_root, dict):
        # preferred order: main, material, sideboard, then any other decks
        preferred_keys = ["main", "material", "sideboard"]
        seen = set()
        for k in preferred_keys:
            if k in cards_root and cards_root[k]:
                value = cards_root[k]
                if isinstance(value, list):
                    for info in value:
                        if isinstance(info, dict):
                            info.setdefault("_source_deck", k)
                        entries.append(info)
                elif isinstance(value, dict):
                    for key, info in value.items():
                        if isinstance(info, dict):
                            info.setdefault("name", key)
                            info.setdefault("_source_deck", k)
                        entries.append(info)
                seen.add(k)

        # include any other decks not in preferred_keys
        for k, value in cards_root.items():
            if k in seen:
                continue
            if not value:
                continue
            if isinstance(value, list):
                for info in value:
                    if isinstance(info, dict):
                        info.setdefault("_source_deck", k)
                    entries.append(info)
            elif isinstance(value, dict):
                for key, info in value.items():
                    if isinstance(info, dict):
                        info.setdefault("name", key)
                        info.setdefault("_source_deck", k)
                    entries.append(info)

    else:
        # not a mapping: treat as single deck
        if isinstance(cards_root, list):
            entries = cards_root
        elif isinstance(cards_root, dict):
            for key, info in cards_root.items():
                if isinstance(info, dict):
                    info.setdefault("name", key)
                entries.append(info)

    # Add entries to printer (merge all decks)
    for e in entries:
        if not isinstance(e, dict):
            continue
        name = e.get("name") or e.get("title") or e.get("card_name") or "Unknown"
        qty = int(e.get("quantity", e.get("qty", 1) or 1))
        img = e.get("image") or e.get("image_url") or e.get("img") or e.get("FaceURL") or e.get("face") or ""
        # Optionally annotate name with source deck for clarity
        srcdeck = e.get("_source_deck")
        if srcdeck and srcdeck not in ("main",):
            # keep main names as-is, but prefix others (material/sideboard)
            name = f"[{srcdeck}] {name}"
        printer.add_card(name=name, card_type=e.get("type", "Card"), quantity=qty, image_url=img)

    return printer


def main():
    parser = argparse.ArgumentParser(description="Generate printable card PDF from TTS save or decklist URL")
    parser.add_argument("source", help="Path to TTS JSON file or decklist URL")
    parser.add_argument("--output", "-o", help="Output PDF filename", default=str(output_dir / "cards_printable.pdf"))
    args = parser.parse_args()

    src = args.source
    out = args.output

    printer = GADeckPrinter()

    # If file exists locally, try as TTS save first, then fallback to load_from_json
    p = Path(src)
    if p.exists():
        print(f"Loading local file: {src}")
        # Heuristic: if file looks like a TTS save (contains ObjectStates), use load_from_tts
        try:
            txt = p.read_text(encoding="utf-8")
            j = json.loads(txt)
            if isinstance(j, dict) and j.get("ObjectStates"):
                printer.load_from_tts(src)
            else:
                printer.load_from_json(src)
        except Exception as e:
            print(f"Failed to parse local JSON: {e}")
            return

    else:
        # Treat as URL
        url = src
        url = transform_deck_url(url)
        print(f"Fetching deck JSON from: {url}")
        try:
            resp = requests.get(url, timeout=15)
            resp.raise_for_status()
        except Exception as e:
            print(f"Error fetching URL: {e}")
            return

        # Try JSON decode
        try:
            data = resp.json()
        except Exception:
            # not JSON
            print("Response was not JSON; aborting.")
            return

        printer = build_printer_from_deck_json(data)

    if not printer.cards or sum(c.get("quantity", 1) for c in printer.cards) == 0:
        print("No cards found to render.")
        return

    print(f"Loaded {len(printer.cards)} unique cards (total copies: {sum(c.get('quantity',1) for c in printer.cards)})")
    print("="*50)

    # Generate printable cards PDF
    printer.create_printable_cards_pdf(out)
    # Also save a deck.json for reference
    try:
        printer.save_to_json(str(output_dir / "deck.json"))
    except Exception:
        pass

    print("\n✓ PDF generated successfully!")
    print(f"  - Printable Cards: {out}")


if __name__ == "__main__":
    main()

