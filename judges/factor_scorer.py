import asyncio
import dspy
from typing import List, Dict

from utilities.dspy_client import ClaudeClient
from judges.models import FactorData
from judges.dspy_signatures import FactorScoringSignature


class FactorScorer:
    """Handles factor scoring for jokes"""
    
    def __init__(self, client: ClaudeClient, max_retries: int = 5):
        self.client = client
        self.max_retries = max_retries
        self.factor_scorer = dspy.Predict(FactorScoringSignature)
        
        # Define the comprehensive scoring instructions
        self.scoring_instructions = """
You are an expert joke evaluator with high professional standards. Your role is to critically assess jokes and create meaningful differentiation across the full scoring spectrum. Use the complete 0-5 range deliberately to distinguish performance levels.

**SCORING SCALE WITH CLEAR DIFFERENTIATION:**
- **0 = Below Average**: Factor execution is weak, flawed, or poorly implemented. Clear deficiencies evident.
- **1 = Average**: Basic, unremarkable execution of the factor. Meets minimum expectations but nothing more.
- **2 = Good**: Solid, competent execution with no major flaws. Well-executed but not noteworthy.
- **3 = Better**: Above-average execution that shows skill and effectiveness. Notably well-done.
- **4 = Very Good**: High-quality execution that demonstrates clear expertise and creativity. Impressive work.
- **5 = Exceptional**: Outstanding execution that represents peak performance. Reserved for roughly 5-10% of jokes - rare but achievable excellence.

**DISTRIBUTION EXPECTATIONS:**
- Scores 0-1: For genuinely mediocre and average adequate factor execution
- Score 2: For solid, good performance that meets professional standards
- Score 3: For notably effective execution that stands out positively
- Score 4: For high-quality work that demonstrates real skill
- Score 5: For the top 5-10% of factor executions that truly excel

**CRITICAL EVALUATION APPROACH:**
- Maintain professional standards but recognize that these jokes were selected for having the factor present
- Focus on HOW WELL the factor is executed, not whether it exists
- Look for gradations in quality: basic competence vs. skillful execution vs. masterful implementation
- Ask: "Among jokes that have this factor, how well is it executed here?"

**SCORING METHODOLOGY:**
- Start by identifying how the factor manifests in the joke
- Assess the quality of execution against professional comedy standards
- Consider creativity, effectiveness, and technical skill in factor implementation
- Compare against both the positive and negative examples provided
- Differentiate between "does the job" (score 2) and "does it well" (score 3-4)

**EVIDENCE-BASED DIFFERENTIATION:**
- Score 0: Factor present but poorly executed or undermined by flaws
- Score 1: Basic, functional execution without distinction or creativity
- Score 2: Competent execution that works well and serves its purpose
- Score 3: Skillful execution that enhances the joke's effectiveness
- Score 4: Creative, polished execution that demonstrates expertise
- Score 5: Exceptional execution that represents the factor at its finest

**QUALITY ASSESSMENT QUESTIONS:**
- Does this factor execution enhance or detract from the joke's impact?
- How creatively or skillfully is this factor implemented?
- Would other comedy professionals recognize this as quality work?
- What specific elements make this execution stand out (positively or negatively)?

**REASONING STRUCTURE:**
1. Identify specific elements demonstrating the factor
2. Analyze the quality and effectiveness of the execution
3. Note what works well and any limitations
4. Compare to factor examples and professional standards
5. Justify the score based on execution quality within the 0-5 spectrum

Use the full range thoughtfully. Recognize that good execution deserves recognition (scores 2-3), while exceptional work should be rewarded (scores 4-5), and poor execution should be honestly assessed (scores 0-1). Create meaningful distinctions between performance levels.
"""
    
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
                                  factor_objects: Dict[str, FactorData]) -> Dict[str, int]:
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
    
    async def _score_single_factor_async(self, joke_text: str, factor: FactorData) -> int:
        """Score joke on a single factor"""
        
        def score():
            result = self.factor_scorer(
                joke_text=joke_text,
                factor_data=factor,
                instruction=self.scoring_instructions
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

