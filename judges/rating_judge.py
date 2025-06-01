import asyncio
import time
from typing import List, Dict
from datetime import datetime

from utilities.xml_parser import Factor, ExampleData, JokeData
from utilities.dspy_client import ClaudeClient
from judges.models import RatingResult, CategoryInfo
from judges.admissibility_checker import AdmissibilityChecker
from judges.category_classifier import CategoryClassifier
from judges.factor_selector import FactorSelector
from judges.factor_scorer import FactorScorer

# File-wide variable for timing logs
LOG_TIME = True


class RatingJudge:
    """Main orchestrator class that coordinates all judgment components"""
    
    def __init__(self, client: ClaudeClient, categories: List[str], 
                 factors: Dict[str, List[Factor]], examples: ExampleData,
                 category_info_list: List[CategoryInfo],
                 max_retries: int = 5):
        """Initialize rating judge with parsed XML data"""
        self.client = client
        self.categories = categories
        self.factors = factors
        self.examples = examples
        self.category_info_list = category_info_list
        self.max_retries = max_retries
        
        # Initialize specialized components
        self.admissibility_checker = AdmissibilityChecker(client, max_retries)
        self.category_classifier = CategoryClassifier(client, category_info_list, max_retries)
        self.factor_selector = FactorSelector(client, factors, max_retries)
        self.factor_scorer = FactorScorer(client, max_retries)
    
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
        
        # Step 1: Check admissibility
        admissibility_results = await self.admissibility_checker.check_all_admissibility_async(joke.text)
        
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
        categories, is_independent = await self.category_classifier.classify_categories_async(joke.text)
        result.assigned_categories = categories
        
        if LOG_TIME:
            elapsed = (time.time() - start_time) * 1000
            print(f"Joke {joke.id} | Category Assignment: {elapsed:.3f}ms")
        
        # Step 3: Select factors per category
        factors_data = await self.factor_selector.select_factors_per_category_async(
            joke.text, categories, is_independent
        )
        result.relevant_factors = factors_data['all_factors']
        result.dropped_categories = factors_data['dropped_categories']
        factor_objects = factors_data['factor_objects']  # Get factor objects for scoring
        
        if LOG_TIME:
            elapsed = (time.time() - start_time) * 1000
            print(f"Joke {joke.id} | Factor Selection: {elapsed:.3f}ms")
        
        # Step 4: Score all factors
        if result.relevant_factors:
            factor_scores = await self.factor_scorer.score_factors_async(
                joke.text, 
                result.relevant_factors,
                factor_objects  # Pass factor objects directly
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
            # Give some benefit for involving more factors and divide by 12 to normalize and bring the value below 5.
        
        if LOG_TIME:
            total_elapsed = (time.time() - start_time) * 1000
            print(f"Joke {joke.id} | Complete: {total_elapsed:.3f}ms")
        
        return result