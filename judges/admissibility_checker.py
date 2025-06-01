import asyncio
import dspy
from typing import List
from datetime import datetime

from utilities.dspy_client import ClaudeClient
from judges.models import AdmissibilityResults, AdmissibilityCheck
from judges.dspy_signatures import AdmissibilitySignature


class AdmissibilityChecker:
    """Handles all admissibility checks for jokes"""
    
    def __init__(self, client: ClaudeClient, max_retries: int = 5):
        self.client = client
        self.max_retries = max_retries
        self.admissibility_predictor = dspy.Predict(AdmissibilitySignature)
    
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
    
    async def check_all_admissibility_async(self, joke_text: str) -> AdmissibilityResults:
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
        instructions = """Focus only on comedic intent. Do not let joke length, complexity, or writing style influence your decision.

Liberal evaluation: Only reject if there is ABSOLUTELY NO comedic intent. When in doubt, PASS. This check should only fail obvious violations. Borderline cases should PASS.

Accept if there's ANY attempt at humor, wordplay, irony, or comedic structure. Even bad jokes or failed attempts at humor should PASS this check."""
        
        examples = """PASS (Clear): "Why don't scientists trust atoms? Because they make up everything!" - Clear pun with setup and punchline.

FAIL (Clear): "The quarterly sales report shows a 15% increase in revenue." - Pure factual statement with no comedic intent.

PASS (Borderline): "My programming skills are so bad, I once spent three hours debugging a semicolon." - Self-deprecating attempt at humor about programming, even if not particularly funny, shows clear comedic intent."""
        
        def check():
            result = self.admissibility_predictor(
                joke_text=joke_text,
                check_type="intent",
                instruction_prompt=instructions,
                examples=examples
            )
            passed = result.passed.lower() == 'true'
            return AdmissibilityCheck(passed=passed, reasoning=result.reasoning)
        
        try:
            # Run synchronous DSPy call in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, lambda: self._retry_on_error(check))
        except Exception as e:
            # If all retries fail, be liberal and pass
            return AdmissibilityCheck(passed=True, reasoning=f"Check failed after {self.max_retries} retries: {str(e)}")
    
    async def _check_completeness_async(self, joke_text: str) -> AdmissibilityCheck:
        """Check if joke is complete"""
        instructions = """Focus only on completeness of the joke structure. Do not let joke length, complexity, or writing style influence your decision.

Liberal evaluation: Only reject if SEVERELY incomplete. When in doubt, PASS. This check should only fail obvious violations. Borderline cases should PASS.

Accept if there's a setup and any form of conclusion, even if weak. One-liners, puns, and short jokes should PASS."""
        
        examples = """PASS (Clear): "I told my wife she was drawing her eyebrows too high. She looked surprised." - Complete setup and punchline.

FAIL (Clear): "So there was this guy and he went to the store and" - Obviously incomplete, cuts off mid-sentence.

PASS (Borderline): "Parallel lines have so much in common. Too bad they'll never meet." - Simple but complete one-liner, has both premise and conclusion."""
        
        def check():
            result = self.admissibility_predictor(
                joke_text=joke_text,
                check_type="completeness",
                instruction_prompt=instructions,
                examples=examples
            )
            passed = result.passed.lower() == 'true'
            return AdmissibilityCheck(passed=passed, reasoning=result.reasoning)
        
        try:
            # Run synchronous DSPy call in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, lambda: self._retry_on_error(check))
        except Exception as e:
            return AdmissibilityCheck(passed=True, reasoning=f"Check failed after {self.max_retries} retries: {str(e)}")
    
    async def _check_appropriateness_async(self, joke_text: str) -> AdmissibilityCheck:
        """Check appropriateness"""
        instructions = """Focus only on extremely harmful content. Do not let joke length, complexity, or writing style influence your decision.

Liberal evaluation: Only reject EXTREMELY offensive content. When in doubt, PASS. This check should only fail obvious violations. Borderline cases should PASS.

Accept edgy humor, dark humor, adult humor, political humor. Only reject if promoting hate, violence, or extreme harm."""
        
        examples = """PASS (Clear): "Why don't cannibals eat clowns? Because they taste funny." - Dark humor but not promoting harm.

FAIL (Clear): "All Pakistani people should be eliminated from society." - Promotes hate and violence against a group.

PASS (Borderline): "My ex is like a software update. Whenever I see the notification, I think 'not now'." - Mildly edgy relationship humor but not harmful."""
        
        def check():
            result = self.admissibility_predictor(
                joke_text=joke_text,
                check_type="appropriateness",
                instruction_prompt=instructions,
                examples=examples
            )
            passed = result.passed.lower() == 'true'
            return AdmissibilityCheck(passed=passed, reasoning=result.reasoning)
        
        try:
            # Run synchronous DSPy call in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, lambda: self._retry_on_error(check))
        except Exception as e:
            return AdmissibilityCheck(passed=True, reasoning=f"Check failed after {self.max_retries} retries: {str(e)}")
    
    async def _check_coherence_async(self, joke_text: str) -> AdmissibilityCheck:
        """Check logical coherence"""
        instructions = """Focus only on internal logical consistency. Do not let joke length, complexity, or writing style influence your decision.

Liberal evaluation: Only reject if COMPLETELY incoherent. When in doubt, PASS. This check should only fail obvious violations. Borderline cases should PASS.

Accept if there's any logical thread, even if absurd or surreal. Abstract humor and non-sequiturs can still PASS if intentional."""
        
        examples = """PASS (Clear): "I haven't slept for ten days, because that would be too long." - Logical wordplay on different meanings of 'for ten days'.

FAIL (Clear): "Purple banana telephone mathematics seventeen." - Random words with no logical connection or comedic structure.

PASS (Borderline): "Time flies like an arrow. Fruit flies like a banana." - Surreal but has intentional logical structure playing with word meanings."""
        
        def check():
            result = self.admissibility_predictor(
                joke_text=joke_text,
                check_type="coherence",
                instruction_prompt=instructions,
                examples=examples
            )
            passed = result.passed.lower() == 'true'
            return AdmissibilityCheck(passed=passed, reasoning=result.reasoning)
        
        try:
            # Run synchronous DSPy call in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, lambda: self._retry_on_error(check))
        except Exception as e:
            return AdmissibilityCheck(passed=True, reasoning=f"Check failed after {self.max_retries} retries: {str(e)}")
    
    async def _check_accessibility_async(self, joke_text: str) -> AdmissibilityCheck:
        """Check language accessibility"""
        instructions = """Focus only on basic understandability. Do not let joke length, complexity, or writing style influence your decision.

Liberal evaluation: Only reject if IMPOSSIBLE to understand. When in doubt, PASS. This check should only fail obvious violations. Borderline cases should PASS.

Accept specialized humor, cultural references, wordplay in any language. Technical or niche jokes should still PASS."""
        
        examples = """PASS (Clear): "Why do programmers prefer dark mode? Because light attracts bugs!" - Uses technical terms but meaning is clear.

FAIL (Clear): "Xlqpz frwm nhtg vjkl zxcv!" - Incomprehensible random letters, impossible to understand.

PASS (Borderline): "TCP jokes aren't funny because you have to keep repeating them until someone gets them." - Technical networking joke that may not be universally understood but is clearly structured."""
        
        def check():
            result = self.admissibility_predictor(
                joke_text=joke_text,
                check_type="accessibility",
                instruction_prompt=instructions,
                examples=examples
            )
            passed = result.passed.lower() == 'true'
            return AdmissibilityCheck(passed=passed, reasoning=result.reasoning)
        
        try:
            # Run synchronous DSPy call in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, lambda: self._retry_on_error(check))
        except Exception as e:
            return AdmissibilityCheck(passed=True, reasoning=f"Check failed after {self.max_retries} retries: {str(e)}")

    