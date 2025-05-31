import vertexai
from vertexai.generative_models import GenerativeModel, GenerationConfig
from google.oauth2 import service_account
import json
import os

def load_credentials_from_file(service_account_path: str):
    """Loads Google Cloud credentials from a service account JSON file."""
    try:
        return service_account.Credentials.from_service_account_file(service_account_path)
    except FileNotFoundError:
        raise FileNotFoundError(f"Service account file not found: {service_account_path}")
    except Exception as e:
        raise RuntimeError(f"Error loading credentials from {service_account_path}: {e}")

def get_project_id_from_file(service_account_path: str) -> str:
    """Extracts the project_id from the service account JSON file."""
    try:
        with open(service_account_path, 'r') as f:
            data = json.load(f)
            project_id = data.get("project_id")
            if not project_id:
                raise ValueError("Key 'project_id' not found in service account file.")
            return project_id
    except FileNotFoundError:
        raise FileNotFoundError(f"Service account file not found: {service_account_path}")
    except (json.JSONDecodeError, ValueError, KeyError) as e:
        raise RuntimeError(f"Error reading project_id from {service_account_path}: {e}")

def generate_text_vertexai(
    project_id: str,
    location: str,
    credentials, # Pass the loaded credentials object
    prompt: str,
    model_name: str = "gemini-1.5-flash", # Default model, can be overridden
    temperature: float = 0.9, # Example generation parameter
    max_output_tokens: int = 256 # Example generation parameter
) -> str:
    """
    Generates text using a Gemini model via the Vertex AI API with explicit credentials.

    Args:
        project_id: The Google Cloud project ID.
        location: The Google Cloud region (e.g., "us-central1").
        credentials: The loaded google.oauth2.service_account.Credentials object.
        prompt: The text prompt for the model.
        model_name: The name of the Gemini model to use (e.g., "gemini-1.5-flash").
        temperature: Controls randomness (0.0-1.0). Higher values are more creative.
        max_output_tokens: Maximum number of tokens in the generated response.

    Returns:
        The generated text from the model. Returns an empty string on errors
        where no candidate is available. Raises exceptions for setup/auth errors.
    """
    print(f"Initializing Vertex AI for project: {project_id}, location: {location}")
    try:
        vertexai.init(project=project_id, location=location, credentials=credentials)

        print(f"Loading model: {model_name}")
        model = GenerativeModel(model_name)

        generation_config = GenerationConfig(
            temperature=temperature,
            max_output_tokens=max_output_tokens
        )

        print(f"Sending prompt: '{prompt[:50]}...'") # Show beginning of prompt
        response = model.generate_content(
            prompt,
            generation_config=generation_config
        )

        print("Response received.")
        # Basic check: Ensure candidates list is not empty and has content
        if response.candidates and response.candidates[0].content.parts:
            return response.candidates[0].content.parts[0].text
        else:
            # Log or handle cases with no valid response (e.g., safety filters)
            print(f"Warning: No valid response candidates found. Response: {response}")

            return ""

    except Exception as e:
        print(f"An error occurred during Vertex AI text generation: {e}")
        # Depending on requirements, you might re-raise, return None, or return ""
        return ""


# --- Main Execution ---
if __name__ == "__main__":
    try:
        # --- Configuration ---
        # IMPORTANT: Replace with the actual path to your service account key file
        # Use environment variables or secure config management in production.
        SERVICE_ACCOUNT_FILE = "../secret/vertex_key.json"
        LOCATION = "us-central1"  # Replace with your desired Google Cloud region
        MODEL_NAME = "gemini-2.5-flash-preview-05-20" # Or "gemini-1.0-pro", etc.
        USER_PROMPT = "Write a short, optimistic paragraph about the future of renewable energy."

        # --- Authentication and Setup ---
        if not os.path.exists(SERVICE_ACCOUNT_FILE):
             raise FileNotFoundError(f"Critical: Service account file not found at {SERVICE_ACCOUNT_FILE}")

        # Load credentials object
        creds = load_credentials_from_file(SERVICE_ACCOUNT_FILE)

        # Extract project ID (can also be passed directly if known)
        proj_id = get_project_id_from_file(SERVICE_ACCOUNT_FILE)

        # --- Generate Text ---
        generated_text = generate_text_vertexai(
            project_id=proj_id,
            location=LOCATION,
            credentials=creds,
            prompt=USER_PROMPT,
            model_name=MODEL_NAME,
            temperature=0.9,
            max_output_tokens=4000
        )

        # --- Output ---
        if generated_text:
            print("\n--- Generated Text ---")
            print(generated_text)
        else:
            print("\nFailed to generate text or received an empty response.")

    except (FileNotFoundError, RuntimeError, Exception) as e:
        print(f"\nAn critical error occurred: {e}")