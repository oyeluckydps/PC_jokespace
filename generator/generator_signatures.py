"""DSPy signatures for structured LLM outputs in joke generation"""

import dspy
from typing import List
from generator.generator_models import HookTemplateOutput

class HookTemplateGenerationSignature(dspy.Signature):
    """Generate hook-template pairs with comprehensive explanations for joke creation"""
    
    task_description = dspy.InputField(
        desc="Detailed instructions for generating diverse hook-template pairs that will serve as creative foundations for joke generation, including requirements for variety, comedic potential, and comprehensive explanations"
    )
    topic = dspy.InputField(
        desc="The specific topic(s) for joke generation in natural language."
    )
    hook_template_pairs: List[HookTemplateOutput] = dspy.OutputField(
        desc="List of more than 1 hook-template pairs, each containing a comedic hook, compatible joke template, and detailed explanation of their synergistic humor potential",
        min_items=1  # Ensures non-empty list with minimum items
    )

class HigherOrderGroupingSignature(dspy.Signature):
    """Create synergistic groups from hook-template pairs"""
    topic_description = dspy.InputField(desc="Formatted description of topics for joke generation")
    available_contexts = dspy.InputField(desc="All available hook-template-context combinations")
    higher_order_groups = dspy.OutputField(desc="List of synergistic groups with 2+ hook-template pairs each - create at least one group")

class JokeGenerationSignature(dspy.Signature):
    """Generate jokes from context guidance"""
    topic_description = dspy.InputField(desc="Formatted description of topics for joke generation")
    context_guidance = dspy.InputField(desc="Flattened context guidance from either hook-template-context or higher-order group")
    generated_jokes = dspy.OutputField(desc="One or more original, novel jokes based on inspiration from context")

    