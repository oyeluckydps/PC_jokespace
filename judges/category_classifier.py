import asyncio
import dspy
import random
from typing import List, Tuple

from utilities.dspy_client import ClaudeClient
from judges.models import CategoryInfo
from judges.dspy_signatures import CategoryAssignmentSignature


class CategoryClassifier:
    """Handles category assignment for jokes"""
    
    def __init__(self, client: ClaudeClient, category_info_list: List[CategoryInfo], max_retries: int = 5):
        self.client = client
        self.category_info_list = category_info_list
        self.max_retries = max_retries
        self.category_predictor = dspy.Predict(CategoryAssignmentSignature)
    
    def _retry_on_error(self, func, *args, **kwargs):
        """Generic retry wrapper for sync functions with retries"""
        for attempt in range(self.max_retries + 1):  # +1 for initial attempt
            try:
                return func(*args, **kwargs)
            except Exception as e:
                if attempt == self.max_retries:
                    # No more retries
                    raise e
                else:
                    # Log retry attempt
                    print(f"\033[93m⚠️  Error: {str(e)[:50]}..., retrying in 2s\033[0m")
                    import time
                    time.sleep(2)
    
    async def classify_categories_async(self, joke_text: str) -> Tuple[List[str], bool]:
        """Assign joke to categories with enhanced prompt"""
        # Randomize category order to reduce position bias
        randomized_category_info = self.category_info_list.copy()
        random.shuffle(randomized_category_info)
        
        instruction = """
You are an expert comedy analyst tasked with categorizing jokes. Your goal is to identify ALL relevant categories that apply to this joke.

ANALYSIS FRAMEWORK:
Analyze the provided list of categories against the joke content. For each potentially relevant category, consider whether the joke's elements, themes, or comedic approach align with that category's definition and examples.

CATEGORIZATION RULES:
- A joke can belong to MULTIPLE categories
- Assign primary categories (core humor type) and secondary categories (content themes)
- Only mark as "Independent" if truly novel and doesn't fit ANY existing category
- Consider both obvious and subtle categorizations

AVOID THESE BIASES:
- Don't favor longer or shorter jokes
- Don't default to popular categories
- Don't let category order influence your decisions
- Consider less common but accurate categories
"""
        
        def classify():
            result = self.category_predictor(
                joke_text=joke_text,
                available_categories=str(randomized_category_info),
                instruction=instruction
            )
            
            # Parse categories
            is_independent = result.is_independent.lower() == 'true'
            
            if is_independent:
                categories = ["Independent"]
            else:
                # Extract category names from response
                categories = []
                for category_info in self.category_info_list:
                    if category_info.name.lower() in result.selected_categories.lower():
                        categories.append(category_info.name)
                
                # If no categories found but not marked independent, mark as independent
                if not categories:
                    categories = ["Independent"]
                    is_independent = True
            
            return categories, is_independent
        
        try:
            # Run synchronous DSPy call in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, lambda: self._retry_on_error(classify))
        except Exception as e:
            # Default to Independent on error
            return ["Independent"], True

    