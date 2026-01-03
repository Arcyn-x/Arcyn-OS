#!/usr/bin/env python3
"""
Minimal executable runner for System Designer Agent (F-2).

This script provides a command-line interface to the System Designer Agent,
allowing you to generate architecture designs and standards.

Usage:
    python agents/system_designer/run.py "Design Arcyn OS memory system"
    python agents/system_designer/run.py "Design Arcyn OS memory system" --output design/
    python agents/system_designer/run.py "Design Arcyn OS memory system" --pretty
"""

import sys
import json
import argparse
from pathlib import Path
from typing import Dict, Any

# Add project root to path for imports when running as script
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from agents.system_designer.system_designer_agent import SystemDesignerAgent


def main():
    """Main entry point for the System Designer Agent runner."""
    parser = argparse.ArgumentParser(
        description="System Designer Agent (F-2) - Generate architecture designs and standards",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python agents/system_designer/run.py "Design Arcyn OS memory system"
  python agents/system_designer/run.py "Design agent communication protocol" --output design/
  python agents/system_designer/run.py "Design module structure" --pretty --export
        """
    )
    
    parser.add_argument(
        'goal',
        type=str,
        help='Design goal description (e.g., "Design Arcyn OS memory system")'
    )
    
    parser.add_argument(
        '--agent-id',
        type=str,
        default='system_designer_agent',
        help='Unique identifier for the agent instance (default: system_designer_agent)'
    )
    
    parser.add_argument(
        '--log-level',
        type=int,
        default=20,
        choices=[10, 20, 30, 40, 50],
        help='Logging level: 10=DEBUG, 20=INFO, 30=WARNING, 40=ERROR, 50=CRITICAL (default: 20)'
    )
    
    parser.add_argument(
        '--output',
        type=str,
        default='design',
        help='Output directory for design artifacts (default: design/)'
    )
    
    parser.add_argument(
        '--pretty',
        action='store_true',
        help='Pretty-print JSON output with indentation'
    )
    
    parser.add_argument(
        '--export',
        action='store_true',
        help='Export artifacts to files in output directory'
    )
    
    args = parser.parse_args()
    
    # Initialize the agent
    try:
        agent = SystemDesignerAgent(agent_id=args.agent_id, log_level=args.log_level)
    except Exception as e:
        print(f"Error: Failed to initialize System Designer Agent: {e}", file=sys.stderr)
        sys.exit(1)
    
    # Generate design
    try:
        result = agent.design(args.goal)
    except Exception as e:
        print(f"Error: Failed to generate design: {e}", file=sys.stderr)
        sys.exit(1)
    
    # Export artifacts if requested
    if args.export:
        try:
            exported = agent.export_artifacts(result, args.output)
            result["exported_artifacts"] = exported
        except Exception as e:
            print(f"Warning: Failed to export artifacts: {e}", file=sys.stderr)
    
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

