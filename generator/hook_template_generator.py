"""Generate hook-template pairs with explanatory contexts using DSPy"""

import asyncio
import dspy
from typing import List, Set
from generator.models import FirstOrderTriplet
from generator.signatures import HookTemplateGenerationSignature
from utilities.dspy_client import ClaudeClient
from utilities.generator_utils import format_topic_set_for_prompt


def get_num_of_jokes(jokespace_size: str) -> str:
    """Get number of jokes based on jokespace size"""
    if jokespace_size == 'small':
        return "1 to 5"
    elif jokespace_size == 'medium':
        return "5 to 10"
    elif jokespace_size == 'large':
        return "10 or more"
    else:
        raise ValueError(f"Invalid jokespace size: {jokespace_size}")


async def generate_hook_template_contexts(topic_set: set, client: ClaudeClient, retries: int = 3, jokespace_size: str = 'medium') -> List[FirstOrderTriplet]:
    """Generate hook-template-explanation triplets"""
    
    # Get number of jokes based on jokespace size
    num_of_jokes = get_num_of_jokes(jokespace_size)
    
    # Format topics for prompt
    formatted_topics = format_topic_set_for_prompt(topic_set)
    
    # Initialize DSPy predictor
    predictor = dspy.Predict(HookTemplateGenerationSignature)
    
    # Detailed task description
    task_description = f"""Generate {num_of_jokes} diverse hook-template-explanation triplets for joke creation following these guidelines:

                        1. HOOK POINT Creation:
                        - Identify comedic anchors directly related to the given topic(s)
                        - Include various types of hook points: wordplay/puns, conceptual connections, cultural references, semantic relationships
                        - Each hook should offer a unique angle or perspective on the topic
                        - Ensure hooks have strong comedic potential

                        2. JOKE TEMPLATE Selection:
                        - Match each hook with a compatible joke structure
                        - Use diverse formats: "Why did...", "What do you call...", setup-punchline, comparison formats, narrative structures
                        - Templates should amplify the hook's humor potential
                        - Avoid repetitive template types

                        3. EXPLANATION Requirements:
                        - Explain WHY this hook-template combination is effective
                        - Describe MULTIPLE ways to generate different jokes from this pair
                        - Detail specific comedic techniques enabled (misdirection, wordplay, absurdity, etc.)
                        - Show how hook and template complement each other
                        - You many include concrete joke generation strategies

                        Focus on combinations that offer clear paths to creating the funniest joke.
                        """
    
    # Retry logic
    for attempt in range(retries + 1):
        try:
            # Make LLM call with Pydantic model
            result = predictor(
                task_description=task_description,
                topic=formatted_topics
            )
            
            # DSPy handles Pydantic validation automatically
            if hasattr(result, 'hook_template_context_list') and result.hook_template_context_list:
                print(f"Generated {len(result.hook_template_context_list)} hook-template-explanation triplets")
                return result.hook_template_context_list  # Return FirstOrderTriplet objects directly
            else:
                raise ValueError("No valid hook-template-explanation triplets in LLM response")
                
        except Exception as e:
            if attempt < retries:
                print(f"Attempt {attempt + 1} failed: {str(e)[:100]}... Retrying in 2s")
                await asyncio.sleep(2)
            else:
                raise Exception(f"Failed to generate hook-template-explanation triplets after {retries + 1} attempts: {str(e)}")
    
    return []