#!/usr/bin/env python3
"""
Minimal CLI runner for Evolution Agent (S-3).

Provides a command-line interface for the Evolution Agent with commands:
- observe: Collect system snapshot
- analyze: Analyze observations
- recommend: Generate recommendations
- status: Show agent status
- health: Show health report
- cycle: Run full observe → analyze → recommend cycle
- exit: Exit the CLI

Usage:
    python agents/evolution/run.py
    
Example Session:
    Evolution Agent (S-3) > observe
    Evolution Agent (S-3) > analyze
    Evolution Agent (S-3) > recommend
    Evolution Agent (S-3) > exit

All outputs are logged and saved to memory.
"""

import sys
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from agents.evolution.evolution_agent import EvolutionAgent


class EvolutionCLI:
    """Command-line interface for Evolution Agent."""
    
    PROMPT = "Evolution Agent (S-3) > "
    
    COMMANDS = {
        "observe": "Take a system snapshot",
        "analyze": "Analyze the last observation (or run observe first)",
        "recommend": "Generate recommendations from analysis",
        "cycle": "Run full observe → analyze → recommend cycle",
        "status": "Show agent status",
        "health": "Show health report",
        "history": "Show recent agent history",
        "help": "Show available commands",
        "exit": "Exit the CLI",
        "quit": "Exit the CLI"
    }
    
    def __init__(self, agent_id: Optional[str] = None, log_level: int = logging.INFO):
        """Initialize CLI with Evolution Agent."""
        self.agent = EvolutionAgent(agent_id=agent_id, log_level=log_level)
        self._running = True
        
        # Ensure logs directory exists
        logs_dir = project_root / "logs"
        logs_dir.mkdir(exist_ok=True)
        
        print("\n" + "=" * 60)
        print("  Evolution Agent (S-3) - Arcyn OS System Monitor")
        print("  Advisory-Only Mode: Observes -> Analyzes -> Recommends")
        print("=" * 60)
        print(f"  Agent ID: {self.agent.agent_id}")
        print(f"  Status: Ready")
        print("  Type 'help' for available commands")
        print("=" * 60 + "\n")
    
    def run(self):
        """Run the interactive CLI loop."""
        while self._running:
            try:
                command = input(self.PROMPT).strip().lower()
                if command:
                    self._handle_command(command)
            except KeyboardInterrupt:
                print("\n\nInterrupted. Type 'exit' to quit.\n")
            except EOFError:
                print("\nExiting...")
                break
    
    def _handle_command(self, command: str):
        """Handle a CLI command."""
        parts = command.split()
        cmd = parts[0]
        args = parts[1:]
        
        if cmd in ("exit", "quit"):
            self._cmd_exit()
        elif cmd == "help":
            self._cmd_help()
        elif cmd == "observe":
            self._cmd_observe()
        elif cmd == "analyze":
            self._cmd_analyze()
        elif cmd == "recommend":
            self._cmd_recommend()
        elif cmd == "cycle":
            self._cmd_cycle()
        elif cmd == "status":
            self._cmd_status()
        elif cmd == "health":
            self._cmd_health()
        elif cmd == "history":
            limit = int(args[0]) if args else 10
            self._cmd_history(limit)
        else:
            print(f"Unknown command: {cmd}. Type 'help' for available commands.\n")
    
    def _cmd_help(self):
        """Show help information."""
        print("\nAvailable Commands:")
        print("-" * 40)
        for cmd, desc in self.COMMANDS.items():
            print(f"  {cmd:<12} - {desc}")
        print()
    
    def _cmd_exit(self):
        """Exit the CLI."""
        print("\nEvolution Agent (S-3) shutting down...")
        print("All observations and recommendations have been saved.\n")
        self._running = False
    
    def _cmd_observe(self):
        """Run observation phase."""
        print("\n[OBSERVE] Taking system snapshot...")
        try:
            result = self.agent.observe()
            self._print_observation_summary(result)
            self._save_output("observe", result)
        except Exception as e:
            print(f"[ERROR] Observation failed: {e}\n")
    
    def _cmd_analyze(self):
        """Run analysis phase."""
        print("\n[ANALYZE] Analyzing observations...")
        try:
            result = self.agent.analyze()
            self._print_analysis_summary(result)
            self._save_output("analyze", result)
        except ValueError as e:
            print(f"[ERROR] {e}")
            print("Hint: Run 'observe' first to collect system data.\n")
        except Exception as e:
            print(f"[ERROR] Analysis failed: {e}\n")
    
    def _cmd_recommend(self):
        """Run recommendation phase."""
        print("\n[RECOMMEND] Generating recommendations...")
        try:
            result = self.agent.recommend()
            self._print_recommendation_summary(result)
            self._save_output("recommend", result)
        except ValueError as e:
            print(f"[ERROR] {e}")
            print("Hint: Run 'analyze' first to analyze observations.\n")
        except Exception as e:
            print(f"[ERROR] Recommendation failed: {e}\n")
    
    def _cmd_cycle(self):
        """Run full observation → analysis → recommendation cycle."""
        print("\n[CYCLE] Running full evolution cycle...")
        print("-" * 40)
        try:
            result = self.agent.run_full_cycle()
            
            print("\n--- Observation Summary ---")
            self._print_observation_summary(result["observation"])
            
            print("--- Analysis Summary ---")
            self._print_analysis_summary(result["analysis"])
            
            print("--- Recommendation Summary ---")
            self._print_recommendation_summary(result["recommendations"])
            
            print("--- Health Score ---")
            health = result.get("health_score", {})
            print(f"  Overall Score: {health.get('overall_score', 0):.1%}")
            print(f"  Status: {health.get('overall_status', 'unknown')}")
            print()
            
            self._save_output("cycle", result)
        except Exception as e:
            print(f"[ERROR] Cycle failed: {e}\n")
    
    def _cmd_status(self):
        """Show agent status."""
        print("\n[STATUS] Agent Status")
        print("-" * 40)
        status = self.agent.get_status()
        print(f"  Agent ID: {status['agent_id']}")
        print(f"  Designation: {status['designation']}")
        print(f"  State: {status['state']}")
        print(f"  Has Observation: {status['has_observation']}")
        print(f"  Has Analysis: {status['has_analysis']}")
        print(f"  Has Recommendations: {status['has_recommendations']}")
        
        health = status.get('health_score', {})
        print(f"  Health Score: {health.get('overall_score', 0):.1%}")
        print(f"  Health Status: {health.get('overall_status', 'unknown')}")
        print()
    
    def _cmd_health(self):
        """Show health report."""
        print("\n[HEALTH] System Health Report")
        print("-" * 40)
        report = self.agent.get_health_report()
        
        score = report.get("health_score", {})
        print(f"  Overall Score: {score.get('overall_score', 0):.1%}")
        print(f"  Status: {score.get('overall_status', 'unknown')}")
        print(f"  Trend: {score.get('trend_summary', 'No data')}")
        
        if score.get("critical_issues"):
            print(f"\n  Critical Issues ({len(score['critical_issues'])}):")
            for issue in score["critical_issues"][:5]:
                print(f"    - {issue.get('indicator')}: {issue.get('value')}")
        
        if score.get("warnings"):
            print(f"\n  Warnings ({len(score['warnings'])}):")
            for warn in score["warnings"][:5]:
                print(f"    - {warn.get('indicator')}: {warn.get('value')}")
        print()
    
    def _cmd_history(self, limit: int = 10):
        """Show agent history."""
        print(f"\n[HISTORY] Recent Activity (last {limit})")
        print("-" * 40)
        context = self.agent.context.get_context()
        history = context.get("history", [])[-limit:]
        
        if not history:
            print("  No history recorded yet.")
        else:
            for entry in reversed(history):
                ts = entry.get("timestamp", "")[:19]  # Truncate to seconds
                event = entry.get("event", "unknown")
                print(f"  [{ts}] {event}")
        print()
    
    def _print_observation_summary(self, result: dict):
        """Print observation summary."""
        agents = result.get("agents", {})
        metrics = result.get("metrics", {})
        warnings = result.get("warnings", [])
        errors = result.get("errors", [])
        
        print(f"  Agents Observed: {len(agents)}")
        print(f"  Active Agents: {metrics.get('active_agents', 0)}")
        print(f"  Total Executions: {metrics.get('total_executions', 0)}")
        print(f"  Overall Failure Rate: {metrics.get('overall_failure_rate', 0):.1%}")
        
        if warnings:
            print(f"  Warnings: {len(warnings)}")
        if errors:
            print(f"  Errors: {len(errors)}")
        print()
    
    def _print_analysis_summary(self, result: dict):
        """Print analysis summary."""
        summary = result.get("summary", {})
        issues = result.get("issues", [])
        
        print(f"  Total Issues: {summary.get('total_issues', 0)}")
        print(f"  System Health: {summary.get('health', 'unknown')}")
        print(f"  Bottlenecks: {summary.get('bottlenecks', 0)}")
        print(f"  Tech Debt Items: {summary.get('debt_items', 0)}")
        
        by_severity = summary.get("by_severity", {})
        if by_severity:
            print(f"  By Severity: ", end="")
            parts = [f"{k}={v}" for k, v in by_severity.items()]
            print(", ".join(parts))
        
        # Show top 3 issues
        if issues:
            print("\n  Top Issues:")
            for issue in issues[:3]:
                print(f"    - [{issue.get('severity', '?')}] {issue.get('title', 'Unknown')}")
        print()
    
    def _print_recommendation_summary(self, result: dict):
        """Print recommendation summary."""
        summary = result.get("summary", {})
        recs = result.get("recommendations", [])
        
        print(f"  Total Recommendations: {summary.get('total_recommendations', 0)}")
        print(f"  Overall Priority: {result.get('priority', 'unknown')}")
        print(f"  Confidence: {result.get('confidence', 0):.0%}")
        print(f"  Quick Wins Available: {summary.get('quick_wins', 0)}")
        print(f"  High Risk Items: {summary.get('high_risk_count', 0)}")
        
        by_type = summary.get("by_type", {})
        if by_type:
            print(f"  By Type: ", end="")
            parts = [f"{k}={v}" for k, v in by_type.items()]
            print(", ".join(parts))
        
        # Show top 3 recommendations
        if recs:
            print("\n  Top Recommendations:")
            for rec in recs[:3]:
                print(f"    - [{rec.get('priority', '?')}] {rec.get('title', 'Unknown')}")
                print(f"      Effort: {rec.get('effort', '?')}, Risk: {rec.get('risk', '?')}")
        print()
    
    def _save_output(self, command: str, result: dict):
        """Save command output to file."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"evolution_{command}_{timestamp}.json"
        output_path = project_root / "logs" / filename
        
        try:
            with open(output_path, 'w') as f:
                json.dump(result, f, indent=2, default=str)
            print(f"[SAVED] Output saved to: logs/{filename}\n")
        except Exception as e:
            print(f"[WARNING] Could not save output: {e}\n")


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Evolution Agent (S-3) - System Monitor CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Commands:
  observe     - Take a system snapshot
  analyze     - Analyze observations
  recommend   - Generate recommendations
  cycle       - Run full observe → analyze → recommend cycle
  status      - Show agent status
  health      - Show health report
  help        - Show available commands
  exit        - Exit the CLI

Example:
  python agents/evolution/run.py
  Evolution Agent (S-3) > observe
  Evolution Agent (S-3) > analyze
  Evolution Agent (S-3) > recommend
        """
    )
    
    parser.add_argument(
        '--agent-id',
        type=str,
        default=None,
        help='Custom agent ID (default: evolution_agent_S-3)'
    )
    
    parser.add_argument(
        '--log-level',
        type=int,
        default=20,
        choices=[10, 20, 30, 40, 50],
        help='Logging level: 10=DEBUG, 20=INFO, 30=WARNING (default: 20)'
    )
    
    parser.add_argument(
        '--command',
        type=str,
        choices=['observe', 'analyze', 'recommend', 'cycle', 'status', 'health'],
        help='Run a single command and exit (non-interactive mode)'
    )
    
    args = parser.parse_args()
    
    cli = EvolutionCLI(agent_id=args.agent_id, log_level=args.log_level)
    
    if args.command:
        # Non-interactive mode: run single command
        cli._handle_command(args.command)
    else:
        # Interactive mode
        cli.run()


if __name__ == '__main__':
    main()
