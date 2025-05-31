"""System orchestration for joke generation pipeline"""

import os
import asyncio
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional
from utilities.dspy_client import ClaudeClient
from utilities.xml_logger import XMLLogger
from utilities.generator_utils import ensure_directory_exists
from generator.topic_processor import process_user_input
from generator.hook_template_generator import generate_hook_template_contexts
from generator.higher_order_grouper import generate_higher_order_groups
from generator.joke_engine import generate_full_joke_set
from generator.output_formatter import format_jokes_to_xml
from generator.generator_models import JokePortfolio, FirstOrderTriplet, HigherOrderGroup


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
        judge_results = integrate_with_judge_system(output_file, batch_size, retries, bypass_cache)
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


def integrate_with_judge_system(xml_output_file: str, batch_size: int, retries: int, 
                              bypass_cache: bool) -> Dict:
    """Call judge system and parse results"""
    
    # Count jokes in file to adjust parameters
    try:
        import xml.etree.ElementTree as ET
        tree = ET.parse(xml_output_file)
        joke_count = len(tree.findall('.//joke'))
    except:
        joke_count = 20  # Default assumption
    
    # Adjust parameters
    adjusted_batch_size = min(joke_count, batch_size) if joke_count < 10 else batch_size
    adjusted_top_count = min(joke_count, 15)
    
    # Build command
    cmd = [
        'python', '-m', 'judges', 
        xml_output_file,
        '--batch-size', str(adjusted_batch_size),
        '--top-count', str(adjusted_top_count),
        '--retries', str(retries)
    ]
    
    if bypass_cache:
        cmd.append('--bypass-cache')
    
    print(f"\n=== Running Judge System ===")
    print(f"Command: {' '.join(cmd)}")
    
    try:
        # Run judge system
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=os.getcwd())
        
        # Stream output
        print(result.stdout)
        if result.stderr:
            print("Errors:", result.stderr)
        
        # Parse winner from output
        winner_id = None
        for line in result.stdout.split('\n'):
            if 'Joke ID:' in line and 'TOURNAMENT WINNER' in result.stdout:
                # Extract ID from "Joke ID: X" pattern
                try:
                    winner_id = int(line.split('Joke ID:')[1].strip().split()[0])
                    break
                except:
                    pass
        
        return {
            'winner_id': winner_id,
            'judge_output': result.stdout,
            'judge_success': result.returncode == 0
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

