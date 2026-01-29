"""Quick test to verify Gemini Flash 1.5 is working."""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Test Gemini adapter
from llm_adapters import GeminiAdapter
import asyncio

async def test_gemini():
    print("Testing Gemini 2.5 Flash Lite...")
    print("=" * 50)

    api_key = os.getenv('GOOGLE_API_KEY')
    if not api_key:
        print("No API key found!")
        return

    print(f"API key loaded: {api_key[:10]}...")
    print(f"Model: gemini-2.5-flash-lite")
    print()

    # Create adapter
    gemini = GeminiAdapter(api_key=api_key)

    # Test prompt
    prompt = """You are an AI agent in Minecraft. You are curious and adventurous.

Current status:
- Health: 20/20
- Hunger: 20/20
- Inventory: Empty
- Location: Unknown

Generate ONE goal for yourself (one sentence, no explanation)."""

    print("Sending prompt to Gemini...")
    print()

    # Generate response
    response = await gemini.generate(prompt)

    print("Gemini Response:")
    print("-" * 50)
    print(response)
    print("-" * 50)
    print()
    print("Gemini 2.5 Flash Lite is working!")

if __name__ == "__main__":
    asyncio.run(test_gemini())
