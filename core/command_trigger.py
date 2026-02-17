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
from typing import Any, Dict, Optional

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
# Integration Hooks
# =============================================================================

class WebhookTrigger:
    """
    Integration hook for external trigger sources.

    Wraps the CommandTrigger with source-specific metadata and
    structured JSON responses for programmatic consumers.

    Supported sources:
        - Voice transcription (speech-to-text output)
        - UI button actions (button_id → command mapping)
        - Webhook payloads (POST /webhook/command)
        - Chat bot messages (Slack, Discord, etc.)

    Example:
        >>> hook = WebhookTrigger()
        >>> result = hook.from_webhook({"command": "system status", "source": "slack"})
        >>> print(result["output"])
    """

    def __init__(self):
        """Initialize the webhook trigger."""
        self._trigger = get_trigger()
        self._button_map: Dict[str, str] = {
            "btn_status": "system status",
            "btn_architecture": "explain architecture",
            "btn_loop_test": "full arcyn os loop test",
            "btn_evolution": "run evolution cycle",
            "btn_help": "help",
        }

    def from_voice(self, transcription: str) -> Dict[str, Any]:
        """
        Process a voice transcription.

        Args:
            transcription: Transcribed text from speech-to-text

        Returns:
            Structured result with output and metadata
        """
        cleaned = transcription.strip()
        if not cleaned:
            return {
                "success": False,
                "source": "voice",
                "error": "Empty transcription",
                "output": ""
            }

        output = self._trigger.execute(cleaned)
        return {
            "success": True,
            "source": "voice",
            "input": cleaned,
            "intent": self._trigger.get_intent(cleaned),
            "output": output
        }

    def from_ui_button(self, button_id: str) -> Dict[str, Any]:
        """
        Process a UI button click.

        Args:
            button_id: Identifier of the button clicked

        Returns:
            Structured result with output and metadata
        """
        command = self._button_map.get(button_id)
        if not command:
            return {
                "success": False,
                "source": "ui",
                "error": f"Unknown button: {button_id}",
                "available_buttons": list(self._button_map.keys()),
                "output": ""
            }

        output = self._trigger.execute(command)
        return {
            "success": True,
            "source": "ui",
            "button_id": button_id,
            "command": command,
            "output": output
        }

    def from_webhook(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a webhook payload.

        Expected payload format:
            {
                "command": str,           # Required — the command to execute
                "source": str,            # Optional — source identifier
                "callback_url": str       # Optional — URL for async response
            }

        Args:
            payload: Webhook payload dictionary

        Returns:
            Structured result with output and metadata
        """
        command = payload.get("command", "").strip()
        source = payload.get("source", "webhook")

        if not command:
            return {
                "success": False,
                "source": source,
                "error": "Missing 'command' in payload",
                "output": ""
            }

        output = self._trigger.execute(command)
        return {
            "success": True,
            "source": source,
            "command": command,
            "intent": self._trigger.get_intent(command),
            "output": output
        }

    def from_chat_bot(self, message: str, platform: str = "generic") -> Dict[str, Any]:
        """
        Process a chat bot message (Slack, Discord, etc.).

        Args:
            message: Message text from the bot
            platform: Platform identifier (e.g., "slack", "discord")

        Returns:
            Structured result with output and metadata
        """
        # Strip bot mentions (e.g., @arcyn, /arcyn)
        import re
        cleaned = re.sub(r'^[@/]?\s*arcyn\s*', '', message, flags=re.IGNORECASE).strip()
        if not cleaned:
            return {
                "success": False,
                "source": platform,
                "error": "Empty message after stripping bot mention",
                "output": ""
            }

        output = self._trigger.execute(cleaned)
        return {
            "success": True,
            "source": platform,
            "input": cleaned,
            "intent": self._trigger.get_intent(cleaned),
            "output": output
        }

    def register_button(self, button_id: str, command: str) -> None:
        """
        Register a UI button mapping.

        Args:
            button_id: Button identifier
            command: Command string to execute when clicked
        """
        self._button_map[button_id] = command


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
