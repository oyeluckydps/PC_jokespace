"""Utility functions for joke generation"""

import re
from pathlib import Path
from typing import List, Union
from generator.models import FirstOrderTriplet, HigherOrderGroup


def format_topic_set_for_prompt(topic_set: set) -> str:
    """Convert topic set to natural language for prompts"""
    topics_list = sorted(list(topic_set))
    
    if len(topics_list) == 1:
        return f"the topic: {topics_list[0]}"
    elif len(topics_list) == 2:
        return f"the topics: {topics_list[0]} and {topics_list[1]}"
    else:
        # Oxford comma for 3+ topics
        all_but_last = ", ".join(topics_list[:-1])
        return f"the topics: {all_but_last}, and {topics_list[-1]}"


def combine_all_contexts(
    first_order_triplets: List[FirstOrderTriplet],
    higher_order_groups: List[HigherOrderGroup]
    ) -> List[Union[FirstOrderTriplet, HigherOrderGroup]]:
    """Combine all contexts into a single list for processing"""
    combined = []
    
    # Add first-order triplets
    combined.extend(first_order_triplets)
    
    # Add higher-order groups
    combined.extend(higher_order_groups)
    
    return combined


def ensure_directory_exists(directory_path: str) -> str:
    """Create directory if it doesn't exist"""
    path = Path(directory_path)
    try:
        path.mkdir(parents=True, exist_ok=True)
        return str(path.absolute())
    except Exception as e:
        raise RuntimeError(f"Failed to create directory {directory_path}: {e}")


def clean_topic_with_whitelist(topic: str) -> str:
    """Apply whitelist filtering to topic"""
    # Keep only alphanumeric, spaces, and hyphens
    cleaned = re.sub(r'[^a-zA-Z0-9\s\-]', '', topic)
    # Strip and normalize whitespace
    cleaned = ' '.join(cleaned.split())
    return cleaned