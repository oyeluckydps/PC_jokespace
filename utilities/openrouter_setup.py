from openai import OpenAI

# Read API key from secret/openrouter.txt
api_key = None
try:
    with open("../secret/openrouter.txt", "r") as f:
        api_key = f.read().strip()
except FileNotFoundError:
    print("Error: secret/openrouter.txt not found. Please create it with your API key.")
    exit(1)
except Exception as e:
    print(f"Error reading API key: {e}")
    exit(1)

if not api_key:
    print("Error: API key is empty in secret/openrouter.txt.")
    exit(1)

client = OpenAI(
  base_url="https://openrouter.ai/api/v1",
  api_key=api_key,
)

completion = client.chat.completions.create(
  extra_headers={
    "HTTP-Referer": "<YOUR_SITE_URL>", # Optional. Site URL for rankings on openrouter.ai.
    "X-Title": "<YOUR_SITE_NAME>", # Optional. Site title for rankings on openrouter.ai.
  },
  extra_body={},
  model="google/gemini-2.5-pro-preview",
  messages=[
    {
      "role": "user",
      "content": [
        {
          "type": "text",
          "text": "What is in this image?"
        },
        {
          "type": "image_url",
          "image_url": {
            "url": "https://upload.wikimedia.org/wikipedia/commons/thumb/d/dd/Gfp-wisconsin-madison-the-nature-boardwalk.jpg/2560px-Gfp-wisconsin-madison-the-nature-boardwalk.jpg"
          }
        }
      ]
    }
  ],
  max_tokens=4000
)
print(completion.choices[0].message.content)