import asyncio
import dspy
from typing import List, Dict

from utilities.dspy_client import ClaudeClient
from utilities.xml_parser import Factor
from judges.dspy_signatures import FactorSelectionSignature


class FactorSelector:
    """Handles factor selection for jokes based on categories"""
    
    def __init__(self, client: ClaudeClient, factors: Dict[str, List[Factor]], max_retries: int = 5):
        self.client = client
        self.factors = factors
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
        
        if "Independent" in categories:
            # For Independent, consider all factors from all categories
            available_factors = []
            for cat_factors in self.factors.values():
                available_factors.extend(cat_factors)
        else:
            # Process each category
            tasks = []
            for category in categories:
                if category in self.factors:
                    tasks.append(self._select_category_factors_async(joke_text, category))
            
            if tasks:
                results = await asyncio.gather(*tasks)
                
                for i, category in enumerate(categories):
                    if category in self.factors:
                        selected_factors = results[i]
                        if selected_factors:
                            for factor_name in selected_factors:
                                # Find the factor object
                                for factor in self.factors[category]:
                                    if factor.name == factor_name:
                                        all_factors.append(factor_name)
                                        factor_objects[factor_name] = factor
                        else:
                            dropped_categories.append(category)
        
        # Handle Independent category
        if "Independent" in categories:
            # Select from all factors
            all_available_factors = []
            for cat_factors in self.factors.values():
                all_available_factors.extend(cat_factors)
            
            selected = await self._select_from_all_factors_async(joke_text, all_available_factors)
            for factor_name in selected:
                for factor in all_available_factors:
                    if factor.name == factor_name:
                        all_factors.append(factor_name)
                        factor_objects[factor_name] = factor
                        break
        
        # Return factor objects along with other data
        return {
            'all_factors': all_factors,
            'dropped_categories': dropped_categories,
            'factor_objects': factor_objects  # Include factor objects in return
        }
    
    async def _select_category_factors_async(self, joke_text: str, category: str) -> List[str]:
        """Select factors for a specific category"""
        if category not in self.factors:
            return []
        
        factors_info = []
        for factor in self.factors[category]:
            factors_info.append(f"{factor.name}: {factor.description}")
        
        factors_str = "\n".join(factors_info)
        
        def select():
            result = self.factor_selector(
                joke_text=joke_text,
                category=category,
                available_factors=factors_str
            )
            
            # Extract factor names
            selected = []
            for factor in self.factors[category]:
                if factor.name.lower() in result.relevant_factors.lower():
                    selected.append(factor.name)
            
            return selected
        
        try:
            # Run synchronous DSPy call in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, lambda: self._retry_on_error(select))
        except Exception as e:
            return []
    
    async def _select_from_all_factors_async(self, joke_text: str, all_factors: List[Factor]) -> List[str]:
        """Select from all available factors for Independent category"""
        factors_info = []
        for factor in all_factors:
            factors_info.append(f"{factor.name} ({factor.category}): {factor.description}")
        
        factors_str = "\n".join(factors_info[:20])  # Limit to prevent token overflow
        
        def select():
            result = self.factor_selector(
                joke_text=joke_text,
                category="Independent",
                available_factors=factors_str
            )
            
            # Extract factor names
            selected = []
            for factor in all_factors:
                if factor.name.lower() in result.relevant_factors.lower():
                    selected.append(factor.name)
            
            return selected[:10]  # Limit to 10 factors for Independent
        
        try:
            # Run synchronous DSPy call in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, lambda: self._retry_on_error(select))
        except Exception as e:
            return []

    