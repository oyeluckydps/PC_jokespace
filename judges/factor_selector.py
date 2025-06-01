import asyncio
import random
import copy
import dspy
from typing import List, Dict

from utilities.dspy_client import ClaudeClient
from judges.models import CategoryFactor, FactorData, FactorDescription, CategoryFactorForDSPy
from judges.dspy_signatures import FactorSelectionSignature


class FactorSelector:
    """Handles factor selection for jokes based on categories with bias mitigation"""
    
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
    
    def _convert_to_dspy_format(self, relevant_categories: List[CategoryFactor]) -> List[CategoryFactorForDSPy]:
        """
        Convert CategoryFactor objects to CategoryFactorForDSPy format containing only factor names and descriptions.
        """
        dspy_categories = []
        
        for category in relevant_categories:
            # Convert FactorData to FactorDescription (name and description only)
            factor_descriptions = []
            for factor_data in category.factors:
                factor_desc = FactorDescription(
                    name=factor_data.name,
                    description=factor_data.description
                )
                factor_descriptions.append(factor_desc)
            
            # Create CategoryFactorForDSPy object
            dspy_category = CategoryFactorForDSPy(
                name=category.name,
                description=category.description,
                factors=factor_descriptions
            )
            dspy_categories.append(dspy_category)
        
        return dspy_categories
    
    def _randomize_categories_and_factors(self, relevant_categories: List[CategoryFactorForDSPy]) -> List[CategoryFactorForDSPy]:
        """
        Randomize the order of categories and factors within each category to prevent position bias.
        Creates deep copies to avoid modifying original data structures.
        """
        try:
            # Create deep copies to avoid modifying original data
            randomized_categories = copy.deepcopy(relevant_categories)
            
            # Randomize the order of categories
            random.shuffle(randomized_categories)
            
            # Randomize the order of factors within each category
            for category in randomized_categories:
                if category.factors:
                    random.shuffle(category.factors)
            
            return randomized_categories
            
        except Exception as e:
            print(f"\033[93m⚠️  Error in randomization: {str(e)}, using original order\033[0m")
            return relevant_categories
    
    def _create_enhanced_instruction(self) -> str:
        """
        Create comprehensive instruction with bias mitigation guidelines and validation questions.
        """
        return """You are an expert joke evaluator tasked with selecting the most relevant factors for evaluating a specific joke. Your goal is to identify factors that will provide meaningful, measurable insights into what makes this joke funny or not funny.

CRITICAL BIAS MITIGATION GUIDELINES:
1. IGNORE FACTOR ORDER: The factors are presented in random order. Do not favor factors based on their position in the list.
2. AVOID LENGTH BIAS: Do not prefer factors with longer or more detailed descriptions over simpler ones.
3. AVOID CONCRETENESS BIAS: Do not automatically favor factors that sound more technical or specific.
4. FOCUS ON RELEVANCE: Select factors based solely on their relevance to THIS specific joke, not on general importance.

MANDATORY VALIDATION QUESTIONS:
For each potential factor, you MUST consider these three validation questions:
1. "Does this factor directly relate to what makes this joke funny?" - The factor must address a specific comedic element present in the joke.
2. "Is this factor measurable in this specific joke?" - You must be able to observe and evaluate this factor based on the joke's content.
3. "Would this factor be important in rating the joke on the scale of funniness?" - The factor should contribute meaningfully to understanding the joke's comedic effectiveness.

FACTOR SELECTION BEST PRACTICES:
- Select one or more factors that would be applicable to rate a the joke.
- Select only those factors that capture the primary comedic mechanism of the joke
- Include factors that address strengths of the joke.
- Avoid redundant factors that measure similar aspects
- Consider the joke's specific style, setup, and punchline structure

DECISION PROCESS:
1. First, identify the primary comedic mechanism(s) in the joke
2. Map this mechanism to relevant factors from the available categories
3. Apply the three validation questions to each potential factor
4. Select only factors that pass all validation criteria
5. Ensure your selection provides comprehensive but focused coverage.

Your factor selection should enable a thorough, unbiased evaluation of this specific joke's comedic effectiveness. Focus on what makes this particular joke work (or not work) rather than applying generic evaluation criteria."""

    async def select_factors_per_category_async(self, joke_text: str, categories: List[str], 
                                               is_independent: bool) -> Dict:
        """Select relevant factors for each category with enhanced bias mitigation"""
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
            # Convert to DSPy format (name and description only)
            dspy_categories = self._convert_to_dspy_format(relevant_categories)
            
            # Randomize categories and factors to prevent position bias
            randomized_categories = self._randomize_categories_and_factors(dspy_categories)
            
            # Create enhanced instruction with bias mitigation
            enhanced_instruction = self._create_enhanced_instruction()
            
            # Make the DSPy call to select factors
            def select():
                result = self.factor_selector(
                    joke_text=joke_text,
                    relevant_categories=randomized_categories,
                    instruction=enhanced_instruction
                )
                
                # Extract and validate factor names from the result
                selected = []
                if result.relevant_factors:
                    import re
                    factor_names = re.split(r'[,;\n]', result.relevant_factors)
                    
                    # Build lookup for case-insensitive matching from original (non-randomized) categories
                    factor_lookup = {}
                    for category_factor in relevant_categories:  # Use original categories for lookup
                        for factor_data in category_factor.factors:
                            factor_lookup[factor_data.name.lower()] = factor_data.name
                    
                    # Clean and validate factor names
                    for name in factor_names:
                        clean_name = name.strip().strip('"\'')
                        if clean_name and clean_name.lower() in factor_lookup:
                            selected.append(factor_lookup[clean_name.lower()])
                
                return selected
            
            try:
                # Build a lookup dictionary for faster factor finding using original categories
                factor_lookup = {}
                for category_factor in relevant_categories:  # Use original categories for lookup
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

