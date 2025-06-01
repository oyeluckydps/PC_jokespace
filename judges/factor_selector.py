import asyncio
import dspy
from typing import List, Dict

from utilities.dspy_client import ClaudeClient
from judges.models import CategoryFactor, FactorData
from judges.dspy_signatures import FactorSelectionSignature


class FactorSelector:
    """Handles factor selection for jokes based on categories"""
    
    def __init__(self, client: ClaudeClient, category_factors: Dict[str, CategoryFactor], max_retries: int = 5):
        self.client = client
        self.category_factors = category_factors
        self.max_retries = max_retries
        self.factor_selector = dspy.Predict(FactorSelectionSignature)
    
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
    
    async def select_factors_per_category_async(self, joke_text: str, categories: List[str], 
                                               is_independent: bool) -> Dict:
        """Select relevant factors for each category"""
        all_factors = []
        dropped_categories = []
        factor_objects = {}  # Track factor objects for scoring
        
        # Determine which categories to use
        if "Independent" in categories:
            # For Independent, consider all factors from all categories
            relevant_categories = list(self.category_factors.values())
        else:
            # Get CategoryFactor objects for the selected categories
            relevant_categories = []
            for category_name in categories:
                if category_name in self.category_factors:
                    relevant_categories.append(self.category_factors[category_name])
                else:
                    dropped_categories.append(category_name)
        
        # If we have categories to work with, select factors
        if relevant_categories:
            # Make the DSPy call to select factors
            def select():
                result = self.factor_selector(
                    joke_text=joke_text,
                    relevant_categories=relevant_categories,
                    instruction="You are provided with categories and their associated factors. Choose only the factors that are most relevant to evaluating this specific joke. The factors must be directly observable and measurable in this joke."
                )
                
                # Extract and validate factor names from the result
                selected = []
                if result.relevant_factors:
                    import re
                    factor_names = re.split(r'[,;\n]', result.relevant_factors)
                    
                    # Build lookup for case-insensitive matching
                    factor_lookup = {}
                    for category_factor in relevant_categories:
                        for factor_data in category_factor.factors:
                            factor_lookup[factor_data.name.lower()] = factor_data.name
                    
                    # Clean and validate factor names
                    for name in factor_names:
                        clean_name = name.strip().strip('"\'')
                        if clean_name and clean_name.lower() in factor_lookup:
                            selected.append(factor_lookup[clean_name.lower()])
                
                return selected
            
            try:
                # Build a lookup dictionary for faster factor finding
                factor_lookup = {}
                for category_factor in relevant_categories:
                    for factor_data in category_factor.factors:
                        factor_lookup[factor_data.name.lower()] = factor_data
                
                # Run synchronous DSPy call in thread pool to avoid blocking
                loop = asyncio.get_event_loop()
                selected_factors = await loop.run_in_executor(None, lambda: self._retry_on_error(select))
                
                # Build factor objects mapping and all_factors list using lookup
                for factor_name in selected_factors:
                    if factor_name.lower() in factor_lookup:
                        factor_data = factor_lookup[factor_name.lower()]
                        all_factors.append(factor_data.name)  # Use the original name from factor_data
                        factor_objects[factor_data.name] = factor_data
                        
            except Exception as e:
                print(f"Error in factor selection: {e}")
        
        # Return factor objects along with other data
        return {
            'all_factors': all_factors,
            'dropped_categories': dropped_categories,
            'factor_objects': factor_objects
        }

    