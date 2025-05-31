"""Data models for joke generator - includes Pydantic models for DSPy outputs"""

from pydantic import BaseModel, Field
from typing import List

# Pydantic models for DSPy structured outputs
class HookTemplateOutput(BaseModel):
    """A single hook-template pair with comedic generation explanation"""
    hook: str = Field(description="A comedic anchor or connection point related to the topic - wordplay, concept, cultural reference, or semantic relationship")
    template: str = Field(description="A joke structure format that amplifies the hook's humor potential - classic formats, setup-punchline structures, or narrative patterns")
    explanation: str = Field(description="Comprehensive strategy explaining how this hook-template combination generates multiple funny jokes, what comedic techniques it enables, and why it's effective")

class HookTemplateContext:
    """Single hook-template pair with detailed generator explanation"""
    def __init__(self, hook: str, template: str, explanation: str):
        self.hook = hook
        self.template = template
        self.explanation = explanation
    
    def __repr__(self):
        return f"HookTemplateContext(hook='{self.hook[:30]}...', template='{self.template[:30]}...')"

class GenerationContext:
    """Base class for unified processing after flattening"""
    def __init__(self, context_type: str, details: str, explanation: str):
        self.context_type = context_type  # 'first_order' or 'higher_order'
        self.details = details
        self.explanation = explanation

class FirstOrderContext(GenerationContext):
    """Subclass for single hook-template pairs"""
    def __init__(self, hook_template_context: HookTemplateContext):
        details = f"Hook: {hook_template_context.hook}\nTemplate: {hook_template_context.template}"
        super().__init__('first_order', details, hook_template_context.explanation)
        self.original_context = hook_template_context

class HigherOrderGroup:
    """Collection of 2+ hook-template-context combinations with unified group explanation"""
    def __init__(self, hook_template_contexts: list, group_explanation: str):
        self.hook_template_contexts = hook_template_contexts
        self.group_explanation = group_explanation
    
    def __repr__(self):
        return f"HigherOrderGroup(contexts={len(self.hook_template_contexts)}, explanation='{self.group_explanation[:50]}...')"

class HigherOrderContext(GenerationContext):
    """Subclass for higher-order groups"""
    def __init__(self, higher_order_group: HigherOrderGroup):
        details = "\n\n".join([
            f"Hook-Template Pair {i+1}:\nHook: {ctx.hook}\nTemplate: {ctx.template}"
            for i, ctx in enumerate(higher_order_group.hook_template_contexts)
        ])
        super().__init__('higher_order', details, higher_order_group.group_explanation)
        self.original_group = higher_order_group

class GeneratedJoke:
    """Individual joke with simple integer ID"""
    def __init__(self, text: str, joke_id: int = None):
        self.text = text
        self.id = joke_id  # Will be assigned later
    
    def __repr__(self):
        return f"GeneratedJoke(id={self.id}, text='{self.text[:50]}...')"

class JokePortfolio:
    """Complete collection of all generated jokes"""
    def __init__(self):
        self.jokes = []
    
    def add_joke(self, joke: GeneratedJoke):
        self.jokes.append(joke)
    
    def add_jokes(self, jokes: list):
        self.jokes.extend(jokes)
    
    def get_joke_by_id(self, joke_id: int) -> GeneratedJoke:
        for joke in self.jokes:
            if joke.id == joke_id:
                return joke
        return None
    
    def __len__(self):
        return len(self.jokes)
    
    def __repr__(self):
        return f"JokePortfolio(total_jokes={len(self.jokes)})"

    