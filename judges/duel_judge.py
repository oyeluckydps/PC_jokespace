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
        self.max_retries = max_retries  # Store max retries for error handling
        self.duel_predictor = dspy.Predict(DuelComparisonSignature)
    
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
                    print(f"\033[93m⚠️  Duel comparison error: {str(e)[:50]}..., retrying in 2s\033[0m")
                    await asyncio.sleep(2)
   
    async def _compare_ab_async(self, joke_a_text: str, joke_b_text: str) -> Dict:
        """Compare A vs B with examples"""
        good_examples = "\n".join(f"Good: {ex}" for ex in self.examples.good_jokes)
        bad_examples = "\n".join(f"Bad: {ex}" for ex in self.examples.bad_jokes)
        
        async def compare():
            result = self.duel_predictor(
                joke_a=joke_a_text,
                joke_b=joke_b_text,
                good_examples=good_examples,
                bad_examples=bad_examples
            )
            
            winner = result.winner.lower().strip()
            try:
                confidence = float(result.confidence_factor)
                confidence = max(1.0, confidence)  # Ensure >= 1.0
            except:
                confidence = 1.0
            
            return {
                'winner': 'a' if 'joke_a' in winner else 'b',
                'confidence': confidence,
                'reasoning': result.reasoning
            }
        
        try:
            return await self._retry_on_error(compare)
        except Exception as e:
            # Default to A with low confidence on error after all retries
            return {
               'winner': 'a',
               'confidence': 1.0,
               'reasoning': f"Comparison failed after {self.max_retries} retries: {str(e)}"
           }
  
    async def _compare_ba_async(self, joke_b_text: str, joke_a_text: str) -> Dict:
        """Compare B vs A with examples"""
        good_examples = "\n".join(f"Good: {ex}" for ex in self.examples.good_jokes)
        bad_examples = "\n".join(f"Bad: {ex}" for ex in self.examples.bad_jokes)
       
        async def compare():
            result = self.duel_predictor(
                joke_a=joke_b_text,
                joke_b=joke_a_text,
                good_examples=good_examples,
                bad_examples=bad_examples
            )
           
            winner = result.winner.lower().strip()
            # Reverse the result since we swapped inputs
            if 'joke_a' in winner:
                actual_winner = 'b'
            else:
                actual_winner = 'a'
           
            try:
                confidence = float(result.confidence_factor)
                confidence = max(1.0, confidence)
            except:
                confidence = 1.0
           
            return {
                'winner': actual_winner,
                'confidence': confidence,
                'reasoning': result.reasoning
            }
       
        try:
            return await self._retry_on_error(compare)
        except Exception as e:
            return {
                'winner': 'a',
                'confidence': 1.0,
                'reasoning': f"Comparison failed after {self.max_retries} retries: {str(e)}"
            }
  
    def _resolve_comparison(self, ab_result: Dict, ba_result: Dict, 
                           joke_a: RatingResult, joke_b: RatingResult) -> Dict:
        """Resolve conflicts between two comparisons"""
        position_consistent = ab_result['winner'] == ba_result['winner']
        decision_type = None
        
        # Calculate winner IDs for each direction
        ab_winner_id = joke_a.joke_id if ab_result['winner'] == 'a' else joke_b.joke_id
        ba_winner_id = joke_a.joke_id if ba_result['winner'] == 'a' else joke_b.joke_id

        if position_consistent:
            # Both comparisons agree
            winner = ab_result['winner']
            confidence = (ab_result['confidence'] + ba_result['confidence']) / 2
            reasoning = f"Consistent decision. AB: {ab_result['reasoning']} BA: {ba_result['reasoning']}"
            decision_type = "consistent"
        else:
            # Comparisons disagree - check for tie
            if ab_result['confidence'] == ba_result['confidence']:
                # Exact tie - use original ratings to break tie
                if joke_a.overall_rating > joke_b.overall_rating:
                    winner = 'a'
                    confidence = ab_result['confidence']
                    reasoning = f"Tie detected (confidence {confidence}). Using original rating to break tie: A({joke_a.overall_rating:.2f}) > B({joke_b.overall_rating:.2f})"
                    decision_type = "by_rating"
                elif joke_b.overall_rating > joke_a.overall_rating:
                    winner = 'b'
                    confidence = ba_result['confidence']
                    reasoning = f"Tie detected (confidence {confidence}). Using original rating to break tie: B({joke_b.overall_rating:.2f}) > A({joke_a.overall_rating:.2f})"
                    decision_type = "by_rating"
                else:
                    # Even ratings - use seed
                    winner = 'a' if joke_a.original_rank < joke_b.original_rank else 'b'
                    confidence = ab_result['confidence']
                    reasoning = f"Tie with equal ratings. Using seed to break tie."
                    decision_type = "by_rating"
            else:
                # Use higher confidence result
                if ab_result['confidence'] > ba_result['confidence']:
                    winner = ab_result['winner']
                    confidence = ab_result['confidence']
                    reasoning = f"Position inconsistent. Using AB result (higher confidence). {ab_result['reasoning']}"
                    decision_type = "by_confidence"
                else:
                    winner = ba_result['winner']
                    confidence = ba_result['confidence']
                    reasoning = f"Position inconsistent. Using BA result (higher confidence). {ba_result['reasoning']}"
                    decision_type = "by_confidence"
        
        return {
            'winner': winner,
            'winner_id': joke_a.joke_id if winner == 'a' else joke_b.joke_id,
            'confidence': confidence,
            'position_consistent': position_consistent,
            'reasoning': reasoning,
            'ab_confidence': ab_result['confidence'],
            'ba_confidence': ba_result['confidence'],
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
            ab_winner_id=comparison.get('ab_winner_id'),  # ADD THIS
            ba_winner_id=comparison.get('ba_winner_id'),  # ADD THIS
            decision_type=comparison.get('decision_type')
        )
    
    