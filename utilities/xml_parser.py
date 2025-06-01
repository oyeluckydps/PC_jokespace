import xml.etree.ElementTree as ET
from typing import List, Dict, Optional, Tuple
from pathlib import Path
from pydantic import BaseModel
from judges.models import CategoryInfo

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
        for category in root.findall(".//Category"):
            name = category.get('Name')  # Changed from category.text to category.get('Name')
            if name:
                categories.append(name)
        
        return categories
    
    def parse_category_info(self) -> List[CategoryInfo]:
        """Parse criteria_category_of_jokes.xml and return list of CategoryInfo objects"""
        file_path = self.base_path / "criteria_category_of_jokes.xml"
        tree = self._load_xml_file(file_path)
        root = tree.getroot()
        
        category_info_list = []
        # Traverse all category elements regardless of hierarchy
        for category in root.findall(".//Category"):
            name = category.get('Name')
            description = category.get('Description', '')
            
            if name:
                # Extract examples
                examples = []
                for example in category.findall('Example'):
                    if example.text:
                        examples.append(example.text.strip())
                
                # Create CategoryInfo object with up to 2 examples
                category_info = CategoryInfo(
                    name=name,
                    description=description,
                    example1=examples[0] if len(examples) > 0 else "",
                    example2=examples[1] if len(examples) > 1 else ""
                )
                category_info_list.append(category_info)
        
        return category_info_list
    
    def parse_categories_with_descriptions(self) -> List[Tuple[str, str]]:
        """Parse criteria_category_of_jokes.xml and return list of (category_name, description) tuples"""
        file_path = self.base_path / "criteria_category_of_jokes.xml"
        tree = self._load_xml_file(file_path)
        root = tree.getroot()
        
        categories_with_descriptions = []
        # Traverse all category elements regardless of hierarchy
        for category in root.findall(".//Category"):
            name = category.get('Name')
            description = category.get('Description', '')
            if name:
                categories_with_descriptions.append((name, description))
        
        return categories_with_descriptions
    
    def parse_category_examples(self) -> Dict[str, List[str]]:
        """Parse criteria_category_of_jokes.xml and return dictionary of category examples"""
        file_path = self.base_path / "criteria_category_of_jokes.xml"
        tree = self._load_xml_file(file_path)
        root = tree.getroot()
        
        category_examples = {}
        # Traverse all category elements regardless of hierarchy
        for category in root.findall(".//Category"):
            name = category.get('Name')
            if name:
                examples = []
                for example in category.findall('Example'):
                    if example.text:
                        examples.append(example.text.strip())
                category_examples[name] = examples[:3]  # Limit to 3 examples
        
        return category_examples
    
    def parse_factors(self) -> Dict[str, List[Factor]]:
        """
        Parses the 'factors_to_judge_joke.xml' file to extract joke factors,
        organizing them by category.

        Returns:
            Dict[str, List[Factor]]: A dictionary where keys are category names
            (e.g., "Wordplay / Puns", "Animals") and values are lists of Factor objects
            belonging to that category.
        """
        file_path = self.base_path / "factors_to_judge_joke.xml"
        tree = self._load_xml_file(file_path)
        root = tree.getroot()

        factors_by_category: Dict[str, List[Factor]] = {}

        # Iterate through Criteria elements (Mechanism, Theme, Structure, etc.)
        # The XML structure has <Root><Criteria><Category><Factor>
        for criteria_elem in root.findall("Criteria"):
            # Iterate through Category elements within each Criteria
            for category_elem in criteria_elem.findall("Category"):
                category_name = category_elem.get('name')

                # Initialize list for this category if it doesn't exist yet
                if category_name not in factors_by_category:
                    factors_by_category[category_name] = []

                # Now iterate through Factor elements within the current Category
                for factor_elem in category_elem.findall("Factor"):
                    factor_name = factor_elem.get('name')

                    # Correctly retrieve text from the 'Explanation' tag
                    explanation_text = factor_elem.findtext('Explanation', '').strip()

                    # Correctly retrieve text from 'GoodExample' and 'BadExample' tags.
                    # Since Factor expects List[str], wrap single examples in a list.
                    good_example_text = factor_elem.findtext('GoodExample', '').strip()
                    positive_examples_list = [good_example_text] if good_example_text else []

                    bad_example_text = factor_elem.findtext('BadExample', '').strip()
                    negative_examples_list = [bad_example_text] if bad_example_text else []

                    # Create a Factor object and assign the correct category_name
                    factor = Factor(
                        name=factor_name,
                        category=category_name, # This is the crucial fix: get from parent Category
                        description=explanation_text,
                        positive_examples=positive_examples_list,
                        negative_examples=negative_examples_list
                    )

                    factors_by_category[category_name].append(factor)

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
    
    def parse_random_topics_from_generator(self) -> List[str]:
        """Parse random_funny_topics.xml from generator folder"""
        try:
            file_path = Path("generator") / "random_funny_topics.xml"
            tree = self._load_xml_file(file_path)
            root = tree.getroot()
            
            topics = []
            # Parse Topic elements within FunnyJokeSeeds
            for topic_elem in root.findall(".//Topic"):
                if topic_elem.text:
                    topics.append(topic_elem.text.strip())
            
            return topics if topics else ["Banana", "Coffee", "Monday", "Pizza", "Cats"]
            
        except Exception as e:
            print(f"Warning: Could not parse random topics: {e}")
            # Return fallback topics
            return ["Banana", "Coffee", "Monday", "Pizza", "Cats"]