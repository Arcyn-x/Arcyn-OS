"""
Contract Validator module for Integrator Agent.

Validates agent-to-agent message contracts, ensures schemas from System Designer Agent
are respected, and detects missing or malformed fields.
"""

from typing import Dict, Any, List, Tuple, Optional


class ContractValidator:
    """
    Validates contracts and schemas.
    
    Responsibilities:
    - Validate agent-to-agent message contracts
    - Ensure schemas from F-2 are respected
    - Detect missing or malformed fields
    
    Input: Task plans, design schemas, build outputs
    Output: Pass/fail with reasons
    
    TODO: Add JSON Schema validation
    TODO: Implement schema version compatibility checking
    TODO: Add contract evolution tracking
    TODO: Integrate with runtime contract validation
    """
    
    def __init__(self):
        """Initialize the contract validator."""
        self.required_fields = {
            "architect_plan": ["goal", "milestones", "tasks", "task_graph"],
            "system_design": ["architecture", "modules", "standards", "dependencies"],
            "builder_output": ["action", "files_changed", "summary"]
        }
    
    def validate_architect_plan(self, plan: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Validate an Architect Agent plan output.
        
        Args:
            plan: Plan dictionary from Architect Agent
        
        Returns:
            Tuple of (is_valid: bool, errors: List[str])
        """
        errors = []
        
        # Check required fields
        for field in self.required_fields["architect_plan"]:
            if field not in plan:
                errors.append(f"Missing required field: {field}")
        
        # Validate milestones structure
        milestones = plan.get("milestones", [])
        if not isinstance(milestones, list):
            errors.append("Milestones must be a list")
        else:
            for i, milestone in enumerate(milestones):
                if not isinstance(milestone, dict):
                    errors.append(f"Milestone {i} must be a dictionary")
                else:
                    if "id" not in milestone:
                        errors.append(f"Milestone {i} missing 'id' field")
                    if "name" not in milestone:
                        errors.append(f"Milestone {i} missing 'name' field")
        
        # Validate tasks structure
        tasks = plan.get("tasks", [])
        if not isinstance(tasks, list):
            errors.append("Tasks must be a list")
        else:
            for i, task in enumerate(tasks):
                if not isinstance(task, dict):
                    errors.append(f"Task {i} must be a dictionary")
                else:
                    if "id" not in task:
                        errors.append(f"Task {i} missing 'id' field")
                    if "name" not in task:
                        errors.append(f"Task {i} missing 'name' field")
        
        # Validate task_graph
        task_graph = plan.get("task_graph", {})
        if task_graph:
            if "nodes" not in task_graph:
                errors.append("Task graph missing 'nodes' field")
            if "edges" not in task_graph:
                errors.append("Task graph missing 'edges' field")
        
        return len(errors) == 0, errors
    
    def validate_system_design(self, design: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Validate a System Designer Agent architecture output.
        
        Args:
            design: Design dictionary from System Designer Agent
        
        Returns:
            Tuple of (is_valid: bool, errors: List[str])
        """
        errors = []
        
        # Check required fields
        for field in self.required_fields["system_design"]:
            if field not in design:
                errors.append(f"Missing required field: {field}")
        
        # Validate architecture structure
        architecture = design.get("architecture", {})
        if architecture:
            if "goal" not in architecture:
                errors.append("Architecture missing 'goal' field")
            if "layers" not in architecture:
                errors.append("Architecture missing 'layers' field")
            elif not isinstance(architecture["layers"], dict):
                errors.append("Architecture 'layers' must be a dictionary")
        
        # Validate modules structure
        modules = design.get("modules", [])
        if not isinstance(modules, list):
            errors.append("Modules must be a list")
        else:
            for i, module in enumerate(modules):
                if not isinstance(module, dict):
                    errors.append(f"Module {i} must be a dictionary")
                else:
                    if "name" not in module:
                        errors.append(f"Module {i} missing 'name' field")
                    if "layer" not in module:
                        errors.append(f"Module {i} missing 'layer' field")
        
        # Validate standards structure
        standards = design.get("standards", {})
        if not isinstance(standards, dict):
            errors.append("Standards must be a dictionary")
        
        # Validate dependencies structure
        dependencies = design.get("dependencies", {})
        if dependencies and not isinstance(dependencies, dict):
            errors.append("Dependencies must be a dictionary")
        
        return len(errors) == 0, errors
    
    def validate_builder_output(self, output: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Validate a Builder Agent output.
        
        Args:
            output: Output dictionary from Builder Agent
        
        Returns:
            Tuple of (is_valid: bool, errors: List[str])
        """
        errors = []
        
        # Check required fields
        for field in self.required_fields["builder_output"]:
            if field not in output:
                errors.append(f"Missing required field: {field}")
        
        # Validate action
        action = output.get("action")
        if action not in ["build", "modify", "refactor"]:
            errors.append(f"Invalid action: {action}. Must be 'build', 'modify', or 'refactor'")
        
        # Validate files_changed
        files_changed = output.get("files_changed", [])
        if not isinstance(files_changed, list):
            errors.append("files_changed must be a list")
        
        # Validate summary
        summary = output.get("summary", "")
        if not isinstance(summary, str):
            errors.append("summary must be a string")
        
        return len(errors) == 0, errors
    
    def validate_message_contract(self, message: Dict[str, Any], contract: Optional[Dict[str, Any]] = None) -> Tuple[bool, List[str]]:
        """
        Validate a message against a contract.
        
        Args:
            message: Message to validate
            contract: Optional contract definition (uses default if None)
        
        Returns:
            Tuple of (is_valid: bool, errors: List[str])
        """
        errors = []
        
        # Default contract requirements
        required_fields = ["action", "agent_id", "timestamp", "data"]
        
        if contract:
            required_fields = contract.get("required_fields", required_fields)
        
        # Check required fields
        for field in required_fields:
            if field not in message:
                errors.append(f"Message missing required field: {field}")
        
        # Validate field types
        if "action" in message and not isinstance(message["action"], str):
            errors.append("'action' field must be a string")
        
        if "agent_id" in message and not isinstance(message["agent_id"], str):
            errors.append("'agent_id' field must be a string")
        
        if "timestamp" in message and not isinstance(message["timestamp"], str):
            errors.append("'timestamp' field must be a string")
        
        if "data" in message and not isinstance(message["data"], dict):
            errors.append("'data' field must be a dictionary")
        
        return len(errors) == 0, errors
    
    def validate_schema_compliance(self, data: Dict[str, Any], schema: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Validate data against a schema definition.
        
        Args:
            data: Data to validate
            schema: Schema definition
        
        Returns:
            Tuple of (is_valid: bool, errors: List[str])
        """
        errors = []
        
        # Basic schema validation
        if "properties" in schema:
            required = schema.get("required", [])
            
            for field in required:
                if field not in data:
                    errors.append(f"Missing required field: {field}")
            
            for field_name, field_schema in schema["properties"].items():
                if field_name in data:
                    field_type = field_schema.get("type")
                    value = data[field_name]
                    
                    # Type checking
                    if field_type == "string" and not isinstance(value, str):
                        errors.append(f"Field '{field_name}' must be a string")
                    elif field_type == "integer" and not isinstance(value, int):
                        errors.append(f"Field '{field_name}' must be an integer")
                    elif field_type == "boolean" and not isinstance(value, bool):
                        errors.append(f"Field '{field_name}' must be a boolean")
                    elif field_type == "object" and not isinstance(value, dict):
                        errors.append(f"Field '{field_name}' must be an object")
                    elif field_type == "array" and not isinstance(value, list):
                        errors.append(f"Field '{field_name}' must be an array")
        
        return len(errors) == 0, errors
    
    def validate_payload(self, payload: Dict[str, Any]) -> Tuple[bool, List[str], Dict[str, Any]]:
        """
        Validate a complete integration payload.
        
        Args:
            payload: Integration payload containing outputs from multiple agents
        
        Returns:
            Tuple of (is_valid: bool, errors: List[str], validation_details: Dict)
        """
        errors = []
        validation_details = {
            "architect_plan_valid": None,
            "system_design_valid": None,
            "builder_output_valid": None,
            "contracts_valid": None
        }
        
        # Validate Architect plan if present
        if "architect_plan" in payload:
            is_valid, plan_errors = self.validate_architect_plan(payload["architect_plan"])
            validation_details["architect_plan_valid"] = is_valid
            if not is_valid:
                errors.extend([f"Architect plan: {e}" for e in plan_errors])
        
        # Validate System Design if present
        if "system_design" in payload:
            is_valid, design_errors = self.validate_system_design(payload["system_design"])
            validation_details["system_design_valid"] = is_valid
            if not is_valid:
                errors.extend([f"System design: {e}" for e in design_errors])
        
        # Validate Builder output if present
        if "builder_output" in payload:
            is_valid, builder_errors = self.validate_builder_output(payload["builder_output"])
            validation_details["builder_output_valid"] = is_valid
            if not is_valid:
                errors.extend([f"Builder output: {e}" for e in builder_errors])
        
        # Validate message contracts if present
        if "messages" in payload:
            messages = payload["messages"]
            if isinstance(messages, list):
                for i, message in enumerate(messages):
                    is_valid, msg_errors = self.validate_message_contract(message)
                    if not is_valid:
                        errors.extend([f"Message {i}: {e}" for e in msg_errors])
                validation_details["contracts_valid"] = len([m for m in messages if self.validate_message_contract(m)[0]]) == len(messages)
        
        return len(errors) == 0, errors, validation_details

