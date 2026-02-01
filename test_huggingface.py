import os
from dotenv import load_dotenv
from huggingface_hub import InferenceClient

load_dotenv()

# Test without API key first
print("Testing HuggingFace Inference API...")
print("=" * 50)

try:
    client = InferenceClient()
    
    completion = client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=[
            {
                "role": "user",
                "content": "How many 'G's in 'huggingface'?"
            }
        ],
    )
    
    print("Success! Response:")
    print(completion.choices[0].message)
    print("=" * 50)
    print("No API key needed for this model!")
    
except Exception as e:
    print(f"Error: {e}")
    print("=" * 50)
    print("\nTesting with HF_TOKEN from environment...")
    
    # Try with API key if available
    hf_token = os.getenv("HF_TOKEN")
    if hf_token:
        try:
            client = InferenceClient(token=hf_token)
            completion = client.chat.completions.create(
                model="openai/gpt-oss-120b",
                messages=[
                    {
                        "role": "user",
                        "content": "How many 'G's in 'huggingface'?"
                    }
                ],
            )
            print("Success with API key!")
            print(completion.choices[0].message)
        except Exception as e2:
            print(f"Still failed: {e2}")
    else:
        print("No HF_TOKEN in environment")
        print("Get free token at: https://huggingface.co/settings/tokens")
