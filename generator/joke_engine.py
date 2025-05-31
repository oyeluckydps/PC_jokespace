"""Generate jokes from contexts using DSPy"""

import asyncio
import dspy
from typing import List, Union, Dict
from utilities.dspy_client import ClaudeClient
from utilities.generator_utils import format_topic_set_for_prompt
from generator.models import (
    FirstOrderTriplet, HigherOrderGroup, 
    GeneratedJoke, JokeOutput
)
from generator.signatures import JokeGenerationSignature


async def generate_jokes_from_context(
    context: Union[FirstOrderTriplet, HigherOrderGroup],
    topic_set: set,
    client: ClaudeClient,
    retries: int = 3
) -> List[GeneratedJoke]:
    """Generate jokes from either first-order triplet or higher-order group"""
    
    # Format topics for prompt
    formatted_topics = format_topic_set_for_prompt(topic_set)
    
    # Initialize DSPy predictor
    predictor = dspy.Predict(JokeGenerationSignature)
    
    # Determine context type and create appropriate task description
    if isinstance(context, FirstOrderTriplet):
        task_description = """Generate 1-3 ORIGINAL, FUNNY jokes using the provided hook-template-explanation as INSPIRATION (not a rigid formula):

                            1. JOKE REQUIREMENTS:
                            - Create completely NEW jokes, not examples from the explanation
                            - Use the hook as a creative starting point, but feel free to extend/modify
                            - Adapt the template structure creatively - don't follow it rigidly
                            - Ensure jokes are genuinely funny and surprising
                            - Make jokes feel natural and conversational

                            2. QUALITY STANDARDS:
                            - Strong, unexpected punchlines that subvert expectations
                            - Clear setup that doesn't telegraph the punchline
                            - Concise delivery without unnecessary words
                            - Original content not found in typical joke collections

                            3. USE THE CONTEXT AS INSPIRATION:
                            - The explanation shows POSSIBILITIES, not requirements
                            - Feel free to combine, twist, or reimagine the suggestions
                            - The goal is funny, original jokes that work on their own

                            Generate 1-3 distinct, high-quality jokes that would make people laugh."""
    else:  # HigherOrderGroup
        task_description = """Generate 2-5 SOPHISTICATED, MULTI-LAYERED jokes using the provided group of hook-template pairs:

                            1. ADVANCED JOKE REQUIREMENTS:
                            - Create jokes that utilize MULTIPLE elements from the group
                            - Build complex humor through interaction of different hooks/templates
                            - Layer different comedic techniques for sophisticated effect
                            - Ensure each joke stands alone as genuinely funny

                            2. SYNERGISTIC TECHNIQUES:
                            - Combine hooks for unexpected connections
                            - Use multiple templates in sequence or nested structures
                            - Create callbacks, reversals, or progressive escalation
                            - Build to bigger payoffs through element interaction

                            3. QUALITY STANDARDS:
                            - Intelligent humor that rewards attention
                            - Natural flow despite complexity
                            - Clear through-line even with multiple elements
                            - Original, memorable content

                            Use the group explanation as a guide for creating sophisticated, funny jokes.
                            Generate 2-5 distinct jokes that showcase the synergistic potential."""
    
    # Define synchronous function for DSPy call
    def sync_joke_generation():
        # Retry logic within the synchronous function
        for attempt in range(retries + 1):
            try:
                # Make LLM call (synchronous DSPy predictor)
                result = predictor(
                    task_description=task_description,
                    topic=formatted_topics,
                    context_guidance=context  # Pass the actual FirstOrderTriplet or HigherOrderGroup object
                )
                
                # Convert JokeOutput objects to GeneratedJoke objects
                if hasattr(result, 'generated_jokes') and result.generated_jokes:
                    jokes = []
                    for joke_output in result.generated_jokes:
                        jokes.append(GeneratedJoke(text=joke_output.text))
                    
                    print(f"Generated {len(jokes)} jokes from {'first-order' if isinstance(context, FirstOrderTriplet) else 'higher-order'} context")
                    return jokes
                else:
                    raise ValueError("No valid jokes in LLM response")
                    
            except Exception as e:
                if attempt < retries:
                    print(f"Attempt {attempt + 1} failed: {str(e)[:100]}... Retrying in 2s")
                    import time
                    time.sleep(2)  # Use synchronous sleep within the sync function
                else:
                    raise Exception(f"Failed to generate jokes after {retries + 1} attempts: {str(e)}")
        
        return []
    
    # Run the synchronous DSPy call in a thread pool to avoid blocking the event loop
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, sync_joke_generation)


async def generate_full_joke_set(
    first_order_triplets: List[FirstOrderTriplet],
    higher_order_groups: List[HigherOrderGroup],
    topic_set: set,
    client: ClaudeClient,
    jokes_per_first_order: int = 2,
    jokes_per_higher_order: int = 3
) -> List[GeneratedJoke]:
    """Generate jokes from all contexts (both first-order and higher-order)"""
    
    all_jokes = []
    
    # Generate jokes from first-order triplets
    print(f"Generating jokes from {len(first_order_triplets)} first-order contexts...")
    first_order_tasks = [
        generate_jokes_from_context(triplet, topic_set, client)
        for triplet in first_order_triplets
    ]
    
    first_order_results = await asyncio.gather(*first_order_tasks, return_exceptions=True)
    
    for i, result in enumerate(first_order_results):
        if isinstance(result, Exception):
            print(f"Failed to generate jokes from first-order context {i+1}: {str(result)[:100]}")
        else:
            all_jokes.extend(result)
    
    # Generate jokes from higher-order groups
    print(f"Generating jokes from {len(higher_order_groups)} higher-order groups...")
    higher_order_tasks = [
        generate_jokes_from_context(group, topic_set, client)
        for group in higher_order_groups
    ]
    
    higher_order_results = await asyncio.gather(*higher_order_tasks, return_exceptions=True)
    
    for i, result in enumerate(higher_order_results):
        if isinstance(result, Exception):
            print(f"Failed to generate jokes from higher-order group {i+1}: {str(result)[:100]}")
        else:
            all_jokes.extend(result)
    
    # Assign sequential IDs to all jokes
    for i, joke in enumerate(all_jokes):
        joke.id = i + 1
    
    print(f"Total jokes generated: {len(all_jokes)}")
    return all_jokes