"""
Command Trigger for Arcyn OS.

Single-entry execution interface that accepts natural-language commands
and returns predefined system outputs.

This trigger acts as a DISPATCHER, not an agent.
It does not think — it routes.

Usage:
    from core.command_trigger import trigger
    
    output = trigger("Give me the full Arcyn OS loop test prompt.")
    print(output)

CLI Usage:
    python core/command_trigger.py "Your command here"
    python core/command_trigger.py --interactive

Design Constraints:
    - Deterministic behavior
    - No background loops
    - No autonomous execution
    - No system mutation
    - Output-only authority

Future Integration Points:
    # TODO: Voice trigger hook - trigger(transcribed_audio)
    # TODO: UI button hook - trigger_from_ui(button_id)
    # TODO: API endpoint hook - POST /api/trigger {command: "..."}
    # TODO: Webhook hook - POST /webhook/command
    # TODO: Slack/Discord bot hook - on_message(text)
"""

import sys
from pathlib import Path
from typing import Optional

# Add project root to path
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from core.intent_router import IntentRouter, Intent
from core.dispatcher import Dispatcher


class CommandTrigger:
    """
    Main command trigger interface.
    
    Accepts string commands, classifies intent, and returns
    complete system outputs. Acts as the keyboard of Arcyn OS.
    
    Example:
        >>> trigger = CommandTrigger()
        >>> output = trigger.execute("Give me the full Arcyn OS loop test prompt.")
        >>> print(output)
    
    Attributes:
        router: IntentRouter for classifying commands
        dispatcher: Dispatcher for generating outputs
    """
    
    def __init__(self):
        """Initialize the command trigger."""
        self.router = IntentRouter()
        self.dispatcher = Dispatcher()
    
    def execute(self, command: str) -> str:
        """
        Execute a command and return the output.
        
        Args:
            command: Natural language command string
            
        Returns:
            Complete, copy-paste-ready output string
            
        Example:
            >>> trigger = CommandTrigger()
            >>> output = trigger.execute("system status")
            >>> print(output)
        """
        # Validate input
        if not command or not command.strip():
            return "Command not recognized by Arcyn OS.\n\nPlease provide a command."
        
        # Classify intent
        intent_match = self.router.classify(command)
        
        # Dispatch to handler
        output = self.dispatcher.dispatch(intent_match)
        
        return output
    
    def get_intent(self, command: str) -> str:
        """
        Get the classified intent for a command (for debugging).
        
        Args:
            command: Natural language command string
            
        Returns:
            Intent name as string
        """
        intent_match = self.router.classify(command)
        return intent_match.intent.value
    
    def get_supported_commands(self) -> list:
        """Return list of supported command intents."""
        return self.router.get_supported_intents()


# Global trigger instance for convenience
_trigger: Optional[CommandTrigger] = None


def get_trigger() -> CommandTrigger:
    """Get or create the global trigger instance."""
    global _trigger
    if _trigger is None:
        _trigger = CommandTrigger()
    return _trigger


def trigger(command: str) -> str:
    """
    Convenience function to execute a command.
    
    Args:
        command: Natural language command string
        
    Returns:
        Complete output string
        
    Example:
        >>> from core.command_trigger import trigger
        >>> output = trigger("Give me the full Arcyn OS loop test prompt.")
        >>> print(output)
    """
    return get_trigger().execute(command)


# =============================================================================
# CLI Interface
# =============================================================================

def run_interactive():
    """Run interactive command loop."""
    print("\n" + "=" * 60)
    print("  Arcyn OS Command Trigger")
    print("  The keyboard of Arcyn OS")
    print("=" * 60)
    print("  Type a command or 'exit' to quit")
    print("  Type 'help' for available commands")
    print("=" * 60 + "\n")
    
    cmd_trigger = CommandTrigger()
    
    while True:
        try:
            command = input("Arcyn > ").strip()
            
            if not command:
                continue
            
            if command.lower() in ("exit", "quit"):
                print("\nArcyn OS Command Trigger shutting down.\n")
                break
            
            output = cmd_trigger.execute(command)
            print("\n" + output)
            
        except KeyboardInterrupt:
            print("\n\nInterrupted. Type 'exit' to quit.\n")
        except EOFError:
            print("\nExiting...")
            break


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Arcyn OS Command Trigger",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python core/command_trigger.py "Give me the full Arcyn OS loop test"
  python core/command_trigger.py "system status"
  python core/command_trigger.py --interactive
  python core/command_trigger.py -i

Available Commands:
  - "full arcyn os loop test" - Get loop test prompt
  - "agent prompt for [name]" - Get agent build prompt
  - "system status" - Check system health
  - "explain architecture" - Get architecture overview
  - "run evolution cycle" - Run system analysis
  - "help" - Show help
        """
    )
    
    parser.add_argument(
        'command',
        type=str,
        nargs='?',
        help='Command to execute'
    )
    
    parser.add_argument(
        '-i', '--interactive',
        action='store_true',
        help='Run in interactive mode'
    )
    
    args = parser.parse_args()
    
    if args.interactive:
        run_interactive()
    elif args.command:
        output = trigger(args.command)
        print(output)
    else:
        # Default to interactive if no arguments
        run_interactive()


if __name__ == '__main__':
    main()
