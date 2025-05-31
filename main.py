"""System orchestration for joke generation pipeline"""

import os
import asyncio
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, Tuple
from utilities.dspy_client import ClaudeClient
from utilities.xml_logger import XMLLogger
from utilities.generator_utils import ensure_directory_exists
from generator.topic_processor import process_user_input
from generator.hook_template_generator import generate_hook_template_contexts
from generator.higher_order_grouper import generate_higher_order_groups
from generator.joke_engine import generate_full_joke_set
from generator.output_formatter import format_jokes_to_xml
from generator.generator_models import JokePortfolio, FirstOrderTriplet, HigherOrderGroup
from judges.cli import evaluate_jokes_programmatic


def run_complete_generation_and_judging(topic_input: str = None, first_order_only: bool = False,
                                      generation_only: bool = False, output_dir: str = "output/",
                                      batch_size: int = 5, retries: int = 3, 
                                      bypass_cache: bool = False) -> Dict:
    """Main orchestration function"""
    
    # Create client with cache setting
    client = ClaudeClient(cache=not bypass_cache)
    
    # Process topics
    topic_set = process_user_input(topic_input)
    print(f"Processing topics: {', '.join(topic_set)}")
    
    # Create log directory
    log_dir = create_timestamped_log_directory()
    print(f"Log directory: {log_dir}")
    
    # Run generation pipeline
    portfolio = asyncio.run(execute_generation_pipeline(
        topic_set, client, first_order_only, log_dir, output_dir, batch_size, retries
    ))
    
    # Format output
    output_file = format_jokes_to_xml(portfolio, "generated_jokes.xml", output_dir)
    
    results = {
        'total_jokes': len(portfolio),
        'output_file': output_file,
        'log_dir': log_dir,
        'topics': list(topic_set)
    }
    
    # Run judge system if not generation-only
    if not generation_only:
        judge_results = asyncio.run(integrate_with_judge_system(
            output_file, len(portfolio), batch_size, retries, bypass_cache
        ))
        results.update(judge_results)
        
        # Get winner joke text from portfolio
        if 'winner_id' in judge_results and judge_results['winner_id']:
            winner_joke = portfolio.get_joke_by_id(judge_results['winner_id'])
            if winner_joke:
                results['winner_text'] = winner_joke.text
    
    return results


async def execute_generation_pipeline(topic_set: set, client: ClaudeClient, first_order_only: bool,
                                    log_dir: str, output_dir: str, batch_size: int, 
                                    retries: int) -> JokePortfolio:
    """Execute core generation pipeline"""
    
    logger = XMLLogger(log_dir)
    
    # Stage 1: Generate hook-template contexts
    print("\n=== Stage 1: Generating Hook-Template Contexts ===")
    first_order_triplets = await generate_hook_template_contexts(topic_set, client, retries)
    
    # Log first-order contexts
    logger.log_first_order_contexts(first_order_triplets, log_dir)
    
    # Stage 2: Create higher-order groups (unless first_order_only)
    higher_order_groups = []
    if not first_order_only:
        print("\n=== Stage 2: Creating Higher-Order Groups ===")
        higher_order_groups = await generate_higher_order_groups(
            first_order_triplets, topic_set, client, retries
        )
        
        # Log higher-order groups
        logger.log_higher_order_groups(higher_order_groups, log_dir)
    
    # Stage 3: Generate jokes
    print("\n=== Stage 3: Generating Jokes ===")
    jokes = await generate_full_joke_set(
        first_order_triplets, higher_order_groups, topic_set, client
    )
    
    # Create portfolio
    portfolio = JokePortfolio()
    portfolio.add_jokes(jokes)
    
    return portfolio


async def integrate_with_judge_system(xml_output_file: str, joke_count: int, batch_size: int, 
                                    retries: int, bypass_cache: bool) -> Dict:
    """Call judge system using the programmatic interface"""
    
    # Adjust parameters based on joke count
    adjusted_batch_size = min(joke_count, batch_size) if joke_count < 10 else batch_size
    adjusted_top_count = min(joke_count, 15)
    
    print(f"\n=== Running Judge System ===")
    print(f"Evaluating {joke_count} jokes with batch size {adjusted_batch_size}")
    
    try:
        # Call the judge system programmatically
        result = await evaluate_jokes_programmatic(
            jokes_file=xml_output_file,
            batch_size=adjusted_batch_size,
            top_count=adjusted_top_count,
            bypass_cache=bypass_cache,
            rating_only=False,  # We want the full tournament
            retries=retries
        )
        
        if result is None:
            return {
                'winner_id': None,
                'judge_output': "No valid jokes found for evaluation",
                'judge_success': False
            }
        
        # Unpack the winner tuple
        winner_id, winner_text = result
        
        return {
            'winner_id': winner_id,
            'winner_text': winner_text,
            'judge_output': f"Tournament completed. Winner: Joke ID {winner_id}",
            'judge_success': True
        }
        
    except Exception as e:
        print(f"Error running judge system: {e}")
        return {
            'winner_id': None,
            'judge_output': str(e),
            'judge_success': False
        }


def create_timestamped_log_directory() -> str:
    """Create timestamped log directory"""
    timestamp = datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
    log_dir = f"logs/generator_{timestamp}"
    return ensure_directory_exists(log_dir)


def log_intermediate_results(stage_name: str, data: any, log_dir: str) -> None:
    """Log intermediate results (handled by XMLLogger in pipeline)"""
    pass  # Logging is done directly in execute_generation_pipeline 