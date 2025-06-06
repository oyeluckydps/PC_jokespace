# ./generator/higher_order_grouper.py
"""Create higher-order groups from hook-template-context combinations using DSPy"""

import asyncio
import dspy
from typing import List, Set
from generator.models import FirstOrderTriplet, HigherOrderGroup, HookTemplatePair
from generator.signatures import HigherOrderGroupingSignature
from utilities.dspy_client import ClaudeClient
from utilities.generator_utils import format_topic_set_for_prompt


def get_num_of_jokes(jokespace_size: str) -> str:
    """Get number of jokes based on jokespace size"""
    if jokespace_size == 'small':
        return "1 to 3"
    elif jokespace_size == 'medium':
        return "3 to 8"
    elif jokespace_size == 'large':
        return "8 or more"
    else:
        raise ValueError(f"Invalid jokespace size: {jokespace_size}")


async def generate_higher_order_groups(
    first_order_triplets: List[FirstOrderTriplet], 
    topic_set: set, 
    client: ClaudeClient, 
    retries: int = 3,
    jokespace_size: str = 'medium'
) -> List[HigherOrderGroup]:
    """Create synergistic groups from hook-template-context triplets"""
    
    # Get number of jokes based on jokespace size
    num_of_jokes = get_num_of_jokes(jokespace_size)
    
    # Format topics for prompt
    formatted_topics = format_topic_set_for_prompt(topic_set)
    
    # Initialize DSPy predictor
    predictor = dspy.Predict(HigherOrderGroupingSignature)
    
    # Detailed task description
    task_description = f"""Analyze the provided hook-template-context triplets and create {num_of_jokes} SYNERGISTIC GROUPS following these guidelines:

                        1. GROUP FORMATION:
                        - Each group should contain 2 or more hook-template pairs that work together to form a meta hook-template for a funny joke
                        - Select pairs that create MULTI-LAYERED humor opportunities
                        - You may look for complementary hooks that build on each other
                        - You may look for contrasting hooks that contradict to bring humor
                        - Ensure templates work together for complex joke structures

                        2. SYNERGY CRITERIA:
                        - Semantic connections between hooks (shared concepts, contrasts, progressions)
                        - Template compatibility (formats that can be combined or sequenced)
                        - Comedic escalation potential (setups that build to bigger punchlines)
                        - Thematic unity while maintaining diversity

                        3. GROUP EXPLANATION Requirements:
                        - Explain the SYNERGISTIC potential of the combination
                        - Describe how to create SOPHISTICATED jokes using multiple elements
                        - Detail specific multi-layered comedic techniques enabled
                        - Show how the group creates humor beyond individual pairs
                        - Include strategies for combining elements

                        Focus on groups that enable complex, intelligent humor through interaction of multiple elements to create humour that may be complex or simple.
                        Generate {num_of_jokes} distinct groups, each with clear synergistic value."""
    
    # Format available contexts as numbered list
    formatted_contexts = "\n".join([
        f"{i+1}. Hook: {ctx.hook}\n   Template: {ctx.template}\n   Explanation: {ctx.explanation}"
        for i, ctx in enumerate(first_order_triplets)
    ])
    
    # Retry logic
    for attempt in range(retries + 1):
        try:
            # Make LLM call
            result = predictor(
                task_description=task_description,
                topic=formatted_topics,
                available_contexts=first_order_triplets  # Pass the actual list of FirstOrderTriplet objects
            )
            
            # Validate result
            if hasattr(result, 'list_of_groups') and result.list_of_groups:
                print(f"Generated {len(result.list_of_groups)} higher-order groups")
                return result.list_of_groups  # Return List[HigherOrderGroup] directly
            else:
                raise ValueError("No valid higher-order groups in LLM response")
                
        except Exception as e:
            if attempt < retries:
                print(f"Attempt {attempt + 1} failed: {str(e)[:100]}... Retrying in 2s")
                await asyncio.sleep(2)
            else:
                raise Exception(f"Failed to generate higher-order groups after {retries + 1} attempts: {str(e)}")
    
    return []