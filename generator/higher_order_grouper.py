"""Create higher-order groups from hook-template contexts"""

import asyncio
import dspy
from typing import List
from utilities.dspy_client import ClaudeClient
from utilities.generator_utils import format_topic_set_for_prompt
from generator.generator_models import HookTemplateContext, HigherOrderGroup
from generator.generator_signatures import HigherOrderGroupingSignature


async def create_higher_order_groups(topic_set: set, hook_template_contexts: List[HookTemplateContext], 
                                   client: ClaudeClient, retries: int = 3) -> List[HigherOrderGroup]:
    """Create synergistic groups of hook-template pairs"""
    
    # Format inputs
    formatted_topics = format_topic_set_for_prompt(topic_set)
    
    # Format contexts for LLM
    contexts_description = "\n\n".join([
        f"Context {i+1}:\nHook: {ctx.hook}\nTemplate: {ctx.template}\nExplanation: {ctx.explanation}"
        for i, ctx in enumerate(hook_template_contexts)
    ])
    
    # Initialize DSPy predictor
    predictor = dspy.Predict(HigherOrderGroupingSignature)
    
    # Retry logic
    for attempt in range(retries + 1):
        try:
            # Make LLM call
            result = predictor(
                topic_description=formatted_topics,
                available_contexts=f"""Given {formatted_topics}

                And these hook-template-context combinations:
                {contexts_description}

                Create higher-order groups by combining multiple hook-template pairs that can work together synergistically to create sophisticated, multi-layered jokes.

                GROUP CREATION CRITERIA:
                - Combine 2-4 hook-template pairs that complement each other comedically
                - Look for combinations that enable layered humor, complex wordplay, or conceptual connections
                - Identify pairs that can be woven together in single jokes or joke sequences
                - Focus on combinations that create MORE humor potential together than separately
                - Only create groups where the combination genuinely enhances comedic possibilities

                For each group, provide:
                1. SELECTED HOOK-TEMPLATE PAIRS: The specific combinations you're grouping (reference by Context number)
                2. GROUP GENERATOR EXPLANATION: Comprehensive strategy covering:
                - How these hooks can be connected, contrasted, or sequenced to create very funny jokes
                - How the templates can be combined, modified, or linked
                - What sophisticated humor strategies become possible with this group
                - Specific approaches for creating complex, layered jokes using this group

                Treat each group of selected hook-templates as a single unified element for joke generation purposes.

                REQUIREMENTS:
                - CREATE AT LEAST ONE GROUP (this is mandatory)
                - You may create additional groups if you see genuine synergistic opportunities
                - Prioritize quality of synergy over quantity of groups
                - Only group elements that truly work better together

                Output format should be structured list of higher-order group objects."""
            )
            
            # Parse structured output
            groups = []
            if hasattr(result, 'higher_order_groups') and result.higher_order_groups:
                for group_item in result.higher_order_groups:
                    if hasattr(group_item, 'selected_contexts') and hasattr(group_item, 'group_explanation'):
                        # Extract context indices
                        selected_contexts = []
                        for idx in group_item.selected_contexts:
                            if isinstance(idx, int) and 0 <= idx < len(hook_template_contexts):
                                selected_contexts.append(hook_template_contexts[idx])
                        
                        if len(selected_contexts) >= 2:  # Ensure at least 2 contexts
                            groups.append(HigherOrderGroup(
                                hook_template_contexts=selected_contexts,
                                group_explanation=group_item.group_explanation
                            ))
            
            if groups:
                print(f"Created {len(groups)} higher-order groups")
                return groups
            else:
                # Create at least one group as required
                print("No valid groups from LLM, creating default group")
                if len(hook_template_contexts) >= 2:
                    return [HigherOrderGroup(
                        hook_template_contexts=hook_template_contexts[:2],
                        group_explanation="These contexts can work together to create layered humor through contrasting perspectives and wordplay combinations."
                    )]
                
        except Exception as e:
            if attempt < retries:
                print(f"Attempt {attempt + 1} failed: {str(e)[:100]}... Retrying in 2s")
                await asyncio.sleep(2)
            else:
                # On final failure, create mandatory group
                if len(hook_template_contexts) >= 2:
                    print(f"Creating default group after failures: {str(e)}")
                    return [HigherOrderGroup(
                        hook_template_contexts=hook_template_contexts[:2],
                        group_explanation="Default synergistic group for multi-layered joke creation."
                    )]
    
    return []

