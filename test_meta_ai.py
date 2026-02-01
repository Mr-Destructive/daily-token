"""
Test script to understand meta-ai-api-tool-call library usage
"""
import os
from dotenv import load_dotenv

load_dotenv()

# Test 1: Check what meta-ai-api-tool-call provides
print("=" * 70)
print("Testing meta-ai-api-tool-call library")
print("=" * 70)

try:
    from meta_ai_api_tool_call import MetaAI
    print("\n✓ Successfully imported MetaAI")
    print(f"  MetaAI class: {MetaAI}")
    print(f"  MetaAI module: {MetaAI.__module__}")
    
    # Check what methods/attributes are available
    print("\n  Available methods/attributes:")
    for attr in dir(MetaAI):
        if not attr.startswith('_'):
            print(f"    - {attr}")
    
except ImportError as e:
    print(f"\n✗ Failed to import MetaAI: {e}")
    exit(1)

# Test 2: Check how to initialize
print("\n" + "=" * 70)
print("Testing MetaAI initialization")
print("=" * 70)

meta_ai_cookie = os.getenv("META_AI_COOKIE")

if meta_ai_cookie:
    print(f"\n✓ META_AI_COOKIE found: {meta_ai_cookie[:20]}...")
    try:
        ai = MetaAI(access_token=meta_ai_cookie)
        print("✓ MetaAI initialized successfully with access_token")
        
        # Test a simple prompt
        print("\n  Testing simple prompt...")
        response = ai.prompt(message="What is 2+2?")
        print(f"  Response type: {type(response)}")
        print(f"  Response: {response}")
        
    except Exception as e:
        print(f"✗ Error initializing MetaAI: {e}")
else:
    print("\n⚠ META_AI_COOKIE not set in .env")
    print("  To use Meta-AI, add to .env:")
    print("    META_AI_COOKIE=your_cookie_here")
    print("\n  For now, using Gemini instead...")

# Test 3: Check Gemini
print("\n" + "=" * 70)
print("Testing Gemini (fallback)")
print("=" * 70)

gemini_key = os.getenv("GEMINI_API_KEY")

if gemini_key:
    print(f"\n✓ GEMINI_API_KEY found: {gemini_key[:20]}...")
    try:
        import google.generativeai as genai
        # Try to import config model, fallback to flash-lite if config fails
        try:
            import sys
            from pathlib import Path
            sys.path.append(str(Path(__file__).parent / "backend"))
            from config import GEMINI_MODEL
        except ImportError:
            GEMINI_MODEL = "gemini-2.5-flash-lite"
            
        genai.configure(api_key=gemini_key)
        print(f"  Using model: {GEMINI_MODEL}")
        model = genai.GenerativeModel(GEMINI_MODEL)
        
        print("✓ Gemini initialized successfully")
        
        # Test a simple prompt
        print("\n  Testing simple prompt...")
        response = model.generate_content("What is 2+2?")
        print(f"  Response: {response.text}")
        
    except Exception as e:
        print(f"✗ Error with Gemini: {e}")
else:
    print("\n✗ GEMINI_API_KEY not set in .env")
    print("  Add to .env:")
    print("    GEMINI_API_KEY=your_key_here")

print("\n" + "=" * 70)
print("Summary")
print("=" * 70)
print("""
For local testing, you need ONE of:
  1. GEMINI_API_KEY in .env (recommended for quick start)
  2. META_AI_COOKIE in .env (optional)

Get Gemini key (free):
  https://makersuite.google.com/app/apikey

Then run:
  python backend/test_pipeline.py
""")
