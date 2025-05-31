"""Format jokes to XML matching sample_jokes.xml structure"""

import xml.etree.ElementTree as ET
import xml.sax.saxutils as saxutils
from xml.dom import minidom
from pathlib import Path
from typing import List
from generator.generator_models import JokePortfolio, GeneratedJoke
from utilities.generator_utils import ensure_directory_exists


def format_jokes_to_xml(joke_portfolio: JokePortfolio, output_filename: str, output_dir: str) -> str:
    """Format jokes into XML exactly matching sample_jokes.xml"""
    
    # Ensure output directory exists
    output_path = ensure_directory_exists(output_dir)
    
    # Not required because the jokes already have an ID. # Assign IDs to jokes
    # jokes_with_ids = assign_joke_ids(joke_portfolio.jokes)
    
    # Create XML structure
    xml_content = create_xml_structure(joke_portfolio)
    
    # Write to file
    output_file = Path(output_path) / output_filename
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(xml_content)
    
    print(f"Jokes written to: {output_file}")
    return str(output_file)


def create_xml_structure(joke_portfolio: List[GeneratedJoke]) -> str:
    """Create XML matching sample_jokes.xml format"""
   
    # Create root element
    root = ET.Element("jokes")
   
    # Add each joke
    for joke in joke_portfolio.jokes:
        joke_elem = ET.SubElement(root, "joke")
        joke_elem.set("id", str(joke.id))
        # Escape special characters in joke text
        joke_elem.text = saxutils.escape(joke.text)
   
    # Convert to string with proper formatting
    xml_str = ET.tostring(root, encoding='unicode')
   
    # Add XML declaration and format with proper indentation
    dom = minidom.parseString(xml_str)
    pretty_xml = dom.toprettyxml(indent="  ")
    
    # Remove the first line (minidom adds its own XML declaration)
    lines = pretty_xml.split('\n')[1:]
    
    # Add our XML declaration and join
    final_xml = '<?xml version="1.0" encoding="UTF-8"?>\n' + '\n'.join(lines)
   
    return final_xml

    