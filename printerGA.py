"""
Grand Archive Deck PDF Generator
Creates a printable PDF for a Grand Archive card game deck
Supports Tabletop Simulator JSON deck files
"""

from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT
import json
from pathlib import Path
from io import BytesIO
import requests
from urllib.parse import urlparse
import os
from PIL import Image as PILImage


class GADeckPrinter:
    """Generate PDF files for Grand Archive deck printing"""
    
    def __init__(self, deck_name="GA_Deck", cards_per_row=3, cards_per_column=3):
        """
        Initialize the deck printer
        
        Args:
            deck_name: Name of the deck for the PDF title
            cards_per_row: Number of cards per row
            cards_per_column: Number of cards per column
        """
        self.deck_name = deck_name
        self.cards_per_row = cards_per_row
        self.cards_per_column = cards_per_column
        self.cards = []
        self.card_images = {}  # Store card images
        self.image_cache = {}  # Cache downloaded images
        
    def add_card(self, name, card_type, cost=0, power=0, toughness=0, ability="", quantity=1, image_url=""):
        """
        Add a card to the deck
        
        Args:
            name: Card name
            card_type: Type of card (Unit, Spell, etc.)
            cost: Casting cost
            power: Card power
            toughness: Card toughness
            ability: Card ability text
            quantity: Number of copies
            image_url: URL to card image
        """
        card = {
            "name": name,
            "type": card_type,
            "cost": cost,
            "power": power,
            "toughness": toughness,
            "ability": ability,
            "quantity": quantity,
            "image_url": image_url
        }
        self.cards.append(card)
        if image_url:
            self.card_images[name] = image_url
    
    def load_from_json(self, json_file):
        """Load deck from JSON file"""
        with open(json_file, 'r') as f:
            data = json.load(f)
        
        self.deck_name = data.get("deck_name", self.deck_name)
        for card in data.get("cards", []):
            self.add_card(**card)
    
    def load_from_tts(self, tts_json_file):
        """
        Load deck from Tabletop Simulator JSON save file
        
        Args:
            tts_json_file: Path to TTS save file
        """
        with open(tts_json_file, 'r') as f:
            tts_data = json.load(f)
        
        # Get the main deck object
        object_states = tts_data.get("ObjectStates", [])
        if not object_states:
            print("No ObjectStates found in TTS file")
            return
        
        deck_obj = object_states[0]
        self.deck_name = deck_obj.get("Nickname", "GA_Deck")
        
        # Extract CustomDeck information
        custom_deck = deck_obj.get("CustomDeck", {})
        card_images_map = {}
        
        # Map deck IDs to image URLs
        for deck_id, deck_info in custom_deck.items():
            face_url = deck_info.get("FaceURL", "")
            card_images_map[deck_id] = face_url
        
        # Process contained objects (individual cards)
        contained_objects = deck_obj.get("ContainedObjects", [])
        card_count = {}
        
        for card_obj in contained_objects:
            card_name = card_obj.get("Nickname", "Unknown Card")
            card_desc = card_obj.get("Description", "")
            card_id = card_obj.get("CardID", 0)
            
            # Get the deck ID from CardID (first 4 digits represent deck)
            deck_id_key = str(card_id // 100)
            image_url = card_images_map.get(deck_id_key, "")
            
            # Count duplicates
            if card_name not in card_count:
                card_count[card_name] = 0
                self.add_card(
                    name=card_name,
                    card_type="Card",
                    ability=card_desc,
                    image_url=image_url,
                    quantity=1
                )
            else:
                card_count[card_name] += 1
                # Update quantity for existing card
                for card in self.cards:
                    if card["name"] == card_name:
                        card["quantity"] += 1
                        break
    
    def load_from_json(self, json_file):
        """Load deck from JSON file"""
        with open(json_file, 'r') as f:
            data = json.load(f)
        
        self.deck_name = data.get("deck_name", self.deck_name)
        for card in data.get("cards", []):
            self.add_card(**card)
    
    def save_to_json(self, json_file):
        """Save deck to JSON file"""
        data = {
            "deck_name": self.deck_name,
            "cards": self.cards
        }
        with open(json_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def create_card_box(self, c, x, y, width, height, card):
        """Draw a single card image on the canvas (images only, no text)"""
        # Try to download and draw image
        if card.get("image_url"):
            try:
                img = self._download_image(card["image_url"])
                if img:
                    # Use full card dimensions (fill entire box)
                    img_width = width
                    img_height = height
                    
                    # Save image temporarily and draw
                    temp_img_path = f"/tmp/card_{id(card)}.png"
                    os.makedirs("/tmp", exist_ok=True)
                    img.save(temp_img_path)
                    c.drawImage(temp_img_path, x, y, width=img_width, height=img_height)
                    
                    # Clean up
                    try:
                        os.remove(temp_img_path)
                    except:
                        pass
            except Exception as e:
                print(f"  Could not embed image: {e}")
    
    def _wrap_text(self, text, char_limit):
        """Wrap text to specified character limit"""
        words = text.split()
        lines = []
        current_line = ""
        
        for word in words:
            if len(current_line) + len(word) + 1 <= char_limit:
                current_line += word + " "
            else:
                if current_line:
                    lines.append(current_line.strip())
                current_line = word + " "
        
        if current_line:
            lines.append(current_line.strip())
        
        return lines
    
    def _download_image(self, url, timeout=10):
        """
        Download image from URL
        
        Args:
            url: Image URL
            timeout: Request timeout in seconds
            
        Returns:
            PIL Image object or None if download fails
        """
        try:
            # Check cache first
            if url in self.image_cache:
                return self.image_cache[url]
            
            response = requests.get(url, timeout=timeout)
            response.raise_for_status()
            
            # Convert to PIL Image
            img = PILImage.open(BytesIO(response.content))
            self.image_cache[url] = img
            print(f"  Downloaded: {url[:60]}...")
            return img
        except Exception as e:
            print(f"  Warning: Could not download image from {url}: {e}")
            return None
    
    def create_deck_list_pdf(self, output_file):
        """Create a PDF with a deck list table"""
        doc = SimpleDocTemplate(output_file, pagesize=letter)
        story = []
        styles = getSampleStyleSheet()
        
        # Title
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#1f4788'),
            spaceAfter=30,
            alignment=TA_CENTER
        )
        story.append(Paragraph(f"{self.deck_name} - Deck List", title_style))
        
        # Deck statistics
        total_cards = sum(card["quantity"] for card in self.cards)
        stats_style = ParagraphStyle(
            'Stats',
            parent=styles['Normal'],
            fontSize=12,
            alignment=TA_CENTER,
            spaceAfter=20
        )
        story.append(Paragraph(f"Total Cards: {total_cards} | Unique Cards: {len(self.cards)}", stats_style))
        
        # Create table data
        table_data = [["Card Name", "Type", "Cost", "Power", "Toughness", "Quantity", "Image URL"]]
        for card in self.cards:
            table_data.append([
                card["name"],
                card["type"],
                str(card["cost"]),
                str(card["power"]),
                str(card["toughness"]),
                str(card["quantity"]),
                card.get("image_url", "")[:50] + "..." if card.get("image_url", "") else ""
            ])
        
        # Create table
        table = Table(table_data, colWidths=[1.5*inch, 1*inch, 0.6*inch, 0.6*inch, 0.8*inch, 0.6*inch, 1.2*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1f4788')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
        ]))
        
        story.append(table)
        doc.build(story)
        print(f"✓ Deck list PDF created: {output_file}")
    
    def create_printable_cards_pdf(self, output_file):
        """Create a PDF with card layouts for printing"""
        page_width, page_height = letter
        margin = 0.5 * inch
        card_width = (page_width - 2 * margin) / self.cards_per_row
        card_height = (page_height - 2 * margin) / self.cards_per_column
        
        c = canvas.Canvas(output_file, pagesize=letter)
        card_index = 0
        page_num = 1
        total_cards = sum(card["quantity"] for card in self.cards)
        print(f"\nGenerating printable PDF with {total_cards} cards...")
        
        for card in self.cards:
            for qty in range(card["quantity"]):
                if card_index >= self.cards_per_row * self.cards_per_column:
                    c.showPage()
                    card_index = 0
                    page_num += 1
                    print(f"  Page {page_num}...")
                
                row = card_index // self.cards_per_row
                col = card_index % self.cards_per_row
                
                x = margin + col * card_width
                y = page_height - margin - (row + 1) * card_height
                
                self.create_card_box(c, x, y, card_width, card_height, card)
                card_index += 1
        
        c.save()
        print(f"✓ Printable cards PDF created: {output_file}")


def example_deck():
    """Create an example Grand Archive deck"""
    printer = GADeckPrinter(deck_name="Sample GA Deck")
    
    # Add sample cards
    printer.add_card("Fire Elemental", "Unit", cost=3, power=3, toughness=2, 
                     ability="When Fire Elemental enters, deal 1 damage to target opponent.", quantity=2)
    printer.add_card("Healing Potion", "Spell", cost=1, ability="Target player gains 3 life.", quantity=3)
    printer.add_card("Sword Master", "Unit", cost=4, power=4, toughness=3,
                     ability="First Strike: This unit deals damage before combat.", quantity=1)
    printer.add_card("Mystic Shield", "Spell", cost=2, ability="Target unit gains +0/+2 until end of turn.", quantity=4)
    printer.add_card("Dark Summoning", "Spell", cost=5, ability="Search your deck for a unit and put it into play.", quantity=2)
    
    return printer


if __name__ == "__main__":
    # Create example deck
    printer = example_deck()
    
    # Create output directory if needed
    output_dir = Path("./output")
    output_dir.mkdir(exist_ok=True)
    
    # Generate PDFs
    printer.create_deck_list_pdf(str(output_dir / "deck_list.pdf"))
    printer.create_printable_cards_pdf(str(output_dir / "printable_cards.pdf"))
    printer.save_to_json(str(output_dir / "deck.json"))
    
    print("\n✓ All files generated successfully!")
    
    # Example: Load from TTS file
    print("\n" + "="*50)
    print("To load from a Tabletop Simulator file:")
    print("="*50)
    print("tts_printer = GADeckPrinter()")
    print("tts_printer.load_from_tts('your_tts_save.json')")
    print("tts_printer.create_deck_list_pdf('output/tts_deck_list.pdf')")
    print("tts_printer.create_printable_cards_pdf('output/tts_cards.pdf')")
