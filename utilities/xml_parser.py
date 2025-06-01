import xml.etree.ElementTree as ET
from typing import List, Dict, Optional, Tuple
from pathlib import Path
from judges.models import (
    CategoryInfo, FactorData, CategoryFactor, 
    ExampleData, JokeData
)

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
    
    def parse_category_factors(self) -> Dict[str, CategoryFactor]:
        """
        Parse factors_to_judge_joke.xml and return CategoryFactor objects with associated factors.
        
        Returns:
            Dict[str, CategoryFactor]: Dictionary mapping category names to CategoryFactor objects
        """
        file_path = self.base_path / "factors_to_judge_joke.xml"
        tree = self._load_xml_file(file_path)
        root = tree.getroot()

        category_factors: Dict[str, CategoryFactor] = {}

        # First, get category descriptions from criteria_category_of_jokes.xml
        category_descriptions = {}
        try:
            category_info_list = self.parse_category_info()
            for cat_info in category_info_list:
                category_descriptions[cat_info.name] = cat_info.description
        except:
            # If we can't load descriptions, continue without them
            pass

        # Iterate through Criteria elements (Mechanism, Theme, Structure, etc.)
        for criteria_elem in root.findall("Criteria"):
            # Iterate through Category elements within each Criteria
            for category_elem in criteria_elem.findall("Category"):
                category_name = category_elem.get('name')
                
                if not category_name:
                    continue

                # Get category description (from criteria file or empty string)
                category_description = category_descriptions.get(category_name, '')

                # Create list of FactorData objects for this category
                factor_data_list = []

                # Iterate through Factor elements within the current Category
                for factor_elem in category_elem.findall("Factor"):
                    factor_name = factor_elem.get('name')

                    # Get factor description from Explanation tag
                    explanation_text = factor_elem.findtext('Explanation', '').strip()

                    # Get positive and negative examples
                    good_example_text = factor_elem.findtext('GoodExample', '').strip()
                    positive_examples = [good_example_text] if good_example_text else []

                    bad_example_text = factor_elem.findtext('BadExample', '').strip()
                    negative_examples = [bad_example_text] if bad_example_text else []

                    # Create FactorData object
                    factor_data = FactorData(
                        name=factor_name,
                        description=explanation_text,
                        positive_examples=positive_examples,
                        negative_examples=negative_examples
                    )

                    factor_data_list.append(factor_data)

                # Create CategoryFactor object
                category_factor = CategoryFactor(
                    name=category_name,
                    description=category_description,
                    factors=factor_data_list
                )

                category_factors[category_name] = category_factor

        return category_factors
    
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