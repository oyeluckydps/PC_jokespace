import os
import time
import dspy
from typing import Optional, Any
from anthropic import Anthropic
import random

# Import OpenRouter clients from utilities
try:
    from utilities.openrouter import OpenRouterClient, OpenRouterClientV2
    OPENROUTER_AVAILABLE = True
except ImportError:
    print("Warning: OpenRouter utilities not found. Fallback will not be available.")
    OPENROUTER_AVAILABLE = False


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
        self.fallback_client = None
        self.client_type = "claude"  # Track which client is being used
        
        # Try to configure DSPy with Claude first
        success = self._try_claude_configuration()
        
        if not success and OPENROUTER_AVAILABLE:
            print("\033[93mClaude configuration failed. Attempting OpenRouter fallback...\033[0m")
            success = self._try_openrouter_fallback()
            
        if not success:
            raise Exception("Failed to initialize any language model client (Claude or OpenRouter)")
    
    def _try_claude_configuration(self) -> bool:
        """Try to configure DSPy with Claude"""
        try:
            # Configure DSPy with Claude
            self.lm = dspy.LM(
                model=self.model,
                api_key=self.api_key,
                max_tokens=4000,
                cache=self.cache,
                temperature=0.1 + (0 if self.cache else 1)*0.001*random.uniform(-1, 1)        # The cache of DSPy is not functioning well so add some randomness to bypass the cache.
            )
            dspy.settings.configure(lm=self.lm, cache=self.cache)
            
            # Test the configuration with a simple call
            test_response = self.lm("Test", max_tokens=5)
            if test_response:
                print("\033[92mClaude configuration successful!\033[0m")
                self.client_type = "claude"
                return True
            else:
                print("\033[91mClaude configuration test failed - no response\033[0m")
                return False
                
        except Exception as e:
            print(f"\033[91mClaude configuration failed: {str(e)}\033[0m")
            return False
    
    def _try_openrouter_fallback(self) -> bool:
        """Try to fallback to OpenRouter clients"""
        if not OPENROUTER_AVAILABLE:
            print("\033[91mOpenRouter utilities not available\033[0m")
            return False
        
        # Check if OpenRouter API key is available
        openrouter_key_available = self._check_openrouter_key()
        if not openrouter_key_available:
            print("\033[91mOpenRouter API key not found. Please create '../secret/LLAMA_API_KEY.txt' or set OPENROUTER_API_KEY environment variable\033[0m")
            print("\033[93mNote: Even free OpenRouter models require an API key (sign up at https://openrouter.ai)\033[0m")
            return False
            
        # Try OpenRouterClient first
        try:
            print("\033[93mTrying OpenRouterClient...\033[0m")
            self.fallback_client = OpenRouterClient(
                model="meta-llama/llama-3.1-8b-instruct:free",  # Use free model for fallback
                cache=self.cache
            )
            
            # Test the fallback client
            test_response = self.fallback_client.generate("Test", max_tokens=5)
            if test_response:
                print("\033[92mOpenRouterClient fallback successful!\033[0m")
                self.client_type = "openrouter_v1"
                return True
            else:
                print("\033[91mOpenRouterClient test failed - no response\033[0m")
                
        except Exception as e:
            print(f"\033[91mOpenRouterClient fallback failed: {str(e)}\033[0m")
        
        # Try OpenRouterClientV2 as last resort
        try:
            print("\033[93mTrying OpenRouterClientV2...\033[0m")
            self.fallback_client = OpenRouterClientV2(
                model="meta-llama/llama-3.1-8b-instruct:free",
                cache=self.cache
            )
            
            # Test the fallback client
            test_response = self.fallback_client.generate("Test", max_tokens=5)
            if test_response:
                print("\033[92mOpenRouterClientV2 fallback successful!\033[0m")
                self.client_type = "openrouter_v2"
                return True
            else:
                print("\033[91mOpenRouterClientV2 test failed - no response\033[0m")
                
        except Exception as e:
            print(f"\033[91mOpenRouterClientV2 fallback failed: {str(e)}\033[0m")
        
        return False
    
    def generate(self, prompt: str, max_tokens: int = 2000, temperature: float = 0.1) -> Optional[str]:
        """Generate response with retry logic"""
        for attempt in range(self.max_retries):
            try:
                if self.client_type == "claude":
                    # Use Claude directly
                    with dspy.settings.context(temperature=temperature):
                        response = self.lm(prompt, max_tokens=max_tokens)
                        return response
                else:
                    # Use fallback client
                    response = self.fallback_client.generate(prompt, max_tokens=max_tokens, temperature=temperature)
                    return response
                    
            except Exception as e:
                error_msg = f"API Call Failed (Attempt {attempt + 1}/{self.max_retries}) [{self.client_type}]: {str(e)}"
                print(f"\033[91m{error_msg}\033[0m")  # Print in RED
                
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay)
                else:
                    # If Claude fails completely, try to switch to fallback on final attempt
                    if self.client_type == "claude" and OPENROUTER_AVAILABLE and not self.fallback_client:
                        print("\033[93mClaude completely failed. Attempting emergency OpenRouter switch...\033[0m")
                        if self._try_openrouter_fallback():
                            return self.generate(prompt, max_tokens, temperature)
                    
                    raise Exception(f"Failed after {self.max_retries} attempts with {self.client_type}: {str(e)}")
        
        return None
    
    def get_client_info(self) -> dict:
        """Get information about the currently active client"""
        info = {
            "client_type": self.client_type,
            "model": self.model if self.client_type == "claude" else getattr(self.fallback_client, 'model', 'unknown'),
            "cache": self.cache,
            "max_retries": self.max_retries,
            "retry_delay": self.retry_delay
        }
        
        if self.client_type != "claude" and self.fallback_client:
            info["fallback_model"] = getattr(self.fallback_client, 'model', 'unknown')
            
        return info
    
    def _check_openrouter_key(self) -> bool:
        """Check if OpenRouter API key is available"""
        try:
            # Try to read from file first
            with open("./secret/LLAMA_API_KEY.txt", "r") as f:
                key = f.read().strip()
                if key:
                    return True
        except (FileNotFoundError, Exception):
            print("\033[91mOpenRouter API key not found. -AKV\033[0m")
            
        # Check environment variable
        key = os.environ.get('OPENROUTER_API_KEY')
        return bool(key)
    
    def switch_to_fallback(self, force: bool = False) -> bool:
        """Manually switch to OpenRouter fallback"""
        if not OPENROUTER_AVAILABLE:
            print("\033[91mOpenRouter utilities not available for fallback\033[0m")
            return False
        
        if not self._check_openrouter_key():
            print("\033[91mOpenRouter API key not found. Cannot switch to fallback.\033[0m")
            print("\033[93mGet a free API key at: https://openrouter.ai\033[0m")
            return False
            
        if self.client_type != "claude" and not force:
            print("\033[93mAlready using fallback client\033[0m")
            return True
            
        return self._try_openrouter_fallback()
    
    def switch_to_claude(self) -> bool:
        """Manually switch back to Claude (if possible)"""
        if self.client_type == "claude":
            print("\033[93mAlready using Claude client\033[0m")
            return True
            
        success = self._try_claude_configuration()
        if success:
            self.fallback_client = None  # Clear fallback client
        return success
    
    def _get_api_key(self) -> str:
        """Retrieve API key from environment variable"""
        api_key = os.environ.get('ANTHROPIC_API_KEY')
        # if not api_key:
        #     raise ValueError("ANTHROPIC_API_KEY not found in environment variables")
        return api_key


# Example usage and testing
if __name__ == "__main__":
    print("=== Testing ClaudeClient with Fallback ===")
    
    try:
        # Initialize client (will try Claude first, then fallback if needed)
        client = ClaudeClient(cache=True)
        
        # Show client info
        info = client.get_client_info()
        print(f"\nClient Info: {info}")
        
        # Test generation
        print(f"\nTesting generation with {info['client_type']}...")
        response = client.generate("What is the capital of France?", max_tokens=100)
        print(f"Response: {response}")
        
        # Test with DSPy modules
        print(f"\nTesting DSPy modules with {info['client_type']}...")
        qa = dspy.Predict("question -> answer")
        result = qa(question="What is 2+2?")
        print(f"DSPy result: {result.answer}")
        
        # Test manual switching (if fallback is available)
        if OPENROUTER_AVAILABLE and client.client_type == "claude":
            print(f"\nTesting manual switch to fallback...")
            if client.switch_to_fallback():
                info = client.get_client_info()
                print(f"Switched to: {info['client_type']}")
                
                response = client.generate("Name three colors.", max_tokens=50)
                print(f"Fallback response: {response}")
                
                # Try to switch back
                print(f"\nTesting switch back to Claude...")
                if client.switch_to_claude():
                    info = client.get_client_info()
                    print(f"Switched back to: {info['client_type']}")
        
    except Exception as e:
        print(f"\033[91mError during testing: {e}\033[0m")
    
    print("\n=== Testing Complete ===")

