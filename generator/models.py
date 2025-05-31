"""Data models for joke generator - includes Pydantic models for DSPy outputs"""

from pydantic import BaseModel, Field
from typing import List

# Basic building block for hook-template pairs
class HookTemplatePair(BaseModel):
    """A basic hook-template pair without explanation"""
    hook: str = Field(description="A comedic anchor or connection point related to the topic")
    template: str = Field(description="A joke structure format that amplifies the hook's humor potential")

# First-order structure with explanation
class FirstOrderTriplet(BaseModel):
    """A single hook-template pair with comedic generation explanation"""
    hook: str = Field(description="A comedic anchor or connection point related to the topic - wordplay, concept, cultural reference, or semantic relationship")
    template: str = Field(description="A joke structure format that amplifies the hook's humor potential - classic formats, setup-punchline structures, or narrative patterns")
    explanation: str = Field(description="Comprehensive strategy explaining how this hook-template combination generates multiple funny jokes, what comedic techniques it enables, and why it's effective")
    
    def __repr__(self):
        return f"FirstOrderTriplet(hook='{self.hook[:30]}...', template='{self.template[:30]}...')"

# Higher-order group structure
class HigherOrderGroup(BaseModel):
    """A group of 2+ hook-template pairs that work together synergistically"""
    hook_template_pairs: List[HookTemplatePair] = Field(
        description="List of hook-template pairs that work together synergistically",
        min_items=2
    )
    context_explanation: str = Field(
        description="Comprehensive strategy for how these hooks and templates work together to create sophisticated multi-layered jokes"
    )
    
    def __repr__(self):
        return f"HigherOrderGroup(pairs={len(self.hook_template_pairs)}, explanation='{self.context_explanation[:50]}...')"

# Joke generation output
class JokeOutput(BaseModel):
    """A single generated joke"""
    text: str = Field(description="The complete joke text, ready for presentation")

# Non-Pydantic classes for joke storage
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