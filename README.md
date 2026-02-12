# GrandArchiveProxier

## How to use

This script now accepts either a local Tabletop Simulator JSON save or a decklist URL from supported sites and generates a single PDF containing the Main, Material and Sideboard cards.

Basic usage:

```
python generate_from_tts.py <path_or_url> --output <output_pdf_path>
```

Examples:

- Fetch and generate from a decklist URL:

```
python generate_from_tts.py "https://tcgarchitect.com/grand-archive/tournaments/decklists/9746" -o output/tcg_9746_printable_all.pdf
```

- Generate from a local TTS save file:

```
python generate_from_tts.py "C:/Users/Josh/Documents/My Games/Tabletop Simulator/Saves/Saved Objects/my_deck.json" -o output/my_deck_printable.pdf
```

Notes:
- If `--output` is omitted the script writes to `output/cards_printable.pdf` by default.
- The script aggregates `main`, `material`, and `sideboard` decks (and other decks if present) into the same PDF.
- A `deck.json` copy of the parsed deck will be written to the `output/` folder for reference.

## Requirements

Install these Python packages (tested with Python 3.11+):

```
pip install requests Pillow reportlab
```

Alternatively you can install from a requirements file (not included by default):

```
pip install -r requirements.txt
```

## Supported sites

The script attempts to convert common decklist page URLs to their JSON endpoints for these sites (same logic as the TTS Lua importer):

- dungeongui.de
- silvie.org / silvie.gg
- shoutatyourdecks.com
- jsonblob.com
- tcgarchitect.com
- fractalofin.site

If a site responds with a JSON deck export the script will parse card names, images and quantities and include them in the PDF.

## Troubleshooting

- If the script prints `Response was not JSON; aborting.`, the URL you provided did not return JSON. Try the site’s export link or use a local TTS JSON file.
- If images fail to download, check your network or run again (downloads are cached during a run).

---
Updated to simplify workflow: provide a single link or path and an output PDF path; the script does the rest.

## Using the GUI (.exe)

After building the GUI executable (see `README_build.md`), run the produced `gui.exe` from the `dist` folder or double-click it. The GUI exposes a small set of controls:

- **`Deck URL or local TTS JSON`:** Paste a decklist page URL or a local Tabletop Simulator JSON save file path. Supported site URLs will be converted to JSON endpoints automatically. Use the **Browse...** button to pick a local file instead of typing a path.
- **`Output PDF path`:** File path where the generated printable PDF will be saved. Click **Choose...** to open a Windows Save dialog, or **Use Default** to reset to `output/cards_printable.pdf`.
- **`Generate`:** Starts creating the PDF. Controls are temporarily disabled and an indeterminate progress bar runs while the app works in the background.
- **`Open Output`:** Enabled after a successful run. Click to open the generated PDF; if the PDF is missing the button opens the containing folder instead.

Notes:
- When a URL (not a local file) is used as the source, the GUI saves the original deck URL into a `deck_url.txt` file placed in the same folder as the generated PDF.
- The app also writes a `deck.json` file (in the `output/` folder by default) containing the parsed deck data for reference.
- If generation fails, an error dialog shows the exception traceback; re-run with a different source or examine the URL JSON manually.
