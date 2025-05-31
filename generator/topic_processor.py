"""Topic processing and parsing functionality"""

import random
from pathlib import Path
from utilities.xml_parser import XMLConfigParser
from utilities.generator_utils import clean_topic_with_whitelist


def get_random_topic() -> set:
    """Parse random topics XML and select one randomly"""
    try:
        # Parse random_funny_topics.xml from generator folder
        parser = XMLConfigParser(base_path="generator")
        topics = parser.parse_random_topics_from_generator()
        
        if topics:
            # Randomly select one topic
            selected = random.choice(topics)
            # Apply whitelist cleaning
            cleaned = clean_topic_with_whitelist(selected)
            if cleaned:
                return {cleaned}
    except Exception as e:
        print(f"Warning: Could not parse random topics: {e}")
    
    # Fallback topic
    return {"Banana"}


def process_user_input(user_input: str) -> set:
    """Process user input into standardized topic set"""
    # Handle empty input
    if not user_input or not user_input.strip():
        return get_random_topic()
    
    # Split by commas and process each topic
    topics = set()
    for topic in user_input.split(','):
        cleaned = clean_topic_with_whitelist(topic)
        if cleaned:
            topics.add(cleaned)
    
    # If no valid topics after cleaning, use random
    if not topics:
        return get_random_topic()
    
    return topics

    