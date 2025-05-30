import asyncio
from typing import List, Optional
from datetime import datetime
import sys

from utilities.xml_parser import JokeData
from judges.models import RatingResult
from judges.rating_judge import RatingJudge

class BatchProcessor:
    def __init__(self, rating_judge: RatingJudge, batch_size: int = 20):
        """Initialize batch processor with rating judge and batch size"""
        self.rating_judge = rating_judge
        self.batch_size = batch_size
        self.processed_count = 0
        self.failed_jokes = []
        self.start_time = None
    
    async def process_all_jokes(self, jokes: List[JokeData]) -> List[RatingResult]:
        """Process all jokes in batches with progress tracking"""
        if not jokes:
            return []
        
        self.start_time = datetime.now()
        total_jokes = len(jokes)
        all_results = []
        
        print(f"\nProcessing {total_jokes} jokes in batches of {self.batch_size}")
        print(f"Estimated batches: {(total_jokes + self.batch_size - 1) // self.batch_size}")
        
        # Process in batches
        for batch_start in range(0, total_jokes, self.batch_size):
            batch_end = min(batch_start + self.batch_size, total_jokes)
            batch = jokes[batch_start:batch_end]
            batch_num = (batch_start // self.batch_size) + 1
            
            print(f"\n{'='*60}")
            print(f"Processing Batch {batch_num} (Jokes {batch_start + 1}-{batch_end})")
            print(f"{'='*60}")
            
            # Process batch
            batch_results = await self._process_batch(batch, batch_start)
            all_results.extend(batch_results)
            
            # Update progress
            self.processed_count = len(all_results) + len(self.failed_jokes)
            self._display_progress(total_jokes)
            
            # Small delay between batches to avoid rate limiting
            if batch_end < total_jokes:
                await asyncio.sleep(1)
        
        # Final summary
        self._display_final_summary(all_results, total_jokes)
        
        return all_results
    
    async def _process_batch(self, batch: List[JokeData], batch_start_idx: int) -> List[RatingResult]:
        """Process a single batch of jokes in parallel"""
        tasks = []
        joke_indices = []
        
        # Create evaluation tasks
        for i, joke in enumerate(batch):
            task = self._evaluate_joke_with_retry(joke, batch_start_idx + i)
            tasks.append(task)
            joke_indices.append(batch_start_idx + i)
        
        # Run all evaluations in parallel
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        valid_results = []
        for i, result in enumerate(results):
            joke_idx = joke_indices[i]
            joke = batch[i]
            
            if isinstance(result, Exception):
                print(f"\n❌ Failed to process joke {joke.id}: {str(result)}")
                self.failed_jokes.append({
                    'joke': joke,
                    'index': joke_idx,
                    'error': str(result)
                })
            elif result is None:
                print(f"\n❌ Failed to process joke {joke.id}: Maximum retries exceeded")
                self.failed_jokes.append({
                    'joke': joke,
                    'index': joke_idx,
                    'error': "Maximum retries exceeded"
                })
            else:
                # Add original rank for tournament seeding
                result.original_rank = joke_idx + 1
                valid_results.append(result)
                
                # Display brief result
                self._display_joke_result(result, joke_idx)
        
        return valid_results
    
    async def _evaluate_joke_with_retry(self, joke: JokeData, joke_index: int, 
                                      max_retries: int = 10) -> Optional[RatingResult]:
        """Evaluate a single joke with retry logic"""
        for attempt in range(max_retries):
            try:
                # Show processing indicator
                if attempt == 0:
                    print(f"\n📝 Processing joke {joke_index + 1} (ID: {joke.id})...", end='', flush=True)
                else:
                    print(f"\n🔄 Retry {attempt} for joke {joke_index + 1}...", end='', flush=True)
                
                # Evaluate joke
                result = await self.rating_judge.evaluate_joke_async(joke)
                
                # Successful evaluation
                print(" ✓", flush=True)
                return result
                
            except Exception as e:
                error_msg = str(e)
                
                # Check for specific error types
                if "rate limit" in error_msg.lower():
                    wait_time = min(2 ** attempt, 60)  # Exponential backoff, max 60s
                    print(f"\n⏳ Rate limit hit, waiting {wait_time}s...", flush=True)
                    await asyncio.sleep(wait_time)
                elif "timeout" in error_msg.lower():
                    wait_time = 5
                    print(f"\n⏱️  Timeout, waiting {wait_time}s...", flush=True)
                    await asyncio.sleep(wait_time)
                else:
                    wait_time = 2
                    print(f"\n⚠️  Error: {error_msg[:50]}..., retrying in {wait_time}s", flush=True)
                    await asyncio.sleep(wait_time)
                
                # If this was the last attempt, return None
                if attempt == max_retries - 1:
                    return None
        
        return None
    
    def _display_joke_result(self, result: RatingResult, joke_index: int):
        """Display brief result for a processed joke"""
        if result.admissibility_results.is_admissible:
            # Show rating with visual indicator
            rating_bar = self._create_rating_bar(result.overall_rating)
            print(f"   Joke {joke_index + 1}: {rating_bar} Rating: {result.overall_rating:.2f} "
                  f"(Max: {result.max_score}, Mean: {result.mean_score:.2f})")
            
            # Show categories
            if result.assigned_categories:
                categories_str = ", ".join(result.assigned_categories)
                print(f"   Categories: {categories_str}")
            
            # Show top factors
            if result.factor_scores:
                top_factors = sorted(result.factor_scores.items(), 
                                   key=lambda x: x[1], reverse=True)[:3]
                factors_str = ", ".join([f"{name}({score})" for name, score in top_factors])
                print(f"   Top factors: {factors_str}")
        else:
            # Show why joke was rejected
            failed_checks = []
            ar = result.admissibility_results
            if not ar.intent_check.passed:
                failed_checks.append("intent")
            if not ar.completeness_check.passed:
                failed_checks.append("completeness")
            if not ar.appropriateness_check.passed:
                failed_checks.append("appropriateness")
            if not ar.coherence_check.passed:
                failed_checks.append("coherence")
            if not ar.accessibility_check.passed:
                failed_checks.append("accessibility")
            
            print(f"   Joke {joke_index + 1}: ❌ Not admissible (failed: {', '.join(failed_checks)})")
    
    def _create_rating_bar(self, rating: float, width: int = 20) -> str:
        """Create a visual rating bar"""
        filled = int((rating / 5.0) * width)
        empty = width - filled
        return f"[{'█' * filled}{'░' * empty}]"
    
    def _display_progress(self, total_jokes: int):
        """Display overall progress"""
        elapsed = (datetime.now() - self.start_time).total_seconds()
        progress_pct = (self.processed_count / total_jokes) * 100
        
        # Estimate time remaining
        if self.processed_count > 0:
            avg_time_per_joke = elapsed / self.processed_count
            remaining_jokes = total_jokes - self.processed_count
            eta_seconds = avg_time_per_joke * remaining_jokes
            eta_minutes = int(eta_seconds // 60)
            eta_seconds = int(eta_seconds % 60)
            eta_str = f"{eta_minutes}m {eta_seconds}s"
        else:
            eta_str = "calculating..."
        
        print(f"\n{'='*60}")
        print(f"Progress: {self.processed_count}/{total_jokes} ({progress_pct:.1f}%)")
        print(f"Elapsed: {int(elapsed//60)}m {int(elapsed%60)}s | ETA: {eta_str}")
        print(f"Failed: {len(self.failed_jokes)}")
        print(f"{'='*60}")
    
    def _display_final_summary(self, all_results: List[RatingResult], total_jokes: int):
        """Display final processing summary"""
        elapsed = (datetime.now() - self.start_time).total_seconds()
        admissible = sum(1 for r in all_results if r.admissibility_results.is_admissible)
        
        print(f"\n{'='*70}")
        print(f"RATING PHASE COMPLETE")
        print(f"{'='*70}")
        print(f"Total jokes processed: {len(all_results)}/{total_jokes}")
        print(f"Admissible jokes: {admissible} ({(admissible/total_jokes*100):.1f}%)")
        print(f"Failed to process: {len(self.failed_jokes)}")
        print(f"Total time: {int(elapsed//60)}m {int(elapsed%60)}s")
        print(f"Average time per joke: {elapsed/total_jokes:.1f}s")
        
        if self.failed_jokes:
            print(f"\n⚠️  Failed jokes:")
            for failed in self.failed_jokes[:5]:  # Show first 5
                print(f"   - Joke {failed['joke'].id}: {failed['error']}")
            if len(self.failed_jokes) > 5:
                print(f"   ... and {len(self.failed_jokes) - 5} more")
        
        # Show rating distribution
        if admissible > 0:
            admissible_results = [r for r in all_results if r.admissibility_results.is_admissible]
            ratings = [r.overall_rating for r in admissible_results]
            
            print(f"\n📊 Rating Distribution:")
            bins = [0, 1, 2, 3, 4, 5]
            for i in range(len(bins) - 1):
                count = sum(1 for r in ratings if bins[i] <= r < bins[i+1])
                bar_width = int((count / admissible) * 40)
                bar = '█' * bar_width
                print(f"   {bins[i]}-{bins[i+1]}: {bar} {count} jokes")
            
            # Show top 3 jokes
            top_3 = sorted(admissible_results, key=lambda x: x.overall_rating, reverse=True)[:3]
            print(f"\n🏆 Top 3 Jokes:")
            for i, joke in enumerate(top_3):
                print(f"   {i+1}. Joke {joke.joke_id} - Rating: {joke.overall_rating:.2f}")
                print(f"      {joke.joke_text[:80]}{'...' if len(joke.joke_text) > 80 else ''}")
        
        print(f"{'='*70}\n")

