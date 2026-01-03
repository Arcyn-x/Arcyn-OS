#!/usr/bin/env python3
"""
Minimal CLI interface for Persona Agent (S-1).

Provides a REPL-style interface for interacting with Arcyn OS.
"""

import sys
import argparse
from pathlib import Path

# Add project root to path for imports when running as script
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from agents.persona.persona_agent import PersonaAgent


def main():
    """Main entry point for the Persona Agent CLI."""
    parser = argparse.ArgumentParser(
        description="Persona Agent (S-1) - Human interface to Arcyn OS",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python agents/persona/run.py
  python agents/persona/run.py --verbose
  python agents/persona/run.py --log-level 10

Commands:
  build "Create a memory module"
  design "Design Arcyn OS kernel"
  status
  help
  exit
        """
    )
    
    parser.add_argument(
        '--agent-id',
        type=str,
        default='persona_agent',
        help='Unique identifier for the agent instance (default: persona_agent)'
    )
    
    parser.add_argument(
        '--log-level',
        type=int,
        default=30,
        choices=[10, 20, 30, 40, 50],
        help='Logging level: 10=DEBUG, 20=INFO, 30=WARNING, 40=ERROR, 50=CRITICAL (default: 30)'
    )
    
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Use verbose output mode'
    )
    
    args = parser.parse_args()
    
    # Initialize the agent
    try:
        agent = PersonaAgent(agent_id=args.agent_id, log_level=args.log_level, verbose=args.verbose)
    except Exception as e:
        print(f"Error: Failed to initialize Persona Agent: {e}", file=sys.stderr)
        sys.exit(1)
    
    # Print welcome message
    print("=" * 70)
    print("Arcyn OS - Persona Agent (S-1)")
    print("=" * 70)
    print("Type 'help' for available commands or 'exit' to quit.")
    print("")
    
    # REPL loop
    try:
        while True:
            try:
                # Get user input
                user_input = input("arcyn> ").strip()
                
                # Handle empty input
                if not user_input:
                    continue
                
                # Handle exit commands
                if user_input.lower() in ['exit', 'quit', 'q']:
                    print("Goodbye!")
                    break
                
                # Handle clear command
                if user_input.lower() == 'clear':
                    import os
                    os.system('cls' if os.name == 'nt' else 'clear')
                    continue
                
                # Process input
                result = agent.handle_input(user_input)
                
                # Print response
                if result.get("response"):
                    print(result["response"])
                    print("")
                
                # Print errors if any
                if result.get("error") and not result.get("success"):
                    print(f"Error: {result['error']}")
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


if __name__ == '__main__':
    main()

