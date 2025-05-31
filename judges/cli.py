import argparse
import asyncio
import sys
from pathlib import Path
from datetime import datetime
from typing import Tuple, Optional, List

from judges.main_judge import JokeJudgeSystem
from judges.models import RatingResult


async def evaluate_jokes_programmatic(
    jokes_file: str,
    batch_size: int = 20,
    top_count: int = 20,
    bypass_cache: bool = False,
    rating_only: bool = False,
    retries: int = 5
):
    """
    Programmatic interface for joke evaluation system.
    
    Args:
        jokes_file: Path to XML file containing jokes
        batch_size: Number of jokes to process in parallel (default: 20)
        top_count: Number of top jokes to advance to tournament (default: 20)
        bypass_cache: Bypass DSPy caching mechanism (default: False)
        rating_only: Only run rating phase without tournament (default: False)
        retries: Number of retry attempts for LLM calls (default: 5)
    
    Returns:
        List[RatingResult] if rating_only=True
        Tuple[int, str] (winner_id, winner_text) if rating_only=False
        None if no valid jokes found
        
    Example:
        # Rating only
        best_jokes = await evaluate_jokes_programmatic("jokes.xml", rating_only=True)
        
        # Full tournament
        winner_id, winner_text = await evaluate_jokes_programmatic("jokes.xml", rating_only=False)
    """
    
    if rating_only:
        # Rating-only mode
        best_jokes = await run_rating_only_evaluation(
            jokes_file, 
            batch_size, 
            top_count,
            bypass_cache,
            retries
        )
        return best_jokes
    else:
        # Full tournament mode
        winner, log_dir = await run_batch_evaluation(
            jokes_file, 
            batch_size, 
            top_count,
            bypass_cache,
            retries
        )
        return winner

def main():
    """Entry point for: python -m judges <jokes_file.xml> [options]"""
    args = parse_arguments()
    
    # Run the evaluation
    if args.rating_only:
        # Rating-only mode
        best_jokes = asyncio.run(run_rating_only_evaluation(
            args.jokes_file, 
            args.batch_size, 
            args.top_count,
            args.bypass_cache,
            args.retries
        ))
        
        if best_jokes:
            display_rating_only_results(best_jokes)
        else:
            print("\033[91mError: No valid jokes found in input file\033[0m")
            sys.exit(1)
    else:
        # Full tournament mode
        winner, log_dir = asyncio.run(run_batch_evaluation(
            args.jokes_file, 
            args.batch_size, 
            args.top_count,
            args.bypass_cache,
            args.retries
        ))
        
        # Display results
        if winner:
            display_final_results(winner[0], winner[1], log_dir)
        else:
            print("\033[91mError: No valid jokes found in input file\033[0m")
            sys.exit(1)

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description="LLM-based joke evaluation system",
        usage="python -m judges <jokes_file.xml> [options]"
    )
    
    # Required positional argument
    parser.add_argument(
        'jokes_file',
        type=str,
        help='Path to XML file containing jokes'
    )
    
    # Optional arguments
    parser.add_argument(
        '--batch-size',
        type=int,
        default=20,
        help='Number of jokes to process in parallel (default: 20)'
    )
    
    parser.add_argument(
        '--top-count',
        type=int,
        default=20,
        help='Number of top jokes to advance to tournament (default: 20)'
    )
    
    parser.add_argument(
        '--bypass-cache',
        action='store_true',
        help='Bypass DSPy caching mechanism'
    )
    
    parser.add_argument(
        '--rating-only',
        action='store_true',
        help='Only run rating phase and return top jokes without tournament'
    )
    
    parser.add_argument(
        '--retries',
        type=int,
        default=5,
        help='Number of retry attempts for LLM calls (default: 5, 0 = no retries)'
    )
    
    return parser.parse_args()

async def run_batch_evaluation(jokes_file_path: str, batch_size: int = 20, 
                              top_count: int = 20, bypass_cache: bool = False,
                              max_retries: int = 5) -> Tuple[Optional[Tuple[int, str]], Optional[str]]:
    """Run complete evaluation pipeline"""
    # Extract filename for output directory
    filename = Path(jokes_file_path).stem
    timestamp = datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
    output_dir = f"logs/{filename}_{timestamp}"
    
    # Initialize system with bypass_cache and max_retries
    judge_system = JokeJudgeSystem(output_dir, bypass_cache=bypass_cache, max_retries=max_retries)
    
    # Run evaluation
    result = await judge_system.run_complete_evaluation(
        jokes_file_path, 
        batch_size, 
        top_count
    )
    
    if result[0] is None:
        return (None, None)
    
    return result

async def run_rating_only_evaluation(jokes_file_path: str, batch_size: int = 20,
                                    top_count: int = 20, bypass_cache: bool = False,
                                    max_retries: int = 5) -> Optional[List[RatingResult]]:
    """Run only the rating phase and return top jokes"""
    # Extract filename for output directory
    filename = Path(jokes_file_path).stem
    timestamp = datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
    output_dir = f"logs/{filename}_{timestamp}_rating_only"
    
    # Initialize system with bypass_cache and max_retries
    judge_system = JokeJudgeSystem(output_dir, bypass_cache=bypass_cache, max_retries=max_retries)
    
    # Run rating-only evaluation
    top_jokes = await judge_system.run_rating_only_evaluation(
        jokes_file_path,
        batch_size,
        top_count
    )
    
    return top_jokes

def display_rating_only_results(top_jokes: List[RatingResult]):
    """Display the top jokes from rating phase"""
    print("\n" + "=" * 60)
    print(" " * 20 + "TOP RATED JOKES")
    print("=" * 60)
    
    for i, joke in enumerate(top_jokes, 1):
        print(f"\n{i}. Joke ID: {joke.joke_id}")
        print(f"   Rating: {joke.overall_rating:.2f} (Max: {joke.max_score}, Mean: {joke.mean_score:.2f})")
        print(f"   Categories: {', '.join(joke.assigned_categories)}")
        print(f"   Text: {joke.joke_text}")
        
        # Show top 3 factors
        if joke.factor_scores:
            top_factors = sorted(joke.factor_scores.items(), key=lambda x: x[1], reverse=True)[:3]
            print(f"   Top factors: {', '.join(f'{f}({s})' for f, s in top_factors)}")
    
    print("\n" + "=" * 60)

def display_progress(current_joke: int, total_jokes: int, status: str):
    """Print progress updates to terminal"""
    print(f"[Joke {current_joke}/{total_jokes}] {status}...")

def display_final_results(winner_id: int, winner_text: str, log_dir: str):
    """Display the tournament winner and log location"""
    print("\n" + "=" * 40)
    print(" " * 10 + "TOURNAMENT WINNER")
    print("=" * 40)
    print(f"Joke ID: {winner_id}")
    print(f"Joke Text: {winner_text}")
    print()
    print(f"Full results saved to: {log_dir}")
    print("=" * 40)

if __name__ == "__main__":
    main()