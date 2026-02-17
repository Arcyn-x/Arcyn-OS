"""
Arcyn OS - Main Entry Point.

This module provides the primary CLI interface for Arcyn OS,
supporting multiple execution modes:

    1. Interactive CLI (default)
    2. Single command execution
    3. Pipeline execution
    4. API server
    5. System status check

Usage:
    python main.py                        # Interactive CLI
    python main.py "Build a REST API"     # Execute goal through pipeline
    python main.py --status               # System status
    python main.py --api                  # Start API server
    python main.py --command "help"       # Run a command trigger
"""

import sys
import json
import logging
import argparse
from pathlib import Path

# Ensure project root is on path
project_root = Path(__file__).parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))


def print_banner():
    """Print the Arcyn OS banner."""
    print("""
    ╔═══════════════════════════════════════╗
    ║          🧠  A R C Y N   O S          ║
    ║                                       ║
    ║   AI-First Multi-Agent OS             ║
    ║   for Intelligent Development         ║
    ╚═══════════════════════════════════════╝
    """)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Arcyn OS — AI-first multi-agent operating system",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Modes:
  python main.py                        Interactive CLI mode
  python main.py "Build a REST API"     Execute goal through pipeline
  python main.py --api                  Start REST API server
  python main.py --status               Show system status
  python main.py --command "help"       Run a command trigger
  python main.py --evolution            Run Evolution Agent cycle

Examples:
  python main.py "Create a user authentication system"
  python main.py --api --port 8080
  python main.py --command "system status"
        """,
    )

    parser.add_argument('goal', type=str, nargs='?',
                        help='Goal to execute through the pipeline')
    parser.add_argument('--api', action='store_true',
                        help='Start the REST API server')
    parser.add_argument('--port', type=int, default=8000,
                        help='API server port (default: 8000)')
    parser.add_argument('--status', action='store_true',
                        help='Show system status')
    parser.add_argument('--command', '-c', type=str,
                        help='Execute a single command via CommandTrigger')
    parser.add_argument('--interactive', '-i', action='store_true',
                        help='Interactive pipeline mode')
    parser.add_argument('--evolution', '-e', action='store_true',
                        help='Run Evolution Agent single cycle')
    parser.add_argument('--verbose', '-v', action='store_true',
                        help='Verbose logging')
    parser.add_argument('--quiet', '-q', action='store_true',
                        help='Minimal output')

    args = parser.parse_args()

    log_level = logging.DEBUG if args.verbose else (
        logging.WARNING if args.quiet else logging.INFO
    )
    logging.basicConfig(level=log_level, format='%(name)s | %(levelname)s | %(message)s')

    # ── API Server ──────────────────────────────────────────────────
    if args.api:
        print_banner()
        try:
            from api.server import create_app
            import uvicorn
            app = create_app()
            print(f"  Starting API server on port {args.port}...")
            print(f"  Docs: http://localhost:{args.port}/docs\n")
            uvicorn.run(app, host="0.0.0.0", port=args.port)
        except ImportError:
            print("ERROR: FastAPI required. Install with: pip install fastapi uvicorn")
            sys.exit(1)
        return

    # ── System Status ───────────────────────────────────────────────
    if args.status:
        # Suppress all agent logs so only JSON is printed
        logging.basicConfig(level=logging.CRITICAL, format='%(message)s')
        logging.getLogger().setLevel(logging.CRITICAL)
        from core.orchestrator import Orchestrator
        orch = Orchestrator(log_level=logging.CRITICAL)
        status = orch.get_status()
        print(json.dumps(status, indent=2))
        return

    # ── Command Trigger ─────────────────────────────────────────────
    if args.command:
        from core.command_trigger import trigger
        output = trigger(args.command)
        if isinstance(output, dict):
            print(json.dumps(output, indent=2, default=str))
        else:
            print(output)
        return

    # ── Evolution Agent ─────────────────────────────────────────────
    if args.evolution:
        print_banner()
        print("  Running Evolution Agent cycle...\n")
        from agents.evolution import EvolutionAgent
        agent = EvolutionAgent()
        result = agent.run_full_cycle()
        print(json.dumps(result, indent=2, default=str))
        return

    # ── Pipeline Execution (single goal) ────────────────────────────
    if args.goal:
        print_banner()
        from core.orchestrator import Orchestrator
        orch = Orchestrator(log_level=log_level)
        print(f"  Executing: {args.goal}\n")
        result = orch.execute(args.goal)

        # Print summary
        print(f"  Status: {result['status']}")
        print(f"  Duration: {result['total_duration_ms']:.0f}ms")
        if result.get('error'):
            print(f"  Error: {result['error']}")
        print()

        for stage in result.get('stages', []):
            icon = "✓" if stage['status'] == 'completed' else "✗"
            print(f"    {icon} {stage['name']:12s}  "
                  f"{stage['duration_ms']:6.0f}ms  {stage['status']}")

        print()

        if args.verbose:
            print(json.dumps(result, indent=2, default=str))
        return

    # ── Interactive Mode ────────────────────────────────────────────
    print_banner()
    from core.orchestrator import Orchestrator
    orch = Orchestrator(log_level=log_level)

    print("  Commands:")
    print("    <goal>     Execute goal through pipeline")
    print("    status     Show system status")
    print("    evolution  Run Evolution Agent cycle")
    print("    help       Show help")
    print("    exit       Quit")
    print()

    while True:
        try:
            user_input = input("  arcyn > ").strip()

            if not user_input:
                continue

            if user_input.lower() in ('exit', 'quit', 'q'):
                print("\n  Shutting down Arcyn OS.\n")
                break

            if user_input.lower() == 'status':
                print(json.dumps(orch.get_status(), indent=2))
                continue

            if user_input.lower() == 'evolution':
                from agents.evolution import EvolutionAgent
                agent = EvolutionAgent()
                result = agent.run_full_cycle()
                print(json.dumps(result, indent=2, default=str))
                continue

            if user_input.lower() == 'help':
                print("\n  Arcyn OS Interactive Mode")
                print("  Type a goal to execute through the agent pipeline.")
                print("  Example: 'Build a REST API for task management'\n")
                continue

            # Execute as pipeline goal
            print(f"\n  Executing: {user_input}\n")
            result = orch.execute(user_input)

            print(f"  Status: {result['status']}")
            print(f"  Duration: {result['total_duration_ms']:.0f}ms")
            if result.get('error'):
                print(f"  Error: {result['error']}")
            print()

            for stage in result.get('stages', []):
                icon = "✓" if stage['status'] == 'completed' else "✗"
                print(f"    {icon} {stage['name']:12s}  "
                      f"{stage['duration_ms']:6.0f}ms  {stage['status']}")
            print()

        except KeyboardInterrupt:
            print("\n\n  Type 'exit' to quit.\n")
        except EOFError:
            break


if __name__ == '__main__':
    main()
