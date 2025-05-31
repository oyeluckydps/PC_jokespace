# ./cli.py
"""Command line interface for joke generator"""

import argparse
import time
import sys
from pathlib import Path
from main import run_complete_generation_and_judging # Updated import


def main():
    """Entry point for CLI"""
    args = parse_arguments()
    
    # Validate arguments
    if args.batch_size <= 0:
        print("Error: batch-size must be positive")
        sys.exit(1)
    
    if args.retries < 0:
        print("Error: retries cannot be negative")
        sys.exit(1)
    
    # Run pipeline
    try:
        start_time = time.time()
        results = run_pipeline_with_args(args)
        elapsed_time = time.time() - start_time
        
        # Display results
        display_results(results, elapsed_time)
        
    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\nError: {e}")
        sys.exit(1)


def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        prog='python -m generator.cli',
        description='AI-powered joke generation system',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m generator.cli                           # Random topic, full pipeline
  python -m generator.cli --topic "cats, dogs"      # Specific topics
  python -m generator.cli --generation-only          # Skip judging
  python -m generator.cli --first-order-only         # Skip higher-order groups
  python -m generator.cli --bypass-cache             # Disable caching
        """
    )
    
    parser.add_argument(
        '--topic',
        type=str,
        default=None,
        help='Comma-separated topics (optional, defaults to random)'
    )
    
    parser.add_argument(
        '--first-order-only',
        action='store_true',
        help='Skip higher-order group generation'
    )
    
    parser.add_argument(
        '--generation-only',
        action='store_true',
        help='Skip judge system integration'
    )
    
    parser.add_argument(
        '--output-dir',
        type=str,
        default='output/',
        help='Custom output directory (default: output/)'
    )
    
    parser.add_argument(
        '--batch-size',
        type=int,
        default=5,
        help='Async batch size for joke generation (default: 5)'
    )
    
    parser.add_argument(
        '--retries',
        type=int,
        default=3,
        help='Number of retry attempts for LLM calls (default: 3)'
    )
    
    parser.add_argument(
        '--bypass-cache',
        action='store_true',
        help='Bypass DSPy caching mechanism'
    )
    
    return parser.parse_args()


def run_pipeline_with_args(args: argparse.Namespace) -> dict:
    """Convert CLI args to pipeline parameters"""
    
    # Validate output directory
    try:
        Path(args.output_dir).mkdir(parents=True, exist_ok=True)
    except Exception as e:
        raise ValueError(f"Cannot create output directory: {e}")
    
    # Run pipeline
    return run_complete_generation_and_judging(
        topic_input=args.topic,
        first_order_only=args.first_order_only,
        generation_only=args.generation_only,
        output_dir=args.output_dir,
        batch_size=args.batch_size,
        retries=args.retries,
        bypass_cache=args.bypass_cache
    )


def display_results(results: dict, elapsed_time: float) -> None:
    """Display results to user"""
    
    print("\n" + "=" * 60)
    print(" " * 20 + "GENERATION COMPLETE")
    print("=" * 60)
    
    # Basic info
    print(f"\nTopics: {', '.join(results['topics'])}")
    print(f"Total jokes generated: {results['total_jokes']}")
    print(f"Output file: {results['output_file']}")
    print(f"Log directory: {results['log_dir']}")
    
    # Judge results if available
    if 'winner_id' in results and results['winner_id']:
        print("\n" + "-" * 60)
        print(" " * 20 + "TOURNAMENT WINNER")
        print("-" * 60)
        print(f"Joke ID: {results['winner_id']}")
        if 'winner_text' in results:
            print(f"Text: {results['winner_text']}")
    elif 'judge_success' in results and not results['judge_success']:
        print("\nJudge system encountered an error")
    
    # Performance
    print(f"\nExecution time: {elapsed_time:.1f} seconds")
    print("=" * 60)


if __name__ == "__main__":
    main()