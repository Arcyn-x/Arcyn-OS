#!/usr/bin/env python3
"""
Test script for LLM Provider integration.

This tests the Gemini integration for Arcyn OS.
Requires GEMINI_API_KEY in .env file or environment variable.

Usage:
    python tests/test_llm_provider.py
"""

import sys
import os
from pathlib import Path

# Add project root
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Load .env file
try:
    from dotenv import load_dotenv
    env_path = project_root / '.env'
    if env_path.exists():
        load_dotenv(env_path)
        print(f"[INFO] Loaded .env from {env_path}")
except ImportError:
    print("[WARN] python-dotenv not installed, using system environment variables")


def test_basic_completion():
    """Test basic completion."""
    print("\n1. Testing basic completion...")
    
    from core.llm_provider import LLMProvider
    
    try:
        llm = LLMProvider()
        response = llm.complete("What is 2 + 2? Reply with just the number.")
        print(f"   Response: {response.content.strip()}")
        print(f"   Model: {response.model}")
        print(f"   [OK] Basic completion works")
        return True
    except Exception as e:
        print(f"   [FAIL] {str(e)}")
        return False


def test_structured_output():
    """Test structured JSON output."""
    print("\n2. Testing structured output...")
    
    from core.llm_provider import LLMProvider
    
    try:
        llm = LLMProvider()
        result = llm.structured_output(
            "List 3 programming languages with their main use case.",
            schema={"languages": [{"name": "", "use_case": ""}]}
        )
        print(f"   Result: {result}")
        print(f"   [OK] Structured output works")
        return True
    except Exception as e:
        print(f"   [FAIL] {str(e)}")
        return False


def test_prompt_builder():
    """Test the prompt builder."""
    print("\n3. Testing prompt builder...")
    
    from core.llm_provider import PromptBuilder
    
    try:
        # Test architect prompt
        prompt = PromptBuilder.architect_plan("Build a REST API for user management")
        print(f"   Architect prompt length: {len(prompt)} characters")
        
        # Test builder prompt
        prompt = PromptBuilder.builder_code({
            "name": "User model",
            "description": "Create a User SQLAlchemy model"
        })
        print(f"   Builder prompt length: {len(prompt)} characters")
        
        # Test persona prompt
        prompt = PromptBuilder.persona_classify("I want to build a login system")
        print(f"   Persona prompt length: {len(prompt)} characters")
        
        print(f"   [OK] Prompt builder works")
        return True
    except Exception as e:
        print(f"   [FAIL] {str(e)}")
        return False


def test_embeddings():
    """Test embedding generation."""
    print("\n4. Testing embeddings...")
    
    from core.llm_provider import LLMProvider
    
    try:
        llm = LLMProvider()
        embedding = llm.embed("Hello, world!")
        print(f"   Embedding dimension: {len(embedding)}")
        print(f"   First 5 values: {embedding[:5]}")
        print(f"   [OK] Embeddings work")
        return True
    except Exception as e:
        print(f"   [FAIL] {str(e)}")
        return False


def test_architect_plan():
    """Test a real Architect plan generation."""
    print("\n5. Testing Architect plan generation...")
    
    from core.llm_provider import LLMProvider, PromptBuilder
    
    try:
        llm = LLMProvider()
        
        prompt = PromptBuilder.architect_plan("Build a todo list API with user authentication")
        result = llm.structured_output(prompt)
        
        print(f"   Goal: {result.get('goal', 'N/A')}")
        print(f"   Milestones: {len(result.get('milestones', []))}")
        print(f"   Tasks: {len(result.get('tasks', []))}")
        print(f"   Decisions: {list(result.get('decisions', {}).keys())}")
        print(f"   [OK] Architect plan generation works")
        return True
    except Exception as e:
        print(f"   [FAIL] {str(e)}")
        return False


def main():
    print("=" * 60)
    print("  Arcyn OS LLM Provider Test")
    print("=" * 60)
    
    # Check API key
    if not os.environ.get("GEMINI_API_KEY"):
        print("\n[ERROR] GEMINI_API_KEY environment variable not set!")
        print("\nTo set it:")
        print("  Windows: set GEMINI_API_KEY=your-api-key-here")
        print("  Linux/Mac: export GEMINI_API_KEY=your-api-key-here")
        print("\nGet your API key from: https://aistudio.google.com/app/apikey")
        return 1
    
    print(f"\nAPI Key: {os.environ.get('GEMINI_API_KEY')[:10]}...")
    
    results = []
    
    # Run tests
    results.append(("Basic Completion", test_basic_completion()))
    results.append(("Structured Output", test_structured_output()))
    results.append(("Prompt Builder", test_prompt_builder()))
    results.append(("Embeddings", test_embeddings()))
    results.append(("Architect Plan", test_architect_plan()))
    
    # Summary
    print("\n" + "=" * 60)
    print("  Test Results")
    print("=" * 60)
    
    passed = 0
    failed = 0
    
    for name, result in results:
        status = "PASS" if result else "FAIL"
        print(f"  [{status}] {name}")
        if result:
            passed += 1
        else:
            failed += 1
    
    print("-" * 60)
    print(f"  Passed: {passed}/{len(results)}")
    print(f"  Failed: {failed}/{len(results)}")
    print("=" * 60)
    
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
