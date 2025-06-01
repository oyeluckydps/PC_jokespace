import os
import time
import dspy
from typing import Optional, Any
import random
import requests
import json


class OpenRouterLM(dspy.BaseLM):
    """Custom DSPy Language Model for OpenRouter API"""
    
    def __init__(self, model: str = 'meta-llama/llama-3-70b-instruct', 
                 api_key: Optional[str] = None, 
                 temperature: float = 0.1, 
                 max_tokens: int = 4000,
                 cache: bool = True,
                 **kwargs):
        super().__init__(model=model)
        self.model = model
        self.api_key = api_key or self._get_api_key()
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.cache = cache
        self.api_url = "https://openrouter.ai/api/v1/chat/completions"
        self.kwargs = kwargs
        
    def _get_api_key(self) -> str:
        """Retrieve API key from file or environment variable"""
        # First try to read from file (as shown in your example)
        try:
            with open("./secret/LLAMA_API_KEY.txt", "r") as f:
                api_key = f.read().strip()
                if api_key:
                    return api_key
        except FileNotFoundError:
            pass
        except Exception:
            pass
            
        # Fall back to environment variable
        api_key = os.environ.get('OPENROUTER_API_KEY')
        if not api_key:
            raise ValueError("OpenRouter API key not found. Please create './secret/LLAMA_API_KEY.txt' with your API key or set OPENROUTER_API_KEY environment variable")
        return api_key
    
    def basic_request(self, prompt: str, **kwargs) -> str:
        """Make a basic request to OpenRouter API"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/stanfordnlp/dspy",  # Optional: for OpenRouter analytics
            "X-Title": "DSPy OpenRouter Client"  # Optional: for OpenRouter analytics
        }
        
        # Combine default parameters with call-specific ones
        request_params = {
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            **self.kwargs,
            **kwargs
        }
        
        data = {
            "model": self.model,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            **request_params
        }
        
        try:
            response = requests.post(self.api_url, headers=headers, json=data, timeout=60)
            response.raise_for_status()
            
            response_data = response.json()
            if 'choices' in response_data and len(response_data['choices']) > 0:
                return response_data['choices'][0]['message']['content']
            else:
                raise Exception(f"Invalid response format: {response_data}")
                
        except requests.exceptions.RequestException as e:
            raise Exception(f"OpenRouter API request failed: {str(e)}")
        except json.JSONDecodeError as e:
            raise Exception(f"Failed to parse OpenRouter response: {str(e)}")
    
    def __call__(self, prompt: str = None, messages: list = None, **kwargs) -> list[str]:
        """DSPy-compatible call method"""
        if messages:
            # Convert DSPy messages format to OpenRouter format
            if isinstance(messages, list) and len(messages) > 0:
                if isinstance(messages[0], dict):
                    # Already in correct format
                    formatted_messages = messages
                else:
                    # Convert string messages to proper format
                    formatted_messages = [{"role": "user", "content": str(msg)} for msg in messages]
        else:
            formatted_messages = [{"role": "user", "content": prompt}]
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/stanfordnlp/dspy",
            "X-Title": "DSPy OpenRouter Client"
        }
        
        request_params = {
            "temperature": kwargs.get('temperature', self.temperature),
            "max_tokens": kwargs.get('max_tokens', self.max_tokens),
            **{k: v for k, v in self.kwargs.items() if k not in ['temperature', 'max_tokens']},
            **{k: v for k, v in kwargs.items() if k not in ['messages', 'prompt']}
        }
        
        data = {
            "model": self.model,
            "messages": formatted_messages,
            **request_params
        }
        
        try:
            response = requests.post(self.api_url, headers=headers, json=data, timeout=60)
            response.raise_for_status()
            
            response_data = response.json()
            if 'choices' in response_data and len(response_data['choices']) > 0:
                # Return list of strings as expected by DSPy
                return [choice['message']['content'] for choice in response_data['choices']]
            else:
                raise Exception(f"Invalid response format: {response_data}")
                
        except requests.exceptions.RequestException as e:
            raise Exception(f"OpenRouter API request failed: {str(e)}")
        except json.JSONDecodeError as e:
            raise Exception(f"Failed to parse OpenRouter response: {str(e)}")


class OpenRouterClient:
    """OpenRouter client similar to ClaudeClient for DSPy integration"""
    
    def __init__(self, model: str = '', api_key: Optional[str] = None, 
                 cache: bool = True, **kwargs):
        """Initialize DSPy with OpenRouter using custom or file-based API key"""
        # Popular OpenRouter models with their costs (approximate)
        model_default = "meta-llama/llama-3.1-8b-instruct:free"  # Free model
        # model_default = "meta-llama/llama-3-70b-instruct"      # ~$0.59/$0.79 per MTok
        # model_default = "anthropic/claude-3.5-sonnet"          # $3.00/$15.00 per MTok  
        # model_default = "openai/gpt-4o-mini"                   # $0.15/$0.60 per MTok
        # model_default = "google/gemini-pro-1.5"                # $1.25/$5.00 per MTok
        
        self.model = model if model else model_default
        self.api_key = api_key
        self.cache = cache
        self.max_retries = 10
        self.retry_delay = 5
        
        # Create custom OpenRouter LM
        self.lm = OpenRouterLM(
            model=self.model,
            api_key=self.api_key,
            max_tokens=4000,
            cache=self.cache,
            temperature=0.1 + (0 if self.cache else 1) * 0.001 * random.uniform(-1, 1),
            **kwargs
        )
        
        # Configure DSPy with our custom LM
        dspy.settings.configure(lm=self.lm, cache=self.cache)
    
    def generate(self, prompt: str, max_tokens: int = 2000, temperature: float = 0.1) -> Optional[str]:
        """Generate response with retry logic"""
        for attempt in range(self.max_retries):
            try:
                # Use the basic_request method for simple generation
                response = self.lm.basic_request(
                    prompt=prompt, 
                    max_tokens=max_tokens, 
                    temperature=temperature
                )
                return response
            except Exception as e:
                error_msg = f"API Call Failed (Attempt {attempt + 1}/{self.max_retries}): {str(e)}"
                print(f"\033[91m{error_msg}\033[0m")  # Print in RED
                
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay)
                else:
                    raise Exception(f"Failed after {self.max_retries} attempts: {str(e)}")
        
        return None
    
    def list_models(self) -> list:
        """List available models from OpenRouter (requires API key)"""
        try:
            headers = {
                "Authorization": f"Bearer {self.lm.api_key}",
                "Content-Type": "application/json"
            }
            response = requests.get("https://openrouter.ai/api/v1/models", headers=headers)
            response.raise_for_status()
            return response.json().get('data', [])
        except Exception as e:
            print(f"Failed to fetch models: {e}")
            return []


# Alternative approach using the newer dspy.LM with OpenAI-compatible endpoint
class OpenRouterClientV2:
    """Alternative OpenRouter client using dspy.LM with custom base URL"""
    
    def __init__(self, model: str = '', api_key: Optional[str] = None, 
                 cache: bool = True, **kwargs):
        """Initialize DSPy with OpenRouter using dspy.LM"""
        model_default = "meta-llama/llama-3.1-8b-instruct:free"
        
        self.model = model if model else model_default
        self.api_key = api_key or self._get_api_key()
        self.cache = cache
        self.max_retries = 10
        self.retry_delay = 5
        
        # Note: This approach might work if DSPy supports custom base_url in dspy.LM
        # For now, this is experimental - use OpenRouterClient above for guaranteed compatibility
        try:
            self.lm = dspy.LM(
                model=f"openai/{self.model}",  # Use openai/ prefix for compatibility
                api_key=self.api_key,
                max_tokens=4000,
                cache=self.cache,
                temperature=0.1 + (0 if self.cache else 1) * 0.001 * random.uniform(-1, 1),
                api_base="https://openrouter.ai/api/v1",  # This may or may not be supported
                **kwargs
            )
            dspy.settings.configure(lm=self.lm, cache=self.cache)
        except Exception as e:
            print(f"Warning: dspy.LM approach failed ({e}), falling back to custom implementation")
            # Fall back to the custom implementation
            self.__init__ = OpenRouterClient.__init__
            self.__init__(model, api_key, cache, **kwargs)
    
    def _get_api_key(self) -> str:
        """Retrieve API key from file or environment variable"""
        try:
            with open("./secret/LLAMA_API_KEY.txt", "r") as f:
                api_key = f.read().strip()
                if api_key:
                    return api_key
        except (FileNotFoundError, Exception):
            pass
            
        api_key = os.environ.get('OPENROUTER_API_KEY')
        if not api_key:
            raise ValueError("OpenRouter API key not found")
        return api_key
    
    def generate(self, prompt: str, max_tokens: int = 2000, temperature: float = 0.1) -> Optional[str]:
        """Generate response with retry logic"""
        for attempt in range(self.max_retries):
            try:
                with dspy.settings.context(temperature=temperature):
                    response = self.lm(prompt, max_tokens=max_tokens)
                    return response[0] if isinstance(response, list) else response
            except Exception as e:
                error_msg = f"API Call Failed (Attempt {attempt + 1}/{self.max_retries}): {str(e)}"
                print(f"\033[91m{error_msg}\033[0m")
                
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay)
                else:
                    raise Exception(f"Failed after {self.max_retries} attempts: {str(e)}")
        return None


# Example usage
if __name__ == "__main__":
    # Example 1: Using the custom OpenRouterClient
    print("=== Testing OpenRouterClient ===")
    try:
        client = OpenRouterClient(
            model="meta-llama/llama-3.1-8b-instruct:free",  # Free model for testing
            cache=True
        )
        
        response = client.generate("What is the capital of France?", max_tokens=100)
        print(f"Response: {response}")
        
        # Test with DSPy modules
        qa = dspy.Predict("question -> answer")
        result = qa(question="What is 2+2?")
        print(f"DSPy result: {result.answer}")
        
    except Exception as e:
        print(f"Error: {e}")
    
    # Example 2: Testing the alternative approach
    print("\n=== Testing OpenRouterClientV2 ===")
    try:
        client_v2 = OpenRouterClientV2(
            model="meta-llama/llama-3.1-8b-instruct:free",
            cache=True
        )
        
        response = client_v2.generate("Name three colors.", max_tokens=50)
        print(f"Response: {response}")
        
    except Exception as e:
        print(f"Error: {e}")

