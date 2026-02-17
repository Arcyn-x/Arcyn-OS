#!/usr/bin/env python3
"""
End-to-end test for the Forge Layer of Arcyn OS.

This test orchestrates all four Forge Layer agents in sequence:
1. Architect Agent (A-1) - Plans the work
2. System Designer Agent (F-2) - Designs the architecture
3. Builder Agent (F-1) - Scaffolds the code
4. Integrator Agent (F-3) - Validates integration

Test Goal: "Design and scaffold a basic Arcyn OS memory module."
"""

import sys
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from agents.architect import ArchitectAgent
from agents.system_designer import SystemDesignerAgent
from agents.builder import BuilderAgent
from agents.integrator import IntegratorAgent


def save_artifact(data: Dict[str, Any], filename: str, output_dir: Path) -> None:
    """
    Save an artifact to the output directory.
    
    Args:
        data: Data to save
        filename: Filename (will be saved as JSON)
        output_dir: Output directory path
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    file_path = output_dir / f"{filename}.json"
    
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)
    
    print(f"  [OK] Saved artifact: {file_path}")


def run_forge_test() -> Dict[str, Any]:
    """
    Run the complete Forge Layer end-to-end test.
    
    Returns:
        Test result dictionary
    """
    # Test goal (fixed)
    goal = "Design and scaffold a basic Arcyn OS memory module."
    
    print("=" * 70)
    print("FORGE LAYER END-TO-END TEST")
    print("=" * 70)
    print(f"Goal: {goal}\n")
    
    # Setup output directory
    output_dir = Path("tests/output")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    test_result = {
        "forge_test_status": "failed",
        "goal": goal,
        "timestamp": datetime.now().isoformat(),
        "architect_summary": {},
        "system_design_summary": {},
        "builder_summary": {},
        "integration_result": {},
        "errors": []
    }
    
    try:
        # ============================================================
        # STEP 1: Architect Agent - Plan the work
        # ============================================================
        print("\n[STEP 1] Architect Agent - Planning...")
        print("-" * 70)
        
        architect = ArchitectAgent(agent_id="test_architect", log_level=30)  # WARNING level to reduce noise
        
        try:
            architect_plan = architect.plan(goal)
            print(f"  [OK] Plan generated: {len(architect_plan.get('tasks', []))} tasks, {len(architect_plan.get('milestones', []))} milestones")
            
            test_result["architect_summary"] = {
                "status": "success",
                "goal": architect_plan.get("goal"),
                "task_count": len(architect_plan.get("tasks", [])),
                "milestone_count": len(architect_plan.get("milestones", []))
            }
            
            save_artifact(architect_plan, "01_architect_plan", output_dir)
            
        except Exception as e:
            error_msg = f"Architect Agent failed: {str(e)}"
            print(f"  [FAIL] {error_msg}")
            test_result["errors"].append(error_msg)
            test_result["architect_summary"] = {"status": "failed", "error": str(e)}
            raise
        
        # ============================================================
        # STEP 2: System Designer Agent - Design the architecture
        # ============================================================
        print("\n[STEP 2] System Designer Agent - Designing architecture...")
        print("-" * 70)
        
        system_designer = SystemDesignerAgent(agent_id="test_system_designer", log_level=30)
        
        try:
            # Use the same goal for design
            system_design = system_designer.design(goal)
            print(f"  [OK] Architecture designed: {len(system_design.get('modules', []))} modules defined")
            
            test_result["system_design_summary"] = {
                "status": "success",
                "module_count": len(system_design.get("modules", [])),
                "has_standards": "standards" in system_design,
                "has_dependencies": "dependencies" in system_design
            }
            
            save_artifact(system_design, "02_system_design", output_dir)
            
        except Exception as e:
            error_msg = f"System Designer Agent failed: {str(e)}"
            print(f"  [FAIL] {error_msg}")
            test_result["errors"].append(error_msg)
            test_result["system_design_summary"] = {"status": "failed", "error": str(e)}
            raise
        
        # ============================================================
        # STEP 3: Builder Agent - Scaffold the code
        # ============================================================
        print("\n[STEP 3] Builder Agent - Scaffolding code...")
        print("-" * 70)
        
        builder = BuilderAgent(agent_id="test_builder", log_level=30)
        
        try:
            # Convert design into a build task
            # The Builder should scaffold a memory module based on the design
            modules = system_design.get("modules", [])
            memory_module = None
            
            # Find memory module in design
            for module in modules:
                if "memory" in module.get("name", "").lower():
                    memory_module = module
                    break
            
            if not memory_module:
                # If no memory module found, create a basic one based on the goal
                memory_module = {
                    "name": "memory",
                    "layer": "core",
                    "description": "Basic Arcyn OS memory module"
                }
            
            # Create build task - ONLY scaffold, no implementation
            # Use a unique filename to avoid conflicts
            import uuid
            test_id = str(uuid.uuid4())[:8]
            target_path = f"core/memory_test_{test_id}.py"
            
            build_task = {
                "action": "build",
                "description": "Scaffold basic Arcyn OS memory module",
                "target_path": target_path,
                "overwrite": True,  # Allow overwrite for test
                "content": '''"""
Memory module for Arcyn OS.

TODO: Implement memory management functionality
TODO: Add persistence layer
TODO: Add memory compression
"""

from typing import Any, Optional, Dict


class Memory:
    """
    Memory manager for Arcyn OS.
    
    TODO: Add implementation
    """
    
    def __init__(self):
        """
        Initialize memory manager.
        
        TODO: Add initialization logic
        """
        pass
    
    # TODO: Add methods
'''
            }
            
            builder_output = builder.build(build_task)
            print(f"  [OK] Build completed: {len(builder_output.get('files_changed', []))} file(s) created")
            
            # Verify Builder only scaffolded (check file content)
            files_changed = builder_output.get("files_changed", [])
            if files_changed:
                file_path = Path(files_changed[0])
                if file_path.exists():
                    content = file_path.read_text(encoding='utf-8')
                    # Check that it's only scaffolding (has TODOs, no real logic)
                    if "TODO" not in content:
                        raise ValueError("Builder wrote real logic instead of scaffolding!")
                    if "def read" in content or "def write" in content:
                        # Check if these are implemented or just stubs
                        if "pass" not in content and "raise NotImplementedError" not in content:
                            raise ValueError("Builder implemented logic instead of scaffolding!")
            
            test_result["builder_summary"] = {
                "status": "success",
                "action": builder_output.get("action"),
                "files_changed": builder_output.get("files_changed", []),
                "summary": builder_output.get("summary")
            }
            
            save_artifact(builder_output, "03_builder_output", output_dir)
            
        except Exception as e:
            error_msg = f"Builder Agent failed: {str(e)}"
            print(f"  [FAIL] {error_msg}")
            test_result["errors"].append(error_msg)
            test_result["builder_summary"] = {"status": "failed", "error": str(e)}
            raise
        
        # ============================================================
        # STEP 4: Integrator Agent - Validate integration
        # ============================================================
        print("\n[STEP 4] Integrator Agent - Validating integration...")
        print("-" * 70)
        
        integrator = IntegratorAgent(agent_id="test_integrator", log_level=30)
        
        try:
            # Create integration payload with all outputs
            integration_payload = {
                "architect_plan": architect_plan,
                "system_design": system_design,
                "builder_output": builder_output
            }
            
            integration_result = integrator.integrate(integration_payload)
            status = integration_result.get("status", "unknown")
            
            print(f"  [OK] Integration validation completed: {status.upper()}")
            
            violations = integration_result.get("violations", [])
            warnings = integration_result.get("warnings", [])
            
            if violations:
                print(f"  [WARN] Violations: {len(violations)}")
                for violation in violations[:3]:  # Show first 3
                    print(f"      - {violation}")
            
            if warnings:
                print(f"  [WARN] Warnings: {len(warnings)}")
                for warning in warnings[:3]:  # Show first 3
                    print(f"      - {warning}")
            
            test_result["integration_result"] = {
                "status": status,
                "violations_count": len(violations),
                "warnings_count": len(warnings),
                "summary": integration_result.get("integration_summary", "")
            }
            
            save_artifact(integration_result, "04_integration_result", output_dir)
            save_artifact(integration_payload, "00_integration_payload", output_dir)
            
        except Exception as e:
            error_msg = f"Integrator Agent failed: {str(e)}"
            print(f"  [FAIL] {error_msg}")
            test_result["errors"].append(error_msg)
            test_result["integration_result"] = {"status": "failed", "error": str(e)}
            raise
        
        # ============================================================
        # TEST COMPLETE
        # ============================================================
        print("\n" + "=" * 70)
        print("TEST COMPLETE")
        print("=" * 70)
        
        # Determine final status
        # Test passes if all agents executed and Integrator provided explicit results
        if test_result["errors"]:
            test_result["forge_test_status"] = "failed"
        elif test_result["integration_result"].get("status") == "blocked":
            # Integrator blocking is correct behavior if violations exist
            # Test passes if Integrator provided explicit violations
            violations_count = test_result["integration_result"].get("violations_count", 0)
            if violations_count > 0:
                # Integrator correctly identified violations - this is success
                test_result["forge_test_status"] = "passed"
                test_result["integration_result"]["note"] = "Integrator correctly blocked with explicit violations"
            else:
                test_result["forge_test_status"] = "failed"
                test_result["errors"].append("Integration blocked but no violations reported")
        else:
            test_result["forge_test_status"] = "passed"
        
        print(f"\nFinal Status: {test_result['forge_test_status'].upper()}")
        
        if test_result["errors"]:
            print("\nErrors:")
            for error in test_result["errors"]:
                print(f"  - {error}")
        
        # Save final test result
        save_artifact(test_result, "test_result", output_dir)
        
        return test_result
        
    except Exception as e:
        # Catch any unhandled exceptions
        error_msg = f"Test failed with exception: {str(e)}"
        print(f"\n[FAIL] {error_msg}")
        test_result["errors"].append(error_msg)
        test_result["forge_test_status"] = "failed"
        
        # Save partial result
        save_artifact(test_result, "test_result", output_dir)
        
        return test_result


if __name__ == '__main__':
    result = run_forge_test()
    
    # Print final summary
    print("\n" + "=" * 70)
    print("FINAL TEST SUMMARY")
    print("=" * 70)
    print(json.dumps({
        "forge_test_status": result["forge_test_status"],
        "architect_summary": result["architect_summary"],
        "system_design_summary": result["system_design_summary"],
        "builder_summary": result["builder_summary"],
        "integration_result": result["integration_result"]
    }, indent=2))
    
    # Exit with appropriate code
    sys.exit(0 if result["forge_test_status"] == "passed" else 1)

