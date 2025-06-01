import asyncio
from typing import Dict, Tuple
import dspy

from utilities.dspy_client import ClaudeClient
from utilities.xml_parser import ExampleData
from judges.models import RatingResult, DuelResult
from judges.dspy_signatures import DuelComparisonSignature

class DuelJudge:
    def __init__(self, client: ClaudeClient, examples: ExampleData, max_retries: int = 5):
        """Initialize with good/bad joke examples"""
        self.client = client
        self.examples = examples
        self.max_retries = max_retries
        self.duel_predictor = dspy.Predict(DuelComparisonSignature)
        
        # Enhanced bias-free humor evaluation instruction
        self.evaluation_instruction = """
HUMOR EVALUATION TASK - BIAS-FREE COMPARISON

You are evaluating which of two jokes is funnier. Focus solely on humor quality and comedic effectiveness.

**CORE EVALUATION CRITERIA:**
- Which joke is more likely to make people laugh?
- Consider comedic timing, surprise, wordplay, wit, and relatability
- Evaluate the strength of the comedic mechanism (setup-punchline, wordplay, absurdity, observational humor, etc.)
- Assess novelty and uniqueness - original, creative, or unexpected approaches to humor
- Consider freshness and inventiveness in the comedic concept or execution

**EVALUATION GUIDELINES:**
- Base judgment purely on comedic effectiveness and humor content
- Consider which joke would get a better response from a general audience
- Look for originality, cleverness, surprise, novelty, uniqueness, and comedic timing
- Evaluate how well the joke executes its intended comedic mechanism
- Focus on the humor's impact, not the joke's construction details
- Prioritize fresh, creative, and inventive humor over predictable or overused patterns
- Value unique perspectives, unexpected twists, and original comedic insights

**CRITICAL BIAS MITIGATION - IGNORE THESE FACTORS:**
- **Length bias**: Shorter or longer does NOT mean funnier - judge purely on humor content
- **Style bias**: Ignore formatting, capitalization, punctuation, or visual presentation
- **Concreteness bias**: Don't favor jokes with more specific details, names, or references
- **Cultural bias**: Consider broad appeal rather than niche cultural references
- **Topic bias**: Don't favor certain humor styles (puns vs observational vs wordplay) - judge effectiveness within each style
- **Complexity bias**: Don't assume complex setups are funnier than simple ones - judge execution quality
- **Position bias**: The order of presentation should NOT influence your decision

**CONFIDENCE LEVELS (1.0 to 5.0 scale):**
- **1.0-2.0 (Tie/Equal)**: Both jokes are essentially equal in funniness, very close call
- **2.0-3.0 (Slightly funnier)**: One joke is somewhat better but the difference is small
- **3.0-4.0 (Moderately funnier)**: Clear preference with noticeable difference in humor quality
- **4.0-5.0 (Significantly funnier)**: Strong preference with substantial difference in comedic effectiveness

You can use any decimal value between 1.0 and 5.0 (e.g., 2.3, 3.7, 4.1) to precisely reflect your confidence level. The ranges above are guidelines to help you calibrate your assessment.

**IMPORTANT:** Make your decision based on pure comedic merit, novelty, and uniqueness. If truly equal, use confidence level around 1.0-1.5.
"""
    
    async def compare_jokes_for_tournament(self, joke_a: RatingResult, joke_b: RatingResult,
                                match_id: str, round_number: int, round_name: str,
                                lives_tracker: Dict[int, int]) -> DuelResult:
        """Full tournament comparison with lives tracking"""
        # Run async comparison - NO asyncio.run() needed!
        comparison_result = await self.compare_jokes_async(joke_a, joke_b)
        
        # Build match result
        return self._build_duel_result(
            joke_a, joke_b, comparison_result,
            match_id, round_number, round_name, lives_tracker
        )
    
    async def compare_jokes_async(self, joke_a: RatingResult, joke_b: RatingResult) -> Dict:
        """Run both comparisons in parallel"""
        # Run both directions
        ab_task = self._compare_ab_async(joke_a.joke_text, joke_b.joke_text)
        ba_task = self._compare_ba_async(joke_b.joke_text, joke_a.joke_text)
        
        ab_result, ba_result = await asyncio.gather(ab_task, ba_task)
        
        # Resolve the comparison with joke metadata for tiebreaking
        return self._resolve_comparison(ab_result, ba_result, joke_a, joke_b)
    
    def _retry_on_error(self, func, *args, **kwargs):
        """Generic retry wrapper for sync functions with retries"""
        for attempt in range(self.max_retries + 1):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                if attempt == self.max_retries:
                    raise e
                else:
                    print(f"\033[93m⚠️  Duel comparison error: {str(e)[:50]}..., retrying in 2s\033[0m")
                    import time
                    time.sleep(2)
   
    async def _compare_ab_async(self, joke_a_text: str, joke_b_text: str) -> Dict:
        """Compare A vs B with enhanced bias-free evaluation"""
        good_examples = "\n".join(f"Good: {ex}" for ex in self.examples.good_jokes)
        bad_examples = "\n".join(f"Bad: {ex}" for ex in self.examples.bad_jokes)
        
        def compare():
            result = self.duel_predictor(
                joke_a=joke_a_text,
                joke_b=joke_b_text,
                good_examples=good_examples,
                bad_examples=bad_examples,
                instruction=self.evaluation_instruction
            )
            
            winner = result.winner.lower().strip()
            try:
                confidence_level = float(result.confidence_level)
                confidence_level = max(1.0, min(5.0, confidence_level))  # Ensure 1.0-5.0 range
            except:
                confidence_level = 1.0  # Default to tie
            
            return {
                'winner': 'a' if 'joke_a' in winner else 'b',
                'confidence_level': confidence_level,
                'confidence': confidence_level  # Keep for compatibility
            }
        
        try:
            # Run synchronous DSPy call in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, lambda: self._retry_on_error(compare))
        except Exception as e:
            # Default to A with tie confidence on error after all retries
            return {
               'winner': 'a',
               'confidence_level': 1.0,
               'confidence': 1.0
           }
  
    async def _compare_ba_async(self, joke_b_text: str, joke_a_text: str) -> Dict:
        """Compare B vs A with enhanced bias-free evaluation"""
        good_examples = "\n".join(f"Good: {ex}" for ex in self.examples.good_jokes)
        bad_examples = "\n".join(f"Bad: {ex}" for ex in self.examples.bad_jokes)
       
        def compare():
            result = self.duel_predictor(
                joke_a=joke_b_text,
                joke_b=joke_a_text,
                good_examples=good_examples,
                bad_examples=bad_examples,
                instruction=self.evaluation_instruction
            )
           
            winner = result.winner.lower().strip()
            # Reverse the result since we swapped inputs
            if 'joke_a' in winner:
                actual_winner = 'b'
            else:
                actual_winner = 'a'
           
            try:
                confidence_level = float(result.confidence_level)
                confidence_level = max(1.0, min(5.0, confidence_level))
            except:
                confidence_level = 1.0
           
            return {
                'winner': actual_winner,
                'confidence_level': confidence_level,
                'confidence': confidence_level
            }
       
        try:
            # Run synchronous DSPy call in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, lambda: self._retry_on_error(compare))
        except Exception as e:
            return {
                'winner': 'a',
                'confidence_level': 1.0,
                'confidence': 1.0
            }
  
    def _resolve_comparison(self, ab_result: Dict, ba_result: Dict, 
                           joke_a: RatingResult, joke_b: RatingResult) -> Dict:
        """Resolve conflicts between two comparisons using enhanced logic"""
        position_consistent = ab_result['winner'] == ba_result['winner']
        decision_type = None
        
        # Calculate winner IDs for each direction
        ab_winner_id = joke_a.joke_id if ab_result['winner'] == 'a' else joke_b.joke_id
        ba_winner_id = joke_a.joke_id if ba_result['winner'] == 'a' else joke_b.joke_id

        if position_consistent:
            # Both comparisons agree
            winner = ab_result['winner']
            confidence_level = (ab_result['confidence_level'] + ba_result['confidence_level']) / 2
            confidence = confidence_level
            reasoning = f"Consistent decision across both position tests (levels: {ab_result['confidence_level']:.2f}, {ba_result['confidence_level']:.2f})"
            decision_type = "consistent"
        else:
            # Comparisons disagree - enhanced resolution logic
            confidence_diff = abs(ab_result['confidence_level'] - ba_result['confidence_level'])
            
            if confidence_diff < 0.3:  # Very close confidence levels
                # Close confidence levels but different winners - likely close call
                if ab_result['confidence_level'] <= 2.0 and ba_result['confidence_level'] <= 2.0:
                    # Both indicated ties/slight preferences, use original ratings to break tie
                    if joke_a.overall_rating > joke_b.overall_rating:
                        winner = 'a'
                        confidence_level = max(ab_result['confidence_level'], ba_result['confidence_level']) + 0.2
                        reasoning = f"Both comparisons indicated close calls (levels: {ab_result['confidence_level']:.2f}, {ba_result['confidence_level']:.2f}). Using original rating to break tie: A({joke_a.overall_rating:.2f}) > B({joke_b.overall_rating:.2f})"
                        decision_type = "by_rating"
                    elif joke_b.overall_rating > joke_a.overall_rating:
                        winner = 'b'
                        confidence_level = max(ab_result['confidence_level'], ba_result['confidence_level']) + 0.2
                        reasoning = f"Both comparisons indicated close calls (levels: {ab_result['confidence_level']:.2f}, {ba_result['confidence_level']:.2f}). Using original rating to break tie: B({joke_b.overall_rating:.2f}) > A({joke_a.overall_rating:.2f})"
                        decision_type = "by_rating"
                    else:
                        # Even ratings - use seed
                        winner = 'a' if joke_a.original_rank < joke_b.original_rank else 'b'
                        confidence_level = (ab_result['confidence_level'] + ba_result['confidence_level']) / 2
                        reasoning = f"Both comparisons indicated close calls with equal ratings. Using seed to break tie."
                        decision_type = "by_seed"
                else:
                    # Close confidence but higher levels - use ratings
                    if joke_a.overall_rating > joke_b.overall_rating:
                        winner = 'a'
                        confidence_level = ab_result['confidence_level'] if ab_result['winner'] == 'a' else ba_result['confidence_level']
                        reasoning = f"Position inconsistent with close confidence (diff: {confidence_diff:.2f}). Using rating to break tie: A({joke_a.overall_rating:.2f}) > B({joke_b.overall_rating:.2f})"
                        decision_type = "by_rating"
                    elif joke_b.overall_rating > joke_a.overall_rating:
                        winner = 'b'
                        confidence_level = ab_result['confidence_level'] if ab_result['winner'] == 'b' else ba_result['confidence_level']
                        reasoning = f"Position inconsistent with close confidence (diff: {confidence_diff:.2f}). Using rating to break tie: B({joke_b.overall_rating:.2f}) > A({joke_a.overall_rating:.2f})"
                        decision_type = "by_rating"
                    else:
                        winner = 'a' if joke_a.original_rank < joke_b.original_rank else 'b'
                        confidence_level = max(ab_result['confidence_level'], ba_result['confidence_level'])
                        reasoning = f"Position inconsistent with close confidence and equal ratings. Using seed to break tie."
                        decision_type = "by_seed"
            else:
                # Significant difference in confidence levels - use higher confidence result
                if ab_result['confidence_level'] > ba_result['confidence_level']:
                    winner = ab_result['winner']
                    confidence_level = ab_result['confidence_level']
                    reasoning = f"Position inconsistent. Using AB result (higher confidence level {ab_result['confidence_level']:.2f} vs {ba_result['confidence_level']:.2f})"
                    decision_type = "by_confidence"
                else:
                    winner = ba_result['winner']
                    confidence_level = ba_result['confidence_level']
                    reasoning = f"Position inconsistent. Using BA result (higher confidence level {ba_result['confidence_level']:.2f} vs {ab_result['confidence_level']:.2f})"
                    decision_type = "by_confidence"
            
            confidence = confidence_level
        
        return {
            'winner': winner,
            'winner_id': joke_a.joke_id if winner == 'a' else joke_b.joke_id,
            'confidence': confidence,
            'confidence_level': confidence_level,
            'position_consistent': position_consistent,
            'reasoning': reasoning,
            'ab_confidence': ab_result['confidence'],
            'ba_confidence': ba_result['confidence'],
            'ab_confidence_level': ab_result['confidence_level'],
            'ba_confidence_level': ba_result['confidence_level'],
            'ab_winner_id': ab_winner_id,
            'ba_winner_id': ba_winner_id,
            'decision_type': decision_type
        }
  
    def _build_duel_result(self, joke_a: RatingResult, joke_b: RatingResult,
                        comparison: Dict, match_id: str, round_number: int,
                        round_name: str, lives_tracker: Dict[int, int]) -> DuelResult:
        """Build complete duel result"""
        winner_id = comparison['winner_id']
        loser_id = joke_b.joke_id if winner_id == joke_a.joke_id else joke_a.joke_id
        loser_advanced = lives_tracker.get(loser_id, 0) > 0
        
        return DuelResult(
            match_id=match_id,
            round_number=round_number,
            round_name=round_name,
            joke_a_id=joke_a.joke_id,
            joke_a_seed=joke_a.original_rank,
            joke_a_lives_before=lives_tracker.get(joke_a.joke_id, 0),
            joke_b_id=joke_b.joke_id,
            joke_b_seed=joke_b.original_rank,
            joke_b_lives_before=lives_tracker.get(joke_b.joke_id, 0),
            winner_id=winner_id,
            loser_advanced_by_life=loser_advanced,
            confidence_factor=comparison['confidence'],
            position_consistent=comparison['position_consistent'],
            reasoning=comparison['reasoning'],
            ab_confidence=comparison.get('ab_confidence'),
            ba_confidence=comparison.get('ba_confidence'),
            ab_winner_id=comparison.get('ab_winner_id'),
            ba_winner_id=comparison.get('ba_winner_id'),
            decision_type=comparison.get('decision_type')
        )