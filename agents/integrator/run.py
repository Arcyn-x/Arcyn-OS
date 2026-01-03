#!/usr/bin/env python3
"""
Minimal executable runner for Integrator Agent (F-3).

This script provides a command-line interface to the Integrator Agent,
allowing you to validate and integrate outputs from other agents.

Usage:
    python agents/integrator/run.py integration_payload.json
    python agents/integrator/run.py integration_payload.json --export
    python agents/integrator/run.py integration_payload.json --pretty
"""

import sys
import json
import argparse
from pathlib import Path
from typing import Dict, Any

# Add project root to path for imports when running as script
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from agents.integrator.integrator_agent import IntegratorAgent


def load_payload(payload_path: str) -> Dict[str, Any]:
    """
    Load integration payload from JSON file.
    
    Args:
        payload_path: Path to payload JSON file
        
    Returns:
        Payload dictionary
        
    Raises:
        FileNotFoundError: If payload file doesn't exist
        json.JSONDecodeError: If JSON is invalid
    """
    payload_file = Path(payload_path)
    
    if not payload_file.exists():
        raise FileNotFoundError(f"Payload file not found: {payload_path}")
    
    with open(payload_file, 'r', encoding='utf-8') as f:
        payload = json.load(f)
    
    return payload


def main():
    """Main entry point for the Integrator Agent runner."""
    parser = argparse.ArgumentParser(
        description="Integrator Agent (F-3) - Validate and integrate agent outputs",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python agents/integrator/run.py integration_payload.json
  python agents/integrator/run.py payload.json --export --pretty
  python agents/integrator/run.py payload.json --output integration/

Example payload.json structure:
  {
    "architect_plan": {...},
    "system_design": {...},
    "builder_output": {...}
  }
        """
    )
    
    parser.add_argument(
        'payload_file',
        type=str,
        help='Path to integration payload JSON file'
    )
    
    parser.add_argument(
        '--agent-id',
        type=str,
        default='integrator_agent',
        help='Unique identifier for the agent instance (default: integrator_agent)'
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
        default='integration',
        help='Output directory for integration reports (default: integration/)'
    )
    
    parser.add_argument(
        '--pretty',
        action='store_true',
        help='Pretty-print JSON output with indentation'
    )
    
    parser.add_argument(
        '--export',
        action='store_true',
        help='Export integration report to files'
    )
    
    args = parser.parse_args()
    
    # Load payload
    try:
        payload = load_payload(args.payload_file)
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in payload file: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: Failed to load payload file: {e}", file=sys.stderr)
        sys.exit(1)
    
    # Initialize the agent
    try:
        agent = IntegratorAgent(agent_id=args.agent_id, log_level=args.log_level)
    except Exception as e:
        print(f"Error: Failed to initialize Integrator Agent: {e}", file=sys.stderr)
        sys.exit(1)
    
    # Run integration
    try:
        result = agent.integrate(payload)
    except Exception as e:
        print(f"Error: Failed to run integration: {e}", file=sys.stderr)
        sys.exit(1)
    
    # Export report if requested
    if args.export:
        try:
            output_path = Path(args.output)
            output_path.mkdir(parents=True, exist_ok=True)
            
            # Generate report
            report = agent.report_generator.generate_report(result)
            
            # Export JSON report
            json_path = output_path / "integration_report.json"
            with open(json_path, 'w') as f:
                json.dump(report, f, indent=2)
            
            # Export Markdown report
            md_path = output_path / "integration_report.md"
            md_content = agent.report_generator.to_markdown(report)
            with open(md_path, 'w') as f:
                f.write(md_content)
            
            result["exported_reports"] = {
                "directory": str(output_path),
                "files": [str(json_path), str(md_path)]
            }
        except Exception as e:
            print(f"Warning: Failed to export reports: {e}", file=sys.stderr)
    
    # Output result as JSON
    try:
        if args.pretty:
            json_output = json.dumps(result, indent=2, ensure_ascii=False)
        else:
            json_output = json.dumps(result, ensure_ascii=False)
        
        print(json_output)
        
        # Exit with error code if blocked
        if result.get("status") == "blocked":
            sys.exit(1)
        
    except Exception as e:
        print(f"Error: Failed to serialize result: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()

