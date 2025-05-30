import os
import time
import dspy
from typing import Optional, Any
from anthropic import Anthropic
import random

class ClaudeClient:
    def __init__(self, model: str = '', api_key: Optional[str] = None, 
                 cache: bool = True):
        """Initialize DSPy with Claude 3.5 Sonnet using environment API key"""
        # model_default = "claude-3-5-sonnet-20241022" # Input -> $3.00 / MTok       Output ->$15.00 / MTok
        model_default = "claude-3-haiku-20240307"    # Input -> $0.25 / MTok       Output -> $1.25 / MTok
        # model_default = "claude-3-5-haiku-20241022"  # Input -> $0.80 / MTok       Output -> $4.00 / MTok
        # Claude 3 Haiku: 4,096 output tokens max
        # Claude 3 Sonnet: 8,192 output tokens max
        # Claude 3 Opus: 8,192 output tokens max
        # Claude 3.5 Sonnet: 8,192 output tokens max
        # Claude 3.5 Haiku: 8,192 output tokens max

        self.model = model if model else model_default
        self.api_key = api_key or self._get_api_key()
        self.cache = cache
        self.max_retries = 10
        self.retry_delay = 5
        
        # Configure DSPy with Claude
        self.lm = dspy.LM(
            model=self.model,
            api_key=self.api_key,
            max_tokens=4000,
            cache=self.cache,
            temperature=0.1 + (0 if self.cache else 1)*0.001*random.uniform(-1, 1)        # The cache of DSPy is not functioning well so add some randomness to bypass the cache.
        )
        dspy.settings.configure(lm=self.lm, cache=self.cache)
        pass
    
    def generate(self, prompt: str, max_tokens: int = 2000, temperature: float = 0.1) -> Optional[str]:
        """Generate response with retry logic"""
        for attempt in range(self.max_retries):
            try:
                # Update temperature for this specific generation
                with dspy.settings.context(temperature=temperature):
                    response = self.lm(prompt, max_tokens=max_tokens)
                    return response
            except Exception as e:
                error_msg = f"API Call Failed (Attempt {attempt + 1}/{self.max_retries}): {str(e)}"
                print(f"\033[91m{error_msg}\033[0m")  # Print in RED
                
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay)
                else:
                    raise Exception(f"Failed after {self.max_retries} attempts: {str(e)}")
        
        return None
    
    def _get_api_key(self) -> str:
        """Retrieve API key from environment variable"""
        api_key = os.environ.get('ANTHROPIC_API_KEY')
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY not found in environment variables")
        return api_key