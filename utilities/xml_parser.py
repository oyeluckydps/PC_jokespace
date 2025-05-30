import xml.etree.ElementTree as ET
from typing import List, Dict, Optional, Tuple
from pathlib import Path
from pydantic import BaseModel

class Factor(BaseModel):
    name: str
    category: str
    description: str
    positive_examples: List[str]
    negative_examples: List[str]

class Category(BaseModel):
    name: str
    factors: List[Factor]

class ExampleData(BaseModel):
    good_jokes: List[str]
    bad_jokes: List[str]

class JokeData(BaseModel):
    id: int
    text: str

class XMLConfigParser:
    def __init__(self, base_path: str = ""):
        """Initialize parser with base path for finding XML configuration files"""
        self.base_path = Path(base_path)
    
    def parse_categories(self) -> List[str]:
        """Parse criteria_category_of_jokes.xml and return flat list of category names"""
        file_path = self.base_path / "criteria_category_of_jokes.xml"
        tree = self._load_xml_file(file_path)
        root = tree.getroot()
        
        categories = []
        # Traverse all category elements regardless of hierarchy
        for category in root.findall(".//category"):
            name = category.get('name')
            if name:
                categories.append(name)
        
        return categories
    
    def parse_factors(self) -> Dict[str, List[Factor]]:
        """Parse factors_to_judge_joke.xml and organize by category"""
        file_path = self.base_path / "factors_to_judge_joke.xml"
        tree = self._load_xml_file(file_path)
        root = tree.getroot()
        
        factors_by_category = {}
        
        for factor_elem in root.findall(".//factor"):
            factor_name = factor_elem.get('name')
            category = factor_elem.get('category')
            description = factor_elem.findtext('description', '').strip()
            
            # Parse positive examples
            positive_examples = []
            pos_examples = factor_elem.find('positive_examples')
            if pos_examples is not None:
                for example in pos_examples.findall('example'):
                    positive_examples.append(example.text.strip())
            
            # Parse negative examples
            negative_examples = []
            neg_examples = factor_elem.find('negative_examples')
            if neg_examples is not None:
                for example in neg_examples.findall('example'):
                    negative_examples.append(example.text.strip())
            
            factor = Factor(
                name=factor_name,
                category=category,
                description=description,
                positive_examples=positive_examples,
                negative_examples=negative_examples
            )
            
            if category not in factors_by_category:
                factors_by_category[category] = []
            factors_by_category[category].append(factor)
        
        return factors_by_category
    
    def parse_examples(self) -> ExampleData:
        """Parse good_vs_bad_joke.xml for few-shot examples"""
        file_path = self.base_path / "judges" / "good_vs_bad_joke.xml"
        tree = self._load_xml_file(file_path)
        root = tree.getroot()
        
        good_jokes = []
        bad_jokes = []
        
        # Parse good jokes
        good_section = root.find('good_jokes')
        if good_section is not None:
            for joke in good_section.findall('joke'):
                joke_text = joke.text.strip() if joke.text else ""
                if joke_text:
                    good_jokes.append(joke_text)
        
        # Parse bad jokes
        bad_section = root.find('bad_jokes')
        if bad_section is not None:
            for joke in bad_section.findall('joke'):
                joke_text = joke.text.strip() if joke.text else ""
                if joke_text:
                    bad_jokes.append(joke_text)
        
        # Limit to 5 each as specified
        return ExampleData(
            good_jokes=good_jokes[:5],
            bad_jokes=bad_jokes[:5]
        )
    
    def parse_jokes(self, jokes_file_path: str) -> List[JokeData]:
        """Parse input jokes XML file with corrected structure"""
        try:
            tree = ET.parse(jokes_file_path)
            root = tree.getroot()
            
            jokes = []
            for i, joke_elem in enumerate(root.findall('joke')):
                # Get id attribute
                joke_id = joke_elem.get('id')
                # Get text content directly from joke element
                joke_text = joke_elem.text
                
                if joke_id and joke_text:
                    try:
                        jokes.append(JokeData(
                            id=int(joke_id),
                            text=joke_text.strip()
                        ))
                    except ValueError:
                        print(f"Warning: Skipping invalid joke at position {i} - invalid id format")
                else:
                    print(f"Warning: Skipping invalid joke at position {i} - missing id or text")
            
            return jokes
            
        except ET.ParseError as e:
            print(f"\033[91mError parsing jokes file: {str(e)}\033[0m")
            return []
        except FileNotFoundError:
            print(f"\033[91mJokes file not found: {jokes_file_path}\033[0m")
            return []
    
    def _load_xml_file(self, filename: Path) -> ET.ElementTree:
        """Generic XML file loader with error handling"""
        if not filename.exists():
            raise FileNotFoundError(f"Configuration file not found: {filename}")
        
        try:
            return ET.parse(filename)
        except ET.ParseError as e:
            raise ValueError(f"Error parsing XML file {filename}: {str(e)}")
    
    