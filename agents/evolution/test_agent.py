#!/usr/bin/env python3
"""
Test script for Evolution Agent (S-3).
"""

import sys
from pathlib import Path

# Add project root
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from agents.evolution import EvolutionAgent


def main():
    print("=" * 50)
    print("Evolution Agent Test Run")
    print("=" * 50)
    
    # Initialize agent
    agent = EvolutionAgent()
    print(f"\nAgent initialized: {agent.agent_id}")
    
    # Simulate some agent activities
    agent.record_agent_activity('architect_agent', 'architect', 'plan', 'success', 150)
    agent.record_agent_activity('architect_agent', 'architect', 'breakdown', 'success', 75)
    agent.record_agent_activity('builder_agent', 'builder', 'build', 'success', 200)
    agent.record_agent_activity('builder_agent', 'builder', 'build', 'failure', 50, 'Syntax error in generated code')
    agent.record_agent_activity('integrator_agent', 'integrator', 'integrate', 'success', 300)
    
    print("\n--- Running Full Cycle ---\n")
    
    # Run full cycle
    result = agent.run_full_cycle()
    
    # Print results
    print("\n>>> Observation:")
    obs = result["observation"]
    print(f"    Agents: {len(obs['agents'])}")
    print(f"    Activities: {len(obs['recent_activities'])}")
    print(f"    Warnings: {len(obs['warnings'])}")
    print(f"    Errors: {len(obs['errors'])}")
    
    print("\n>>> Analysis:")
    analysis = result["analysis"]
    summary = analysis["summary"]
    print(f"    Issues: {summary['total_issues']}")
    print(f"    Health: {summary['health']}")
    print(f"    Bottlenecks: {summary.get('bottlenecks', 0)}")
    
    if analysis.get("issues"):
        print("    Top Issues:")
        for issue in analysis["issues"][:3]:
            print(f"      - [{issue['severity']}] {issue['title']}")
    
    print("\n>>> Recommendations:")
    recs = result["recommendations"]
    print(f"    Count: {len(recs['recommendations'])}")
    print(f"    Priority: {recs['priority']}")
    print(f"    Confidence: {recs['confidence']:.0%}")
    
    if recs.get("recommendations"):
        print("    Top Recommendations:")
        for rec in recs["recommendations"][:3]:
            print(f"      - [{rec['priority']}] {rec['title']}")
    
    print("\n>>> Health Score:")
    health = result["health_score"]
    print(f"    Score: {health['overall_score']:.1%}")
    print(f"    Status: {health['overall_status']}")
    
    print("\n" + "=" * 50)
    print("Test completed successfully!")
    print("=" * 50)


if __name__ == "__main__":
    main()
