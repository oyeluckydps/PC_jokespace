"""DSPy signatures for structured LLM outputs in joke generation"""

import dspy
from typing import List, Union
from generator.models import FirstOrderTriplet, HigherOrderGroup, JokeOutput # Updated import

class HookTemplateGenerationSignature(dspy.Signature):
    """Generate hook-template pairs with comprehensive explanations for joke creation"""
    
    task_description = dspy.InputField(
        desc="Detailed instructions for generating diverse hook-template pairs that will serve as creative foundations for joke generation, including requirements for variety, comedic potential, and comprehensive explanations"
    )
    
    topic = dspy.InputField(
        desc="The specific topic(s) for joke generation in natural language."
    )
    
    hook_template_context_list: List[FirstOrderTriplet] = dspy.OutputField(
        desc="List of more than 1 hook-template-explanation triplets, each containing a comedic hook, compatible joke template, and detailed explanation of their synergistic humor potential",
        min_items=1  # Ensures non-empty list with minimum items
    )

class HigherOrderGroupingSignature(dspy.Signature):
    """Create synergistic groups from hook-template pairs"""
    
    task_description = dspy.InputField(
        desc="Instructions for identifying and grouping hook-template pairs that work together synergistically"
    )
    
    topic = dspy.InputField(
        desc="The specific topic(s) for joke generation in natural language"
    )
    
    available_contexts: List[FirstOrderTriplet] = dspy.InputField(
        desc="List of FirstOrderTriplet objects available for grouping, formatted as numbered list"
    )
    
    list_of_groups: List[HigherOrderGroup] = dspy.OutputField(
        desc="List of higher-order groups, each containing 2+ hook-template pairs with explanation of their synergistic potential",
        min_items=1
    )

class JokeGenerationSignature(dspy.Signature):
    """Generate jokes from context guidance"""
    
    task_description = dspy.InputField(
        desc="Detailed instructions for generating original, funny jokes using provided context as inspiration"
    )
    
    topic = dspy.InputField(
        desc="The specific topic(s) for joke generation in natural language"
    )
    
    context_guidance: Union[FirstOrderTriplet, HigherOrderGroup] = dspy.InputField(
        desc="Context guidance that can either be a FirstOrderTriplet or a HigherOrderGroup providing inspiration for joke generation"
    )
    
    generated_jokes: List[JokeOutput] = dspy.OutputField(
        desc="One or more original, novel jokes based on inspiration from context",
        min_items=1
    ) 