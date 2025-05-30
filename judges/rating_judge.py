import asyncio
from typing import List, Dict, Optional, Tuple
import dspy

from utilities.xml_parser import Category, Factor, ExampleData, JokeData
from utilities.dspy_client import ClaudeClient
from judges.models import (
    RatingResult, AdmissibilityResults, AdmissibilityCheck
)
from judges.dspy_signatures import (
    AdmissibilitySignature, CategoryAssignmentSignature,
    FactorSelectionSignature, FactorScoringSignature
)

class RatingJudge:
    def __init__(self, client: ClaudeClient, categories: List[str], 
                 factors: Dict[str, List[Factor]], examples: ExampleData,
                 max_retries: int = 5):
        """Initialize rating judge with parsed XML data"""
        self.client = client
        self.categories = categories
        self.factors = factors
        self.examples = examples
        self.max_retries = max_retries  # Store max retries for use in error handling
        
        # Initialize DSPy predictors
        self.admissibility_predictor = dspy.Predict(AdmissibilitySignature)
        self.category_predictor = dspy.Predict(CategoryAssignmentSignature)
        self.factor_selector = dspy.Predict(FactorSelectionSignature)
        self.factor_scorer = dspy.Predict(FactorScoringSignature)
    
    def evaluate_joke(self, joke: JokeData) -> RatingResult:
        """Synchronous wrapper for async evaluation"""
        return asyncio.run(self.evaluate_joke_async(joke))
    
    async def evaluate_joke_async(self, joke: JokeData) -> RatingResult:
        """Full evaluation pipeline"""
        # Step 1: Check admissibility
        admissibility_results = await self._check_all_admissibility_async(joke.text)
        
        # Initialize default result
        result = RatingResult(
            joke_id=joke.id,
            joke_text=joke.text,
            admissibility_results=admissibility_results,
            assigned_categories=[],
            dropped_categories=[],
            relevant_factors=[],
            factor_scores={},
            max_score=0,
            mean_score=0.0,
            overall_rating=0.0
        )
        
        # If not admissible, return early
        if not admissibility_results.is_admissible:
            return result
        
        # Step 2: Assign categories
        categories, is_independent = await self._classify_categories_async(joke.text)
        result.assigned_categories = categories
        
        # Step 3: Select factors per category
        factors_data = await self._select_factors_per_category_async(joke.text, categories, is_independent)
        result.relevant_factors = factors_data['all_factors']
        result.dropped_categories = factors_data['dropped_categories']
        factor_objects = factors_data['factor_objects']  # Get factor objects for scoring
        
        # Step 4: Score all factors
        if result.relevant_factors:
            factor_scores = await self._score_factors_async(
                joke.text, 
                result.relevant_factors,
                factor_objects  # Pass factor objects directly
            )
            result.factor_scores = factor_scores
            
            # Step 5: Calculate final ratings
            scores = list(factor_scores.values())
            result.max_score = max(scores) if scores else 0
            result.mean_score = sum(scores) / len(scores) if scores else 0.0
            result.overall_rating = (result.max_score*10 + result.mean_score +  len(scores)/5)/12   
            # Give some benefit for involving more factors and divide by 12 to normalize and bring the value below 5.
        
        return result
    
    async def _retry_on_error(self, func, *args, **kwargs):
        """Generic retry wrapper for async functions"""
        for attempt in range(self.max_retries + 1):  # +1 for initial attempt
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                if attempt == self.max_retries:
                    # No more retries
                    raise e
                else:
                    # Log retry attempt
                    print(f"\033[93m⚠️  Error: {str(e)[:50]}..., retrying in 2s\033[0m")
                    await asyncio.sleep(2)
    
    async def _check_all_admissibility_async(self, joke_text: str) -> AdmissibilityResults:
        """Run 5 admissibility checks in parallel"""
        # Define check functions
        check_tasks = [
            self._check_intent_async(joke_text),
            self._check_completeness_async(joke_text),
            self._check_appropriateness_async(joke_text),
            self._check_coherence_async(joke_text),
            self._check_accessibility_async(joke_text)
        ]
        
        # Run all checks in parallel
        results = await asyncio.gather(*check_tasks)
        
        # Compile results
        return AdmissibilityResults(
            intent_check=results[0],
            completeness_check=results[1],
            appropriateness_check=results[2],
            coherence_check=results[3],
            accessibility_check=results[4],
            is_admissible=all(r.passed for r in results)
        )
    
    async def _check_intent_async(self, joke_text: str) -> AdmissibilityCheck:
        """Check comedic intent with liberal evaluation"""
        instructions = """Liberal evaluation: Only reject if there is ABSOLUTELY NO comedic intent.
        Accept if there's ANY attempt at humor, wordplay, irony, or comedic structure.
        Even bad jokes or failed attempts at humor should PASS this check."""
        
        async def check():
            result = self.admissibility_predictor(
                joke_text=joke_text,
                check_type="intent",
                instruction_prompt=instructions
            )
            passed = result.passed.lower() == 'true'
            return AdmissibilityCheck(passed=passed, reasoning=result.reasoning)
        
        try:
            return await self._retry_on_error(check)
        except Exception as e:
            # If all retries fail, be liberal and pass
            return AdmissibilityCheck(passed=True, reasoning=f"Check failed after {self.max_retries} retries: {str(e)}")
    
    async def _check_completeness_async(self, joke_text: str) -> AdmissibilityCheck:
        """Check if joke is complete"""
        instructions = """Liberal evaluation: Only reject if SEVERELY incomplete.
        Accept if there's a setup and any form of conclusion, even if weak.
        One-liners, puns, and short jokes should PASS."""
        
        async def check():
            result = self.admissibility_predictor(
                joke_text=joke_text,
                check_type="completeness",
                instruction_prompt=instructions
            )
            passed = result.passed.lower() == 'true'
            return AdmissibilityCheck(passed=passed, reasoning=result.reasoning)
        
        try:
            return await self._retry_on_error(check)
        except Exception as e:
            return AdmissibilityCheck(passed=True, reasoning=f"Check failed after {self.max_retries} retries: {str(e)}")
    
    async def _check_appropriateness_async(self, joke_text: str) -> AdmissibilityCheck:
        """Check appropriateness"""
        instructions = """Liberal evaluation: Only reject EXTREMELY offensive content.
        Accept edgy humor, dark humor, adult humor, political humor.
        Only reject if promoting hate, violence, or extreme harm."""
        
        async def check():
            result = self.admissibility_predictor(
                joke_text=joke_text,
                check_type="appropriateness",
                instruction_prompt=instructions
            )
            passed = result.passed.lower() == 'true'
            return AdmissibilityCheck(passed=passed, reasoning=result.reasoning)
        
        try:
            return await self._retry_on_error(check)
        except Exception as e:
            return AdmissibilityCheck(passed=True, reasoning=f"Check failed after {self.max_retries} retries: {str(e)}")
    
    async def _check_coherence_async(self, joke_text: str) -> AdmissibilityCheck:
        """Check logical coherence"""
        instructions = """Liberal evaluation: Only reject if COMPLETELY incoherent.
        Accept if there's any logical thread, even if absurd or surreal.
        Abstract humor and non-sequiturs can still PASS if intentional."""
        
        async def check():
            result = self.admissibility_predictor(
                joke_text=joke_text,
                check_type="coherence",
                instruction_prompt=instructions
            )
            passed = result.passed.lower() == 'true'
            return AdmissibilityCheck(passed=passed, reasoning=result.reasoning)
        
        try:
            return await self._retry_on_error(check)
        except Exception as e:
            return AdmissibilityCheck(passed=True, reasoning=f"Check failed after {self.max_retries} retries: {str(e)}")
    
    async def _check_accessibility_async(self, joke_text: str) -> AdmissibilityCheck:
        """Check language accessibility"""
        instructions = """Liberal evaluation: Only reject if IMPOSSIBLE to understand.
        Accept specialized humor, cultural references, wordplay in any language.
        Technical or niche jokes should still PASS."""
        
        async def check():
            result = self.admissibility_predictor(
                joke_text=joke_text,
                check_type="accessibility",
                instruction_prompt=instructions
            )
            passed = result.passed.lower() == 'true'
            return AdmissibilityCheck(passed=passed, reasoning=result.reasoning)
        
        try:
            return await self._retry_on_error(check)
        except Exception as e:
            return AdmissibilityCheck(passed=True, reasoning=f"Check failed after {self.max_retries} retries: {str(e)}")
    
    async def _classify_categories_async(self, joke_text: str) -> Tuple[List[str], bool]:
        """Assign joke to categories"""
        categories_str = ", ".join(self.categories)
        
        async def classify():
            result = self.category_predictor(
                joke_text=joke_text,
                all_categories=f"Available categories: {categories_str}"
            )
            
            # Parse categories
            is_independent = result.is_independent.lower() == 'true'
            
            if is_independent:
                categories = ["Independent"]
            else:
                # Extract category names from response
                categories = []
                for cat in self.categories:
                    if cat.lower() in result.categories.lower():
                        categories.append(cat)
                
                # If no categories found but not marked independent, mark as independent
                if not categories:
                    categories = ["Independent"]
                    is_independent = True
            
            return categories, is_independent
        
        try:
            return await self._retry_on_error(classify)
        except Exception as e:
            # Default to Independent on error
            return ["Independent"], True
    
    async def _select_factors_per_category_async(self, joke_text: str, categories: List[str], 
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
        
        async def select():
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
            return await self._retry_on_error(select)
        except Exception as e:
            return []
    
    async def _select_from_all_factors_async(self, joke_text: str, all_factors: List[Factor]) -> List[str]:
        """Select from all available factors for Independent category"""
        factors_info = []
        for factor in all_factors:
            factors_info.append(f"{factor.name} ({factor.category}): {factor.description}")
        
        factors_str = "\n".join(factors_info[:20])  # Limit to prevent token overflow
        
        async def select():
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
            return await self._retry_on_error(select)
        except Exception as e:
            return []
    
    async def _score_factors_async(self, joke_text: str, factors: List[str], 
                                  factor_objects: Dict[str, Factor]) -> Dict[str, int]:
        """Score each factor in parallel"""
        tasks = []
        factor_names = []
        
        # Create scoring tasks for each factor occurrence
        for factor_name in factors:
            if factor_name in factor_objects:
                factor = factor_objects[factor_name]
                task = self._score_single_factor_async(joke_text, factor)
                tasks.append(task)
                factor_names.append(factor_name)
        
        if not tasks:
            return {}
        
        # Run all scoring tasks in parallel
        scores = await asyncio.gather(*tasks)
        
        # Build scores dictionary (handling duplicates)
        result = {}
        for i, factor_name in enumerate(factor_names):
            # For duplicates, keep the score (will be evaluated separately)
            if factor_name not in result:
                result[factor_name] = scores[i]
            else:
                # Store duplicate scores with a suffix (won't be visible in final output)
                suffix = 2
                while f"{factor_name}_{suffix}" in result:
                    suffix += 1
                result[f"{factor_name}_{suffix}"] = scores[i]
        
        return result
    
    async def _score_single_factor_async(self, joke_text: str, factor: Factor) -> int:
        """Score joke on a single factor"""
        pos_examples = "\n".join(f"- {ex}" for ex in factor.positive_examples[:3])
        neg_examples = "\n".join(f"- {ex}" for ex in factor.negative_examples[:3])
        
        async def score():
            result = self.factor_scorer(
                joke_text=joke_text,
                factor_name=factor.name,
                factor_description=factor.description,
                positive_examples=pos_examples,
                negative_examples=neg_examples
            )
            
            # Parse score
            try:
                score_val = int(result.score)
                return max(0, min(5, score_val))  # Ensure 0-5 range
            except:
                return 3  # Default middle score on parse error
        
        try:
            return await self._retry_on_error(score)
        except Exception as e:
            return 3  # Default middle score on API error