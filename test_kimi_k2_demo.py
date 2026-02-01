# Demonstration of Kimi K2.5 API Usage (Code Examples - No Live API Calls)
# This shows all the patterns without requiring a funded account

import os
from dotenv import load_dotenv

load_dotenv()

# ============================================================================
# Example 1: Basic Chat Completion
# ============================================================================
def demo_basic_chat():
    """Demo code for basic chat completion with Kimi K2.5"""
    
    code = """
from openai import OpenAI

client = OpenAI(
    api_key="your_kimi_api_key",
    base_url="https://api.moonshot.ai/v1"
)

completion = client.chat.completions.create(
    model="kimi-k2.5",
    messages=[
        {
            "role": "system",
            "content": "You are Kimi, an AI assistant provided by Moonshot AI."
        },
        {
            "role": "user",
            "content": "What is 2+2?"
        }
    ],
    temperature=0.6,
    max_tokens=256
)

print(completion.choices[0].message.content)
"""
    print("=" * 70)
    print("Example 1: Basic Chat Completion")
    print("=" * 70)
    print(code)


# ============================================================================
# Example 2: Thinking Mode (Extended Reasoning)
# ============================================================================
def demo_thinking_mode():
    """Demo code for thinking mode"""
    
    code = """
from openai import OpenAI

client = OpenAI(
    api_key="your_kimi_api_key",
    base_url="https://api.moonshot.ai/v1"
)

# Thinking mode enables extended reasoning (temperature=1.0)
completion = client.chat.completions.create(
    model="kimi-k2.5",
    messages=[
        {
            "role": "user",
            "content": "Solve this complex problem: If a train travels at 60 mph..."
        }
    ],
    temperature=1.0,  # Required for thinking mode
    max_tokens=2048,
    thinking={
        "type": "enabled"  # Enable thinking
    }
)

response = completion.choices[0].message

# Access reasoning content if available
if hasattr(response, 'reasoning_content'):
    print("Thinking Process:", response.reasoning_content)
    
print("Final Answer:", response.content)
"""
    print("\n" + "=" * 70)
    print("Example 2: Thinking Mode (Extended Reasoning)")
    print("=" * 70)
    print(code)


# ============================================================================
# Example 3: Instant Mode (Fast Response)
# ============================================================================
def demo_instant_mode():
    """Demo code for instant mode"""
    
    code = """
from openai import OpenAI

client = OpenAI(
    api_key="your_kimi_api_key",
    base_url="https://api.moonshot.ai/v1"
)

# Instant mode for faster responses (temperature=0.6)
completion = client.chat.completions.create(
    model="kimi-k2.5",
    messages=[
        {
            "role": "user",
            "content": "Generate a product name for an AI-powered coffee maker"
        }
    ],
    temperature=0.6,  # Required for instant mode
    max_tokens=256,
    thinking={
        "type": "disabled"  # Disable thinking for instant mode
    }
)

print(completion.choices[0].message.content)
"""
    print("\n" + "=" * 70)
    print("Example 3: Instant Mode (Fast Response)")
    print("=" * 70)
    print(code)


# ============================================================================
# Example 4: Streaming Response
# ============================================================================
def demo_streaming():
    """Demo code for streaming response"""
    
    code = """
from openai import OpenAI

client = OpenAI(
    api_key="your_kimi_api_key",
    base_url="https://api.moonshot.ai/v1"
)

# Enable streaming for real-time output
stream = client.chat.completions.create(
    model="kimi-k2.5",
    messages=[
        {
            "role": "user",
            "content": "Write a poem about Python programming"
        }
    ],
    temperature=0.6,
    max_tokens=512,
    stream=True  # Enable streaming
)

# Process chunks as they arrive
for chunk in stream:
    if chunk.choices[0].delta.content:
        print(chunk.choices[0].delta.content, end="", flush=True)
        
print()  # Newline at end
"""
    print("\n" + "=" * 70)
    print("Example 4: Streaming Response")
    print("=" * 70)
    print(code)


# ============================================================================
# Example 5: Multi-turn Conversation
# ============================================================================
def demo_multi_turn():
    """Demo code for multi-turn conversation"""
    
    code = """
from openai import OpenAI

client = OpenAI(
    api_key="your_kimi_api_key",
    base_url="https://api.moonshot.ai/v1"
)

messages = [
    {
        "role": "system",
        "content": "You are a helpful Python programming assistant."
    }
]

# First turn
messages.append({
    "role": "user",
    "content": "How do I read a file in Python?"
})

completion1 = client.chat.completions.create(
    model="kimi-k2.5",
    messages=messages,
    temperature=0.6
)

assistant_response = completion1.choices[0].message.content
messages.append({
    "role": "assistant",
    "content": assistant_response
})

print("Assistant:", assistant_response)

# Second turn - continue conversation
messages.append({
    "role": "user",
    "content": "Can you show me an example with error handling?"
})

completion2 = client.chat.completions.create(
    model="kimi-k2.5",
    messages=messages,
    temperature=0.6
)

print("Assistant:", completion2.choices[0].message.content)
"""
    print("\n" + "=" * 70)
    print("Example 5: Multi-turn Conversation")
    print("=" * 70)
    print(code)


# ============================================================================
# Example 6: JSON Mode (Structured Output)
# ============================================================================
def demo_json_mode():
    """Demo code for JSON mode"""
    
    code = """
from openai import OpenAI
import json

client = OpenAI(
    api_key="your_kimi_api_key",
    base_url="https://api.moonshot.ai/v1"
)

completion = client.chat.completions.create(
    model="kimi-k2.5",
    messages=[
        {
            "role": "system",
            "content": "You are a JSON API. Return structured data."
        },
        {
            "role": "user",
            "content": "Extract person information from: John Smith is 30 years old from New York"
        }
    ],
    temperature=0.6,
    response_format={
        "type": "json_object"  # Request JSON response
    }
)

# Parse the JSON response
response_json = json.loads(completion.choices[0].message.content)
print(response_json)
"""
    print("\n" + "=" * 70)
    print("Example 6: JSON Mode (Structured Output)")
    print("=" * 70)
    print(code)


# ============================================================================
# Configuration Reference
# ============================================================================
def show_config_reference():
    """Show configuration and parameter reference"""
    
    config = """
╔════════════════════════════════════════════════════════════════════════════╗
║                      KIMI K2.5 CONFIGURATION REFERENCE                    ║
╚════════════════════════════════════════════════════════════════════════════╝

API Endpoint:
  - Base URL: https://api.moonshot.ai/v1
  - Model: "kimi-k2.5"

Key Parameters:

1. temperature
   - Thinking Mode: 1.0 (fixed)
   - Instant Mode: 0.6 (default, safe to use)
   - Range: [0.0 - 2.0]

2. top_p
   - Default: 0.95 (fixed, do not change)

3. max_tokens
   - Default: 32,768 (32k)
   - Max: Depends on context window (256k)

4. thinking
   - type: "enabled" | "disabled"
   - Default: {"type": "enabled"}
   - Enabled: ~2-3x slower, better reasoning
   - Disabled: Instant mode, fast responses

5. context_window
   - Size: 256,144 tokens (256k)
   - Supports long documents, videos, images

6. n (number of completions)
   - Fixed: 1
   - Cannot be changed

7. presence_penalty, frequency_penalty
   - Fixed: 0.0
   - Cannot be changed

Context Window Usage:
  ✓ Text documents
  ✓ Images (base64 encoded)
  ✓ Videos (base64 encoded or file upload)
  ✓ Multi-turn conversations
  ✓ Long context reasoning

Supported Input Types:
  - Text prompts
  - Images (PNG, JPEG, WebP, GIF)
  - Videos (MP4, MOV, AVI, WebM)
  - Base64 encoded media
  - File uploads via API

Pricing:
  - Input: $0.60 per 1M tokens (cache miss)
  - Input: $0.10 per 1M tokens (cache hit)
  - Output: $3.00 per 1M tokens
  - Context: 256,144 tokens (262,144 with padding)

Model Variants:
  - kimi-k2.5: Full model (recommended)
  - kimi-k2-turbo-preview: Faster variant
  - kimi-k2-thinking: Reasoning-focused
"""
    print("\n" + config)


if __name__ == "__main__":
    print("\n")
    print("╔" + "═" * 78 + "╗")
    print("║" + " " * 20 + "KIMI K2.5 API TEST DEMONSTRATIONS" + " " * 24 + "║")
    print("╚" + "═" * 78 + "╝")
    
    # Show all demonstrations
    demo_basic_chat()
    demo_thinking_mode()
    demo_instant_mode()
    demo_streaming()
    demo_multi_turn()
    demo_json_mode()
    show_config_reference()
    
    print("\n" + "=" * 70)
    print("SETUP INSTRUCTIONS")
    print("=" * 70)
    print("""
1. Ensure you have the OpenAI SDK installed:
   pip install openai

2. Add your Kimi API key to .env:
   KIMI_API_KEY=your_actual_api_key_here

3. Make sure your account has sufficient balance at:
   https://platform.moonshot.ai/console/billing

4. To run actual API calls, update your .env with a funded API key

5. For testing with real API, modify test_kimi_k2.py to run individual tests

Documentation: https://platform.moonshot.ai/docs/guide/kimi-k2-5-quickstart
Playground: https://platform.moonshot.ai/playground
    """)
    print("=" * 70)
