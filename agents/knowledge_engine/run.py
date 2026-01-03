#!/usr/bin/env python3
"""
Minimal CLI interface for Knowledge Engine (S-2).

Provides commands for ingesting, querying, and summarizing knowledge.
"""

import sys
import json
import argparse
from pathlib import Path
from typing import Dict, Any

# Add project root to path for imports when running as script
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from agents.knowledge_engine.knowledge_engine import KnowledgeEngine


def parse_ingest_args(args: list) -> Dict[str, Any]:
    """
    Parse ingest command arguments.
    
    Args:
        args: Command arguments
    
    Returns:
        Source dictionary
    """
    source = {}
    
    i = 0
    while i < len(args):
        arg = args[i]
        
        if arg == "--namespace" and i + 1 < len(args):
            source["namespace"] = args[i + 1]
            i += 2
        elif arg == "--key" and i + 1 < len(args):
            source["key"] = args[i + 1]
            i += 2
        elif arg == "--agent" and i + 1 < len(args):
            source["source_agent"] = args[i + 1]
            i += 2
        elif arg == "--file" and i + 1 < len(args):
            # Load content from file
            file_path = Path(args[i + 1])
            if file_path.exists():
                with open(file_path, 'r') as f:
                    source["content"] = json.load(f)
            i += 2
        elif arg == "--content" and i + 1 < len(args):
            try:
                source["content"] = json.loads(args[i + 1])
            except json.JSONDecodeError:
                source["content"] = args[i + 1]  # Fallback to string
            i += 2
        else:
            i += 1
    
    return source


def main():
    """Main entry point for the Knowledge Engine CLI."""
    parser = argparse.ArgumentParser(
        description="Knowledge Engine (S-2) - Structured memory and knowledge retrieval",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python agents/knowledge_engine/run.py ingest --namespace architecture --key design_001 --agent system_designer --file design.json
  python agents/knowledge_engine/run.py query "memory system"
  python agents/knowledge_engine/run.py summarize --namespace architecture
        """
    )
    
    parser.add_argument(
        '--agent-id',
        type=str,
        default='knowledge_engine',
        help='Unique identifier for the agent instance (default: knowledge_engine)'
    )
    
    parser.add_argument(
        '--log-level',
        type=int,
        default=20,
        choices=[10, 20, 30, 40, 50],
        help='Logging level: 10=DEBUG, 20=INFO, 30=WARNING, 40=ERROR, 50=CRITICAL (default: 20)'
    )
    
    parser.add_argument(
        '--db-path',
        type=str,
        default=None,
        help='Path to knowledge database (default: ./knowledge/knowledge.db)'
    )
    
    args, remaining = parser.parse_known_args()
    
    # Initialize the engine
    try:
        engine = KnowledgeEngine(agent_id=args.agent_id, log_level=args.log_level, db_path=args.db_path)
    except Exception as e:
        print(f"Error: Failed to initialize Knowledge Engine: {e}", file=sys.stderr)
        sys.exit(1)
    
    # Handle commands
    if not remaining:
        # Interactive mode
        print("=" * 70)
        print("Arcyn OS - Knowledge Engine (S-2)")
        print("=" * 70)
        print("Commands: ingest, query, summarize, status, exit")
        print("")
        
        try:
            while True:
                try:
                    user_input = input("knowledge> ").strip()
                    
                    if not user_input:
                        continue
                    
                    if user_input.lower() in ['exit', 'quit', 'q']:
                        print("Goodbye!")
                        break
                    
                    # Parse command
                    parts = user_input.split()
                    command = parts[0].lower()
                    cmd_args = parts[1:]
                    
                    if command == "ingest":
                        source = parse_ingest_args(cmd_args)
                        result = engine.ingest(source)
                        if result["success"]:
                            print(f"Success: Ingested as {result['record_id']}")
                        else:
                            print(f"Error: {result['error']}")
                    
                    elif command == "query":
                        query = " ".join(cmd_args) if cmd_args else ""
                        if not query:
                            print("Error: Query required")
                            continue
                        result = engine.query(query)
                        print(f"Found {result['count']} matches")
                        for i, entry in enumerate(result["matched_entries"][:5], 1):
                            print(f"  {i}. {str(entry)[:100]}...")
                    
                    elif command == "summarize":
                        scope = {}
                        i = 0
                        while i < len(cmd_args):
                            if cmd_args[i] == "--namespace" and i + 1 < len(cmd_args):
                                scope["namespace"] = cmd_args[i + 1]
                                i += 2
                            elif cmd_args[i] == "--agent" and i + 1 < len(cmd_args):
                                scope["source_agent"] = cmd_args[i + 1]
                                i += 2
                            else:
                                i += 1
                        result = engine.summarize(scope)
                        print(f"Summary: {result['record_count']} records in {len(result['namespaces'])} namespace(s)")
                        print(f"Namespaces: {', '.join(result['namespaces'])}")
                    
                    elif command == "status":
                        status = engine.get_status()
                        print(f"Status: {status['state']}")
                        print(f"Namespaces: {len(status['namespaces'])}")
                        print(f"Total records: {status['total_records']}")
                    
                    else:
                        print(f"Unknown command: {command}")
                        print("Commands: ingest, query, summarize, status, exit")
                    
                    print("")
                
                except KeyboardInterrupt:
                    print("\n\nInterrupted. Type 'exit' to quit.")
                    continue
                except EOFError:
                    print("\nGoodbye!")
                    break
                except Exception as e:
                    print(f"Error: {str(e)}")
                    print("")
        
        except Exception as e:
            print(f"Fatal error: {e}", file=sys.stderr)
            sys.exit(1)
    
    else:
        # Command-line mode
        command = remaining[0].lower()
        cmd_args = remaining[1:]
        
        try:
            if command == "ingest":
                source = parse_ingest_args(cmd_args)
                result = engine.ingest(source)
                if result["success"]:
                    print(json.dumps(result, indent=2))
                    sys.exit(0)
                else:
                    print(f"Error: {result['error']}", file=sys.stderr)
                    sys.exit(1)
            
            elif command == "query":
                query = " ".join(cmd_args) if cmd_args else ""
                if not query:
                    print("Error: Query required", file=sys.stderr)
                    sys.exit(1)
                result = engine.query(query)
                print(json.dumps(result, indent=2))
            
            elif command == "summarize":
                scope = {}
                i = 0
                while i < len(cmd_args):
                    if cmd_args[i] == "--namespace" and i + 1 < len(cmd_args):
                        scope["namespace"] = cmd_args[i + 1]
                        i += 2
                    elif cmd_args[i] == "--agent" and i + 1 < len(cmd_args):
                        scope["source_agent"] = cmd_args[i + 1]
                        i += 2
                    else:
                        i += 1
                result = engine.summarize(scope)
                print(json.dumps(result, indent=2))
            
            else:
                print(f"Unknown command: {command}", file=sys.stderr)
                parser.print_help()
                sys.exit(1)
        
        except Exception as e:
            print(f"Error: {str(e)}", file=sys.stderr)
            sys.exit(1)


if __name__ == '__main__':
    main()

