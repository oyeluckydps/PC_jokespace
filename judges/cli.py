import argparse
import asyncio
import sys
from pathlib import Path
from datetime import datetime
from typing import Tuple, Optional

from judges.main_judge import JokeJudgeSystem

def main():
    """Entry point for: python -m judges <jokes_file.xml> [--batch-size N] [--top-count N]"""
    args = parse_arguments()
    
    # Run the evaluation
    winner, log_dir = asyncio.run(run_batch_evaluation(
        args.jokes_file, 
        args.batch_size, 
        args.top_count
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
        usage="python -m judges <jokes_file.xml> [--batch-size N] [--top-count N]"
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
    
    return parser.parse_args()

async def run_batch_evaluation(jokes_file_path: str, batch_size: int = 20, 
                              top_count: int = 20) -> Tuple[Optional[Tuple[int, str]], Optional[str]]:
    """Run complete evaluation pipeline"""
    # Extract filename for output directory
    filename = Path(jokes_file_path).stem
    timestamp = datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
    output_dir = f"logs/{filename}_{timestamp}"
    
    # Initialize system
    judge_system = JokeJudgeSystem(output_dir)
    
    # Run evaluation
    result = await judge_system.run_complete_evaluation(
        jokes_file_path, 
        batch_size, 
        top_count
    )
    
    if result[0] is None:
        return (None, None)
    
    return result

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

