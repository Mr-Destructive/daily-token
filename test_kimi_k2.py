# Test script for Kimi K2.5 API
# Required: pip install openai
# Required: MOONSHOT_API_KEY in .env file

import os
import sys
from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables from .env
load_dotenv()

def test_basic_chat():
    """Test basic chat completion with Kimi K2.5"""
    api_key = os.getenv("KIMI_API_KEY")
    
    if not api_key:
        print("Error: KIMI_API_KEY not found in .env file")
        print("Please add: KIMI_API_KEY=your_api_key_here")
        sys.exit(1)
    
    client = OpenAI(
        api_key=api_key,
        base_url="https://api.moonshot.ai/v1"
    )
    
    print("Testing Kimi K2.5 Basic Chat...")
    print("-" * 50)
    
    completion = client.chat.completions.create(
        model="kimi-k2.5",
        messages=[
            {
                "role": "system",
                "content": "You are Kimi, an AI assistant provided by Moonshot AI."
            },
            {
                "role": "user",
                "content": "What is 2+2? Please respond concisely."
            }
        ],
        temperature=0.6,
        max_tokens=256
    )
    
    response = completion.choices[0].message.content
    print(f"Response: {response}")
    print("-" * 50)
    return response


def test_thinking_mode():
    """Test Kimi K2.5 with thinking mode enabled"""
    api_key = os.getenv("KIMI_API_KEY")
    
    if not api_key:
        print("Error: KIMI_API_KEY not found in .env file")
        sys.exit(1)
    
    client = OpenAI(
        api_key=api_key,
        base_url="https://api.moonshot.ai/v1"
    )
    
    print("\nTesting Kimi K2.5 with Thinking Mode...")
    print("-" * 50)
    
    completion = client.chat.completions.create(
        model="kimi-k2.5",
        messages=[
            {
                "role": "user",
                "content": "Solve this: If a train travels at 60 mph for 2 hours, how far does it go?"
            }
        ],
        temperature=1.0,
        max_tokens=1024,
        thinking={
            "type": "enabled"
        }
    )
    
    response = completion.choices[0].message
    
    # Thinking mode response includes reasoning_content
    if hasattr(response, 'reasoning_content') and response.reasoning_content:
        print(f"Thinking Process: {response.reasoning_content}")
        print()
    
    print(f"Final Answer: {response.content}")
    print("-" * 50)
    return response.content


def test_instant_mode():
    """Test Kimi K2.5 in instant (non-thinking) mode"""
    api_key = os.getenv("KIMI_API_KEY")
    
    if not api_key:
        print("Error: KIMI_API_KEY not found in .env file")
        sys.exit(1)
    
    client = OpenAI(
        api_key=api_key,
        base_url="https://api.moonshot.ai/v1"
    )
    
    print("\nTesting Kimi K2.5 in Instant Mode...")
    print("-" * 50)
    
    completion = client.chat.completions.create(
        model="kimi-k2.5",
        messages=[
            {
                "role": "user",
                "content": "Generate a creative product name for an AI-powered coffee maker"
            }
        ],
        temperature=0.6,
        max_tokens=256,
        thinking={
            "type": "disabled"
        }
    )
    
    response = completion.choices[0].message.content
    print(f"Response: {response}")
    print("-" * 50)
    return response


def test_streaming():
    """Test streaming response from Kimi K2.5"""
    api_key = os.getenv("KIMI_API_KEY")
    
    if not api_key:
        print("Error: KIMI_API_KEY not found in .env file")
        sys.exit(1)
    
    client = OpenAI(
        api_key=api_key,
        base_url="https://api.moonshot.ai/v1"
    )
    
    print("\nTesting Kimi K2.5 Streaming...")
    print("-" * 50)
    
    stream = client.chat.completions.create(
        model="kimi-k2.5",
        messages=[
            {
                "role": "user",
                "content": "List 3 benefits of using AI in software development"
            }
        ],
        temperature=0.6,
        max_tokens=256,
        stream=True
    )
    
    print("Streaming response:")
    for chunk in stream:
        if chunk.choices[0].delta.content:
            print(chunk.choices[0].delta.content, end="", flush=True)
    
    print("\n" + "-" * 50)


if __name__ == "__main__":
    print("=" * 50)
    print("Kimi K2.5 Test Script")
    print("=" * 50)
    
    try:
        # Run all tests
        test_basic_chat()
        test_instant_mode()
        test_thinking_mode()
        test_streaming()
        
        print("\n" + "=" * 50)
        print("All tests completed successfully!")
        print("=" * 50)
        
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
