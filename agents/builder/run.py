#!/usr/bin/env python3
"""
Minimal executable runner for Builder Agent (F-1).

This script provides a command-line interface to the Builder Agent,
allowing you to execute build, modify, and refactor tasks.

Usage:
    python agents/builder/run.py task.json

Example task.json for build:
    {
        "action": "build",
        "description": "Create Arcyn OS memory module",
        "constraints": [],
        "target_path": "core/memory.py",
        "content": "# Memory module"
    }

Example task.json for modify:
    {
        "action": "modify",
        "description": "Update function signature",
        "target_path": "core/memory.py",
        "modifications": [
            {
                "type": "replace",
                "params": {
                    "old_text": "def read(key):",
                    "new_text": "def read(key: str):"
                }
            }
        ]
    }

Example task.json for refactor:
    {
        "action": "refactor",
        "description": "Rename function",
        "target_path": "core/memory.py",
        "operations": [
            {
                "type": "rename_function",
                "params": {
                    "old_name": "read",
                    "new_name": "read_data"
                }
            }
        ]
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

from agents.builder.builder_agent import BuilderAgent


def load_task(task_path: str) -> Dict[str, Any]:
    """
    Load task from JSON file.
    
    Args:
        task_path: Path to task JSON file
        
    Returns:
        Task dictionary
        
    Raises:
        FileNotFoundError: If task file doesn't exist
        json.JSONDecodeError: If JSON is invalid
    """
    task_file = Path(task_path)
    
    if not task_file.exists():
        raise FileNotFoundError(f"Task file not found: {task_path}")
    
    with open(task_file, 'r', encoding='utf-8') as f:
        task = json.load(f)
    
    return task


def main():
    """Main entry point for the Builder Agent runner."""
    parser = argparse.ArgumentParser(
        description="Builder Agent (F-1) - Execute build, modify, and refactor tasks",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python agents/builder/run.py task.json
  python agents/builder/run.py task.json --agent-id builder_001
  python agents/builder/run.py task.json --pretty
        """
    )
    
    parser.add_argument(
        'task_file',
        type=str,
        help='Path to task JSON file'
    )
    
    parser.add_argument(
        '--agent-id',
        type=str,
        default='builder_agent',
        help='Unique identifier for the agent instance (default: builder_agent)'
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
    
    # Load task
    try:
        task = load_task(args.task_file)
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in task file: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: Failed to load task file: {e}", file=sys.stderr)
        sys.exit(1)
    
    # Validate task has required fields
    action = task.get('action')
    if not action:
        print("Error: Task must have 'action' field (build, modify, or refactor)", file=sys.stderr)
        sys.exit(1)
    
    if action not in ['build', 'modify', 'refactor']:
        print(f"Error: Invalid action '{action}'. Must be 'build', 'modify', or 'refactor'", file=sys.stderr)
        sys.exit(1)
    
    # Initialize the agent
    try:
        agent = BuilderAgent(agent_id=args.agent_id, log_level=args.log_level)
    except Exception as e:
        print(f"Error: Failed to initialize Builder Agent: {e}", file=sys.stderr)
        sys.exit(1)
    
    # Execute task
    try:
        if action == 'build':
            result = agent.build(task)
        elif action == 'modify':
            result = agent.modify(task)
        elif action == 'refactor':
            result = agent.refactor(task)
        else:
            result = {"error": f"Unknown action: {action}"}
    except Exception as e:
        print(f"Error: Failed to execute task: {e}", file=sys.stderr)
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

