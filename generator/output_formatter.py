"""Format jokes to XML matching sample_jokes.xml structure"""

import xml.etree.ElementTree as ET
import xml.sax.saxutils as saxutils
from pathlib import Path
from typing import List
from generator.generator_models import JokePortfolio, GeneratedJoke
from utilities.generator_utils import ensure_directory_exists


def format_jokes_to_xml(joke_portfolio: JokePortfolio, output_filename: str, output_dir: str) -> str:
    """Format jokes into XML exactly matching sample_jokes.xml"""
    
    # Ensure output directory exists
    output_path = ensure_directory_exists(output_dir)
    
    # Assign IDs to jokes
    jokes_with_ids = assign_joke_ids(joke_portfolio.jokes)
    
    # Create XML structure
    xml_content = create_xml_structure(jokes_with_ids)
    
    # Write to file
    output_file = Path(output_path) / output_filename
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(xml_content)
    
    print(f"Jokes written to: {output_file}")
    return str(output_file)


def assign_joke_ids(jokes: List[GeneratedJoke]) -> List[GeneratedJoke]:
    """Assign sequential integer IDs starting from 1"""
    for i, joke in enumerate(jokes, 1):
        joke.id = i
    return jokes


def create_xml_structure(jokes_with_ids: List[GeneratedJoke]) -> str:
    """Create XML matching sample_jokes.xml format"""
    
    # Create root element
    root = ET.Element("jokes")
    
    # Add each joke
    for joke in jokes_with_ids:
        joke_elem = ET.SubElement(root, "joke")
        joke_elem.set("id", str(joke.id))
        # Escape special characters in joke text
        joke_elem.text = saxutils.escape(joke.text)
    
    # Convert to string with proper formatting
    xml_str = ET.tostring(root, encoding='unicode')
    
    # Add XML declaration and format
    final_xml = '<?xml version="1.0" encoding="UTF-8"?>\n' + xml_str
    
    return final_xml