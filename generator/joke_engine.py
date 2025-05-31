"""Generate jokes from contexts using async parallel processing"""

import asyncio
import dspy
from typing import List
from utilities.dspy_client import ClaudeClient
from utilities.generator_utils import format_topic_set_for_prompt, flatten_all_generation_contexts
from generator.generator_models import (
    GenerationContext, GeneratedJoke, JokePortfolio,
    FirstOrderContext, HigherOrderContext
)
from generator.generator_signatures import JokeGenerationSignature


async def generate_jokes_from_all_contexts(topic_set: set, first_order_contexts: List[FirstOrderContext],
                                         higher_order_groups: List[HigherOrderContext], 
                                         client: ClaudeClient, batch_size: int = 5, 
                                         retries: int = 3) -> JokePortfolio:
    """Orchestrate joke generation from all contexts"""
    
    # Flatten all contexts
    flattened_contexts = flatten_all_generation_contexts(first_order_contexts, higher_order_groups)
    
    if not flattened_contexts:
        raise ValueError("No contexts available for joke generation")
    
    print(f"Generating jokes from {len(flattened_contexts)} contexts in batches of {batch_size}")
    
    # Create portfolio
    portfolio = JokePortfolio()
    
    # Process in batches
    for i in range(0, len(flattened_contexts), batch_size):
        batch = flattened_contexts[i:i + batch_size]
        batch_num = (i // batch_size) + 1
        print(f"\nProcessing batch {batch_num}/{(len(flattened_contexts) + batch_size - 1) // batch_size}")
        
        # Generate jokes for batch
        batch_jokes = await generate_jokes_batch(topic_set, batch, client, retries)
        portfolio.add_jokes(batch_jokes)
        
        # Small delay between batches
        if i + batch_size < len(flattened_contexts):
            await asyncio.sleep(1)
    
    if len(portfolio) == 0:
        raise ValueError("No jokes were generated from any context")
    
    print(f"\nTotal jokes generated: {len(portfolio)}")
    return portfolio


async def generate_jokes_batch(topic_set: set, context_batch: List[GenerationContext], 
                             client: ClaudeClient, retries: int = 3) -> List[GeneratedJoke]:
    """Process a batch of contexts in parallel"""
    
    # Create tasks for each context
    tasks = []
    for context in context_batch:
        task = generate_jokes_from_context(topic_set, context, client, retries)
        tasks.append(task)
    
    # Run all tasks in parallel
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Collect successful results
    all_jokes = []
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            print(f"Context {i+1} failed: {str(result)[:100]}...")
        elif result:
            all_jokes.extend(result)
    
    return all_jokes


async def generate_jokes_from_context(topic_set: set, context: GenerationContext, 
                                    client: ClaudeClient, retries: int = 3) -> List[GeneratedJoke]:
    """Generate jokes from a single context"""
    
    # Format inputs
    formatted_topics = format_topic_set_for_prompt(topic_set)
    
    # Initialize predictor
    predictor = dspy.Predict(JokeGenerationSignature)
    
    # Implement retry logic
    return await _retry_on_error(
        _generate_jokes_with_predictor,
        predictor, formatted_topics, context, retries
    )


async def _generate_jokes_with_predictor(predictor, formatted_topics: str, 
                                       context: GenerationContext, retries: int) -> List[GeneratedJoke]:
    """Internal function to generate jokes with DSPy predictor"""
    
    result = predictor(
        topic_description=formatted_topics,
        context_guidance=f"""Generate one or more brilliant, novel jokes about: {formatted_topics}

            COMEDIC GUIDANCE:
            {context.details}

            GENERATOR EXPLANATION:
            {context.explanation}

            CRITICAL CREATIVE FREEDOM INSTRUCTIONS:
            - You do NOT need to use the exact hooks, templates, or context provided
            - You CAN completely modify, adapt, or ignore any provided elements
            - You CAN use elements as inspiration and create entirely new approaches
            - You CAN combine elements in unexpected ways not suggested in the context
            - You CAN use only parts of templates or create hybrid templates
            - You CAN transform hooks into related concepts or wordplay variations
            - Your PRIMARY GOAL is creating the FUNNIEST, most NOVEL jokes possible

            NOVELTY REQUIREMENTS:
            - Create completely original jokes that don't exist anywhere
            - Use your creativity and imagination extensively
            - Avoid clichéd or common joke formats unless you can transform them uniquely
            - Strive for surprising, unexpected comedic approaches
            - Invent new wordplay, concepts, or comedic connections

            QUALITY PRIORITIES:
            1. Maximum humor impact and surprise
            2. Complete originality and novelty
            3. Clever use of language, concepts, or structure
            4. Appropriateness for general audiences
            5. MANDATORY connection to the topic(s) - this is required and non-negotiable

            The provided hooks, templates, and explanations should serve as INSPIRATION and STARTING POINTS for your creativity, not as rigid requirements to follow.

            Generate one or more jokes, each as a separate, complete joke. You decide how many jokes to create based on your creative inspiration.

            Output format should be structured list of joke objects."""
    )
    
    # Parse output
    jokes = []
    if hasattr(result, 'generated_jokes') and result.generated_jokes:
        for joke_item in result.generated_jokes:
            if hasattr(joke_item, 'text') and joke_item.text:
                jokes.append(GeneratedJoke(text=joke_item.text.strip()))
            elif isinstance(joke_item, str) and joke_item.strip():
                jokes.append(GeneratedJoke(text=joke_item.strip()))
    
    if not jokes:
        raise ValueError("No valid jokes in LLM response")
    
    return jokes


async def _retry_on_error(func, *args, **kwargs):
    """Generic retry wrapper for async functions"""
    max_retries = kwargs.get('retries', 3)
    
    for attempt in range(max_retries + 1):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            if attempt == max_retries:
                raise e
            else:
                wait_time = min(2 ** attempt, 10)  # Exponential backoff, max 10s
                print(f"Retry {attempt + 1}/{max_retries}: {str(e)[:50]}... Waiting {wait_time}s")
                await asyncio.sleep(wait_time)

