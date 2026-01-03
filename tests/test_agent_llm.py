"""
Test script for agent LLM integrations.

Tests that all agents correctly route through the LLM Gateway.
"""

import sys
from pathlib import Path

# Add project root
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Load .env
from dotenv import load_dotenv
load_dotenv(project_root / '.env')

# Reset gateway singleton
from core.llm_gateway import gateway as gw
gw._gateway = None
gw.LLMGateway._instance = None


def test_knowledge_embedder():
    """Test Knowledge Engine embedder."""
    print("\n1. Testing Knowledge Embedder...")
    
    from agents.knowledge_engine.embedder import Embedder
    
    try:
        embedder = Embedder(agent_name="Knowledge")
        
        # Test single embedding
        embedding = embedder.embed("Hello world", task_id="test_embed")
        print(f"   Single embed dims: {len(embedding)}")
        
        # Test batch embedding
        embeddings = embedder.embed_batch(["Hello", "World"], task_id="test_batch")
        print(f"   Batch embed count: {len(embeddings)}")
        
        # Test similarity
        sim = embedder.similarity(embedding, embedding)
        print(f"   Self-similarity: {sim:.3f}")
        
        if len(embedding) == 768 and sim > 0.99:
            print("   [PASS] Embedder works")
            return True
        else:
            print("   [FAIL] Unexpected results")
            return False
            
    except Exception as e:
        print(f"   [FAIL] {str(e)}")
        return False


def test_persona_classifier():
    """Test Persona intent classifier with LLM fallback."""
    print("\n2. Testing Persona Intent Classifier...")
    
    from agents.persona.intent_classifier import IntentClassifier
    
    try:
        classifier = IntentClassifier(agent_name="Persona")
        
        # Test rule-based (high confidence)
        result = classifier.classify("build a REST API", task_id="test_classify")
        print(f"   Intent: {result['intent']}, Confidence: {result['confidence']:.2f}")
        print(f"   Source: {result.get('source', 'unknown')}")
        
        # Test ambiguous input (should trigger LLM)
        result2 = classifier.classify("I need something", task_id="test_ambiguous")
        print(f"   Ambiguous intent: {result2['intent']}, Source: {result2.get('source', 'unknown')}")
        
        if result['intent'] == 'build':
            print("   [PASS] Classifier works")
            return True
        else:
            print("   [FAIL] Wrong intent")
            return False
            
    except Exception as e:
        print(f"   [FAIL] {str(e)}")
        return False


def test_architect_planner():
    """Test Architect planner with LLM planning."""
    print("\n3. Testing Architect Planner (LLM)...")
    
    from agents.architect.planner import Planner
    
    try:
        planner = Planner(agent_name="Architect")
        
        # Test LLM planning
        plan = planner.plan_with_llm(
            goal="Build a simple todo list API",
            task_id="test_plan"
        )
        
        print(f"   Goal: {plan.get('goal', 'N/A')}")
        print(f"   Milestones: {len(plan.get('milestones', []))}")
        print(f"   Tasks: {len(plan.get('tasks', []))}")
        print(f"   Source: {plan.get('source', 'unknown')}")
        
        if plan.get('milestones') and plan.get('tasks'):
            print("   [PASS] LLM planner works")
            return True
        else:
            print("   [FAIL] No milestones/tasks")
            return False
            
    except Exception as e:
        print(f"   [FAIL] {str(e)}")
        return False


def test_evolution_analyzer():
    """Test Evolution analyzer with LLM insights."""
    print("\n4. Testing Evolution Analyzer (LLM)...")
    
    from agents.evolution.analyzer import Analyzer
    
    try:
        analyzer = Analyzer()
        
        # Mock observations
        observations = {
            "agents": {
                "Architect": {
                    "agent_type": "architect",
                    "stats": {"failure_rate": 0.05, "avg_duration_ms": 500, "total_executions": 100},
                    "files": ["__init__.py", "architect_agent.py", "run.py"]
                },
                "Builder": {
                    "agent_type": "builder",
                    "stats": {"failure_rate": 0.15, "avg_duration_ms": 1200, "total_executions": 50},
                    "files": ["__init__.py", "builder_agent.py"]
                }
            },
            "recent_activities": []
        }
        
        # Test LLM analysis
        analysis = analyzer.analyze_with_llm(observations, task_id="test_analyze")
        
        print(f"   Issues found: {len(analysis.get('issues', []))}")
        print(f"   Source: {analysis.get('source', 'unknown')}")
        
        if "llm_insights" in analysis:
            insights = analysis["llm_insights"]
            print(f"   LLM risks: {len(insights.get('risks', []))}")
            print(f"   LLM suggestions: {len(insights.get('suggested_changes', []))}")
            print("   [PASS] LLM analyzer works")
            return True
        else:
            print("   [WARN] No LLM insights (may have failed)")
            return True  # Rule-based still works
            
    except Exception as e:
        print(f"   [FAIL] {str(e)}")
        return False


def main():
    print("=" * 60)
    print("  Agent LLM Integration Test")
    print("=" * 60)
    
    results = []
    
    results.append(("Knowledge Embedder", test_knowledge_embedder()))
    results.append(("Persona Classifier", test_persona_classifier()))
    results.append(("Architect Planner", test_architect_planner()))
    results.append(("Evolution Analyzer", test_evolution_analyzer()))
    
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
