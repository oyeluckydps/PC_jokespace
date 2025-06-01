import asyncio
import dspy
from typing import List, Dict

from utilities.dspy_client import ClaudeClient
from utilities.xml_parser import Factor
from judges.dspy_signatures import FactorScoringSignature


class FactorScorer:
    """Handles factor scoring for jokes"""
    
    def __init__(self, client: ClaudeClient, max_retries: int = 5):
        self.client = client
        self.max_retries = max_retries
        self.factor_scorer = dspy.Predict(FactorScoringSignature)
    
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
    
    async def score_factors_async(self, joke_text: str, factors: List[str], 
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

    