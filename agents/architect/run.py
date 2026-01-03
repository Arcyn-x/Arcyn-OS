#!/usr/bin/env python3
"""
Minimal executable runner for Architect Agent (A-1).

This script provides a command-line interface to the Architect Agent,
allowing you to generate development plans from high-level goals.

Usage:
    python agents/architect/run.py "Build a REST API for user management"
    python agents/architect/run.py "Design Arcyn OS kernel"
    python agents/architect/run.py "Create a web application with authentication"

Example:
    $ python agents/architect/run.py "Design Arcyn OS kernel"
    
    Output:
    {
        "goal": "Design Arcyn OS kernel",
        "milestones": [...],
        "tasks": [...],
        "task_graph": {...},
        "metadata": {...}
    }
"""

import sys
import json
import argparse
from pathlib import Path
from typing import Dict, Any

# Add project root to path for imports when running as script
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from agents.architect.architect_agent import ArchitectAgent


def main():
    """Main entry point for the Architect Agent runner."""
    parser = argparse.ArgumentParser(
        description="Architect Agent (A-1) - Generate development plans from goals",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python agents/architect/run.py "Build a REST API"
  python agents/architect/run.py "Design Arcyn OS kernel"
  python agents/architect/run.py "Create a web application with authentication"
        """
    )
    
    parser.add_argument(
        'goal',
        type=str,
        nargs='?',
        help='High-level goal description (e.g., "Build a REST API")'
    )
    
    parser.add_argument(
        '--agent-id',
        type=str,
        default='architect_agent',
        help='Unique identifier for the agent instance (default: architect_agent)'
    )
    
    parser.add_argument(
        '--log-level',
        type=int,
        default=20,
        choices=[10, 20, 30, 40, 50],
        help='Logging level: 10=DEBUG, 20=INFO, 30=WARNING, 40=ERROR, 50=CRITICAL (default: 20)'
    )
    
    parser.add_argument(
        '--pretty',
        action='store_true',
        help='Pretty-print JSON output with indentation'
    )
    
    args = parser.parse_args()
    
    # Handle missing goal argument gracefully
    if not args.goal:
        parser.print_help()
        print("\nError: Goal argument is required.", file=sys.stderr)
        print("Example: python agents/architect/run.py \"Build a REST API\"", file=sys.stderr)
        sys.exit(1)
    
    # Initialize the agent
    try:
        agent = ArchitectAgent(agent_id=args.agent_id, log_level=args.log_level)
    except Exception as e:
        print(f"Error: Failed to initialize Architect Agent: {e}", file=sys.stderr)
        sys.exit(1)
    
    # Generate plan
    try:
        result = agent.plan(args.goal)
    except Exception as e:
        print(f"Error: Failed to generate plan: {e}", file=sys.stderr)
        sys.exit(1)
    
    # Output result as JSON
    try:
        if args.pretty:
            json_output = json.dumps(result, indent=2, ensure_ascii=False)
        else:
            json_output = json.dumps(result, ensure_ascii=False)
        
        print(json_output)
    except Exception as e:
        print(f"Error: Failed to serialize result: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()

