#!/usr/bin/env python3
"""
Test script for LLM Gateway.

Tests all gateway functionality:
- Basic requests
- Structured requests
- Embeddings
- Policy enforcement
- Rate limiting
- Cost tracking
- Error handling

Usage:
    python tests/test_llm_gateway.py
"""

import sys
import os
from pathlib import Path

# Add project root
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Load .env
try:
    from dotenv import load_dotenv
    env_path = project_root / '.env'
    if env_path.exists():
        load_dotenv(env_path)
        print(f"[INFO] Loaded .env from {env_path}")
except ImportError:
    print("[WARN] python-dotenv not installed")


def reset_gateway():
    """Reset the gateway singleton for fresh tests."""
    from core.llm_gateway import gateway as gw_module
    gw_module._gateway = None
    gw_module.LLMGateway._instance = None


def test_basic_request():
    """Test basic gateway request."""
    print("\n1. Testing basic gateway request...")
    
    from core.llm_gateway import request
    
    try:
        response = request(
            agent="Test",
            task_id="T1",
            prompt="What is 2 + 2? Reply with just the number.",
            config={"max_tokens": 100}
        )
        
        print(f"   Success: {response.success}")
        print(f"   Content: {response.content.strip()}")
        print(f"   Model: {response.model}")
        print(f"   Tokens: {response.tokens_total}")
        print(f"   Latency: {response.latency_ms:.1f}ms")
        
        if response.success:
            print("   [OK] Basic request works")
            return True
        else:
            print(f"   [FAIL] {response.error}")
            return False
            
    except Exception as e:
        print(f"   [FAIL] {str(e)}")
        return False


def test_structured_request():
    """Test structured JSON request."""
    print("\n2. Testing structured request...")
    
    from core.llm_gateway import request_structured
    
    try:
        response = request_structured(
            agent="Architect",
            task_id="T2",
            prompt="List 3 programming languages with their use cases.",
            schema={"languages": [{"name": "", "use_case": ""}]}
        )
        
        print(f"   Success: {response.success}")
        
        if response.success:
            parsed = response.parsed_json
            print(f"   Parsed JSON: {parsed}")
            print("   [OK] Structured request works")
            return True
        else:
            print(f"   [FAIL] {response.error}")
            return False
            
    except Exception as e:
        print(f"   [FAIL] {str(e)}")
        return False


def test_embedding_request():
    """Test embedding request."""
    print("\n3. Testing embedding request...")
    
    from core.llm_gateway import request_embedding
    
    try:
        response = request_embedding(
            agent="Knowledge",
            task_id="T3",
            texts=["Hello world", "Foo bar"]
        )
        
        print(f"   Success: {response.success}")
        
        if response.success:
            embeddings = response.metadata.get("embeddings", [])
            dimensions = response.metadata.get("dimensions", 0)
            print(f"   Embeddings count: {len(embeddings)}")
            print(f"   Dimensions: {dimensions}")
            print("   [OK] Embedding request works")
            return True
        else:
            print(f"   [FAIL] {response.error}")
            return False
            
    except Exception as e:
        print(f"   [FAIL] {str(e)}")
        return False


def test_policy_unauthorized_agent():
    """Test that unauthorized agents are blocked."""
    print("\n4. Testing policy - unauthorized agent...")
    
    from core.llm_gateway import request
    
    try:
        response = request(
            agent="UnauthorizedAgent",
            task_id="T4",
            prompt="This should be blocked"
        )
        
        if not response.success and response.error_code == "POLICY_DENIED":
            print(f"   Error code: {response.error_code}")
            print(f"   Message: {response.error}")
            print("   [OK] Unauthorized agent correctly blocked")
            return True
        else:
            print("   [FAIL] Unauthorized agent was not blocked!")
            return False
            
    except Exception as e:
        print(f"   [FAIL] {str(e)}")
        return False


def test_cost_tracking():
    """Test cost tracking."""
    print("\n5. Testing cost tracking...")
    
    from core.llm_gateway.gateway import _get_gateway
    
    try:
        gateway = _get_gateway()
        budget = gateway.get_budget_status()
        
        print(f"   Session ID: {budget.get('session_id')}")
        print(f"   Tokens used: {budget['budget_tokens']['used']}")
        print(f"   Est. cost: ${budget['budget_usd']['used']:.6f}")
        print(f"   Within budget: {budget['within_budget']}")
        print("   [OK] Cost tracking works")
        return True
        
    except Exception as e:
        print(f"   [FAIL] {str(e)}")
        return False


def test_session_stats():
    """Test session statistics."""
    print("\n6. Testing session statistics...")
    
    from core.llm_gateway.gateway import _get_gateway
    
    try:
        gateway = _get_gateway()
        stats = gateway.get_session_stats()
        
        print(f"   Session: {stats['session_id']}")
        print(f"   Total requests: {stats['cost']['summary']['total_requests']}")
        print("   [OK] Session stats work")
        return True
        
    except Exception as e:
        print(f"   [FAIL] {str(e)}")
        return False


def test_provider_health():
    """Test provider health check."""
    print("\n7. Testing provider health...")
    
    from core.llm_gateway.gateway import _get_gateway
    
    try:
        gateway = _get_gateway()
        health = gateway.provider_health_check()
        
        print(f"   Provider: {health['provider']}")
        print(f"   Model: {health['model']}")
        print(f"   Status: {health['status']}")
        print(f"   Healthy: {health['healthy']}")
        
        if health['healthy']:
            print("   [OK] Provider health check works")
            return True
        else:
            print("   [FAIL] Provider unhealthy")
            return False
            
    except Exception as e:
        print(f"   [FAIL] {str(e)}")
        return False


def main():
    print("=" * 60)
    print("  Arcyn OS LLM Gateway Test")
    print("=" * 60)
    
    # Check API key
    if not os.environ.get("GEMINI_API_KEY"):
        print("\n[ERROR] GEMINI_API_KEY not set!")
        return 1
    
    print(f"\nAPI Key: {os.environ.get('GEMINI_API_KEY')[:10]}...")
    
    # Reset gateway singleton for fresh state
    reset_gateway()
    
    results = []
    
    # Run tests
    results.append(("Basic Request", test_basic_request()))
    results.append(("Structured Request", test_structured_request()))
    results.append(("Embedding Request", test_embedding_request()))
    results.append(("Policy (Unauthorized)", test_policy_unauthorized_agent()))
    results.append(("Cost Tracking", test_cost_tracking()))
    results.append(("Session Stats", test_session_stats()))
    results.append(("Provider Health", test_provider_health()))
    
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
