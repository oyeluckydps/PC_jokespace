import asyncio
from typing import List, Dict, Optional, Tuple
import dspy
import time
from datetime import datetime

from utilities.xml_parser import Category, Factor, ExampleData, JokeData
from utilities.dspy_client import ClaudeClient
from judges.models import (
    RatingResult, AdmissibilityResults
)
from judges.dspy_signatures import (
    CombinedAdmissibilitySignature, CategoryAssignmentSignature,
    FactorSelectionSignature, FactorScoringSignature
)

# File-wide variable for timing logs
LOG_TIME = True

class RatingJudge:
    def __init__(self, client: ClaudeClient, categories: List[str], 
                 factors: Dict[str, List[Factor]], examples: ExampleData,
                 max_retries: int = 5):
        """Initialize rating judge with parsed XML data"""
        self.client = client
        self.categories = categories
        self.factors = factors
        self.examples = examples
        self.max_retries = max_retries
        
        # Initialize DSPy predictors
        self.combined_admissibility_predictor = dspy.Predict(CombinedAdmissibilitySignature)
        self.category_predictor = dspy.Predict(CategoryAssignmentSignature)
        self.factor_selector = dspy.Predict(FactorSelectionSignature)
        self.factor_scorer = dspy.Predict(FactorScoringSignature)
        
        # Pre-build static prompt components
        self._evaluation_criteria = self._build_evaluation_criteria()
        self._bias_mitigation_guidelines = self._build_bias_mitigation_guidelines()
        self._admissibility_examples = self._build_admissibility_examples()
    
    def evaluate_joke(self, joke: JokeData) -> RatingResult:
        """Synchronous wrapper for async evaluation"""
        return asyncio.run(self.evaluate_joke_async(joke))
    
    async def evaluate_joke_async(self, joke: JokeData) -> RatingResult:
        """Full evaluation pipeline"""
        # Initialize timing
        start_time = time.time()
        start_timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]  # HH:MM:SS.mmm
        
        if LOG_TIME:
            print(f"Joke {joke.id} | Start: {start_timestamp}")
        
        # Step 1: Combined admissibility check
        admissibility_results = await self._check_combined_admissibility_async(joke.text)
        
        if LOG_TIME:
            elapsed = (time.time() - start_time) * 1000  # Convert to milliseconds
            print(f"Joke {joke.id} | Admissibility Check: {elapsed:.3f}ms")
        
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
            if LOG_TIME:
                total_elapsed = (time.time() - start_time) * 1000
                print(f"Joke {joke.id} | Not Admissible - Total: {total_elapsed:.3f}ms")
            return result
        
        # Step 2: Assign categories
        categories, is_independent = await self._classify_categories_async(joke.text)
        result.assigned_categories = categories
        
        if LOG_TIME:
            elapsed = (time.time() - start_time) * 1000
            print(f"Joke {joke.id} | Category Assignment: {elapsed:.3f}ms")
        
        # Step 3: Select factors per category
        factors_data = await self._select_factors_per_category_async(joke.text, categories, is_independent)
        result.relevant_factors = factors_data['all_factors']
        result.dropped_categories = factors_data['dropped_categories']
        factor_objects = factors_data['factor_objects']
        
        if LOG_TIME:
            elapsed = (time.time() - start_time) * 1000
            print(f"Joke {joke.id} | Factor Selection: {elapsed:.3f}ms")
        
        # Step 4: Score all factors
        if result.relevant_factors:
            factor_scores = await self._score_factors_async(
                joke.text, 
                result.relevant_factors,
                factor_objects
            )
            result.factor_scores = factor_scores
            
            if LOG_TIME:
                elapsed = (time.time() - start_time) * 1000
                print(f"Joke {joke.id} | Factor Scoring: {elapsed:.3f}ms")
            
            # Step 5: Calculate final ratings
            scores = list(factor_scores.values())
            result.max_score = max(scores) if scores else 0
            result.mean_score = sum(scores) / len(scores) if scores else 0.0
            result.overall_rating = (result.max_score*10 + result.mean_score +  len(scores)/5)/12   
        
        if LOG_TIME:
            total_elapsed = (time.time() - start_time) * 1000
            print(f"Joke {joke.id} | Complete: {total_elapsed:.3f}ms")
        
        return result
    
    def _build_evaluation_criteria(self) -> str:
        """Build the evaluation criteria string"""
        return """
INTENT CHECK - Liberal Evaluation:
Only reject if there is ABSOLUTELY NO comedic intent.
Accept if there's ANY attempt at humor, wordplay, irony, or comedic structure.
Even bad jokes or failed attempts at humor should PASS this check.

COMPLETENESS CHECK - Liberal Evaluation:
Only reject if SEVERELY incomplete.
Accept if there's a setup and any form of conclusion, even if weak.
One-liners, puns, and short jokes should PASS.

APPROPRIATENESS CHECK - Liberal Evaluation:
Only reject EXTREMELY offensive content.
Accept edgy humor, dark humor, adult humor, political humor.
Only reject if promoting hate, violence, or extreme harm.

COHERENCE CHECK - Liberal Evaluation:
Only reject if COMPLETELY incoherent.
Accept if there's any logical thread, even if absurd or surreal.
Abstract humor and non-sequiturs can still PASS if intentional.

ACCESSIBILITY CHECK - Liberal Evaluation:
Only reject if IMPOSSIBLE to understand.
Accept specialized humor, cultural references, wordplay in any language.
Technical or niche jokes should still PASS.
"""
    
    def _build_bias_mitigation_guidelines(self) -> str:
        """Build bias mitigation guidelines"""
        return """
BIAS MITIGATION MEASURES:

LENGTH BIAS AVOIDANCE:
- Do not favor longer or shorter jokes
- Evaluate based on content quality, not word count
- Short one-liners can be as valid as longer setup-punchline jokes

POSITION BIAS AVOIDANCE:
- Evaluate each criterion independently
- Do not let earlier criteria evaluations influence later ones
- Consider all criteria simultaneously rather than sequentially

STYLE BIAS AVOIDANCE:
- Do not prefer certain writing styles or formats
- Accept various joke structures (puns, observational, absurdist, etc.)
- Avoid favoring complex vocabulary over simple language

CULTURAL BIAS AVOIDANCE:
- Accept humor from different cultural contexts
- Do not require universal cultural knowledge
- Specialized or niche references should still pass accessibility if comprehensible

CONCRETENESS BIAS AVOIDANCE:
- Do not favor jokes with specific details over abstract humor
- Avoid preferring authoritative-sounding content
- Simple concepts can be as valid as complex ones

OVERCONFIDENCE MITIGATION:
- Apply liberal evaluation standards consistently
- When in doubt, err on the side of passing the check
- Focus on the minimum threshold for each criterion
"""
    
    def _build_admissibility_examples(self) -> str:
        """Build examples for admissibility checks"""
        return """
INTENT CHECK EXAMPLES:

PASS Example: "I told my wife she was drawing her eyebrows too high. She looked surprised."
- Clear comedic intent with setup and punchline structure

FAIL Example: "The weather is nice today and I like coffee."
- No comedic intent, just factual statements

COMPLETENESS CHECK EXAMPLES:

PASS Example: "Why don't scientists trust atoms? Because they make up everything!"
- Complete joke with setup and punchline

FAIL Example: "There once was a man from..."
- Severely incomplete, missing the entire joke content

APPROPRIATENESS CHECK EXAMPLES:

PASS Example: "My therapist says I have a preoccupation with vengeance. We'll see about that."
- Dark humor but not promoting harm

FAIL Example: [Content promoting violence or extreme hate]
- Would be rejected for promoting actual harm

COHERENCE CHECK EXAMPLES:

PASS Example: "I haven't slept for ten days, because that would be too long."
- Coherent wordplay with logical thread

FAIL Example: "Purple elephant mathematics seven window happy."
- Completely incoherent with no logical connection

ACCESSIBILITY CHECK EXAMPLES:

PASS Example: "There are only 10 types of people: those who understand binary and those who don't."
- Technical reference but comprehensible

FAIL Example: [Content in completely unknown language/script with no context]
- Would be impossible to understand for evaluation
"""
    
    def _retry_on_error(self, func, *args, **kwargs):
        """Generic retry wrapper for sync functions with retries"""
        for attempt in range(self.max_retries + 1):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                if attempt == self.max_retries:
                    raise e
                else:
                    print(f"\033[93m⚠️  Error: {str(e)[:50]}..., retrying in 2s\033[0m")
                    import time
                    time.sleep(2)
    
    async def _check_combined_admissibility_async(self, joke_text: str) -> AdmissibilityResults:
        """Run combined admissibility check with bias mitigation"""
        async def check():
            result = self.combined_admissibility_predictor(
                evaluation_criteria=self._evaluation_criteria,
                bias_mitigation_guidelines=self._bias_mitigation_guidelines,
                examples=self._admissibility_examples,
                joke_text=joke_text
            )
            
            # DSPy returns boolean values directly
            intent_passed = bool(result.intent_passed)
            completeness_passed = bool(result.completeness_passed)
            appropriateness_passed = bool(result.appropriateness_passed)
            coherence_passed = bool(result.coherence_passed)
            accessibility_passed = bool(result.accessibility_passed)
            
            # Calculate overall admissibility programmatically
            is_admissible = all([
                intent_passed, completeness_passed, appropriateness_passed,
                coherence_passed, accessibility_passed
            ])
            
            return AdmissibilityResults(
                intent_check=intent_passed,
                completeness_check=completeness_passed,
                appropriateness_check=appropriateness_passed,
                coherence_check=coherence_passed,
                accessibility_check=accessibility_passed,
                is_admissible=is_admissible
            )
        
        try:
            return await self._retry_on_error_async(check)
        except Exception as e:
            # If all retries fail, be liberal and pass all checks
            return AdmissibilityResults(
                intent_check=True,
                completeness_check=True,
                appropriateness_check=True,
                coherence_check=True,
                accessibility_check=True,
                is_admissible=True
            )
    
    async def _classify_categories_async(self, joke_text: str) -> Tuple[List[str], bool]:
        """Assign joke to categories"""
        categories_str = ", ".join(self.categories)
        
        def classify():
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
            # Run synchronous DSPy call in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, lambda: self._retry_on_error(classify))
        except Exception as e:
            # Default to Independent on error
            return ["Independent"], True
    
    async def _retry_on_error_async(self, func, *args, **kwargs):
        """Generic async retry wrapper"""
        for attempt in range(self.max_retries + 1):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                if attempt == self.max_retries:
                    raise e
                else:
                    print(f"\033[93m⚠️  Error: {str(e)[:50]}..., retrying in 2s\033[0m")
                    await asyncio.sleep(2)
    
    async def _select_factors_per_category_async(self, joke_text: str, categories: List[str], 
                                               is_independent: bool) -> Dict:
        """Select relevant factors for each category"""
        all_factors = []
        dropped_categories = []
        factor_objects = {}
        
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
        
        return {
            'all_factors': all_factors,
            'dropped_categories': dropped_categories,
            'factor_objects': factor_objects
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
        
        def score():
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
            # Run synchronous DSPy call in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, lambda: self._retry_on_error(score))
        except Exception as e:
            return 3  # Default middle score on API error