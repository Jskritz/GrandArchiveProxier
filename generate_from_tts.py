"""
Generate PDF from Tabletop Simulator deck file - Images Only
"""

from printerGA import GADeckPrinter
from pathlib import Path

# Create output directory
output_dir = Path("./output")
output_dir.mkdir(exist_ok=True)

# Load from TTS file - replace with your actual file
tts_file = "C:\\Users\\Joshua\\Documents\\My Games\\Tabletop Simulator\\Saves\\Saved Objects\\OblationCiel.json"  # Change this to your TTS file path

if Path(tts_file).exists():
    print(f"Loading deck from: {tts_file}")
    printer = GADeckPrinter()
    printer.load_from_tts(tts_file)
    
    print(f"Loaded {len(printer.cards)} unique cards")
    print("="*50)
    
    # Generate printable cards with ONLY images (no text, no borders)
    printer.create_printable_cards_pdf(str(output_dir / "tts_cards_printable.pdf"))
    
    print("\n✓ PDF generated successfully!")
    print(f"  - Printable Cards: {output_dir / 'tts_cards_printable.pdf'}")
else:
    print(f"❌ File not found: {tts_file}")
    print("\nUsage: Edit this script and set 'tts_file' to your TTS deck JSON path")
    print("Example: tts_file = 'C:/Users/Joshua/Documents/your_deck.json'")

