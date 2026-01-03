"""
Schema Generator module for System Designer Agent.

Generates API schemas, agent-to-agent message contracts, data object definitions, and memory models.
"""

from typing import Dict, Any, List, Optional
import json


class SchemaGenerator:
    """
    Generates schemas and contracts for Arcyn OS.
    
    Generates:
    - API schemas
    - Agent-to-agent message contracts
    - Data object definitions
    - Memory models
    
    Output formats: JSON schemas, YAML (optional), Markdown documentation
    
    TODO: Add JSON Schema validation
    TODO: Generate OpenAPI/Swagger specs
    TODO: Add YAML export support
    TODO: Generate TypeScript type definitions
    TODO: Integrate with runtime validation
    """
    
    def __init__(self):
        """Initialize the schema generator."""
        pass
    
    def generate_api_schema(self, api_name: str, endpoints: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate API schema for a service or module.
        
        Args:
            api_name: Name of the API
            endpoints: List of endpoint definitions, each with:
                - name: Endpoint name
                - method: HTTP method or action type
                - input: Input schema
                - output: Output schema
                - description: Endpoint description
        
        Returns:
            Complete API schema dictionary
        """
        schema = {
            "api_name": api_name,
            "version": "1.0.0",
            "description": f"API schema for {api_name}",
            "endpoints": []
        }
        
        for endpoint in endpoints:
            endpoint_schema = {
                "name": endpoint.get("name"),
                "method": endpoint.get("method", "POST"),
                "description": endpoint.get("description", ""),
                "input": self._normalize_schema(endpoint.get("input", {})),
                "output": self._normalize_schema(endpoint.get("output", {})),
                "errors": endpoint.get("errors", [])
            }
            schema["endpoints"].append(endpoint_schema)
        
        return schema
    
    def generate_agent_contract(self, agent_name: str, capabilities: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate agent-to-agent message contract.
        
        Args:
            agent_name: Name of the agent
            capabilities: List of capabilities, each with:
                - action: Action name
                - input_schema: Input message schema
                - output_schema: Output message schema
                - description: Capability description
        
        Returns:
            Agent contract dictionary
        """
        contract = {
            "agent_name": agent_name,
            "version": "1.0.0",
            "message_format": {
                "type": "JSON",
                "required_fields": ["action", "agent_id", "timestamp", "data"],
                "optional_fields": ["context", "metadata"]
            },
            "capabilities": []
        }
        
        for capability in capabilities:
            cap_schema = {
                "action": capability.get("action"),
                "description": capability.get("description", ""),
                "input": self._normalize_schema(capability.get("input_schema", {})),
                "output": self._normalize_schema(capability.get("output_schema", {})),
                "errors": capability.get("errors", [])
            }
            contract["capabilities"].append(cap_schema)
        
        return contract
    
    def generate_data_object_schema(self, object_name: str, fields: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate schema for a data object.
        
        Args:
            object_name: Name of the data object
            fields: List of field definitions, each with:
                - name: Field name
                - type: Field type
                - required: Whether field is required
                - description: Field description
                - default: Default value (optional)
        
        Returns:
            Data object schema dictionary
        """
        schema = {
            "object_name": object_name,
            "type": "object",
            "properties": {},
            "required": []
        }
        
        for field in fields:
            field_name = field.get("name")
            field_type = field.get("type", "string")
            is_required = field.get("required", False)
            
            schema["properties"][field_name] = {
                "type": field_type,
                "description": field.get("description", "")
            }
            
            if "default" in field:
                schema["properties"][field_name]["default"] = field["default"]
            
            if is_required:
                schema["required"].append(field_name)
        
        return schema
    
    def generate_memory_model(self, model_name: str, structure: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate memory model schema.
        
        Args:
            model_name: Name of the memory model
            structure: Structure definition with:
                - keys: Key structure
                - values: Value structure
                - metadata: Metadata structure
                - indexing: Index definitions
        
        Returns:
            Memory model schema dictionary
        """
        model = {
            "model_name": model_name,
            "version": "1.0.0",
            "key_structure": structure.get("keys", {}),
            "value_structure": structure.get("values", {}),
            "metadata_structure": structure.get("metadata", {}),
            "indexing": structure.get("indexing", []),
            "constraints": structure.get("constraints", [])
        }
        
        return model
    
    def _normalize_schema(self, schema: Any) -> Dict[str, Any]:
        """
        Normalize a schema to standard format.
        
        Args:
            schema: Schema in any format
            
        Returns:
            Normalized schema dictionary
        """
        if isinstance(schema, dict):
            return schema
        elif isinstance(schema, list):
            return {
                "type": "array",
                "items": self._normalize_schema(schema[0] if schema else {})
            }
        else:
            return {
                "type": str(schema) if schema else "any",
                "description": ""
            }
    
    def to_json_schema(self, schema: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert schema to JSON Schema format.
        
        Args:
            schema: Schema dictionary
            
        Returns:
            JSON Schema compliant dictionary
        """
        # Basic conversion to JSON Schema format
        json_schema = {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "type": "object",
            "properties": {},
            "required": []
        }
        
        if "properties" in schema:
            json_schema["properties"] = schema["properties"]
            json_schema["required"] = schema.get("required", [])
        
        return json_schema
    
    def to_markdown(self, schema: Dict[str, Any], schema_type: str = "api") -> str:
        """
        Convert schema to Markdown documentation.
        
        Args:
            schema: Schema dictionary
            schema_type: Type of schema (api, contract, object, memory)
            
        Returns:
            Markdown string
        """
        md = []
        
        if schema_type == "api":
            md.append(f"# {schema.get('api_name', 'API')} Schema\n")
            md.append(f"**Version**: {schema.get('version', '1.0.0')}\n")
            md.append(f"**Description**: {schema.get('description', '')}\n\n")
            
            md.append("## Endpoints\n")
            for endpoint in schema.get("endpoints", []):
                md.append(f"### {endpoint.get('name')}\n")
                md.append(f"- **Method**: {endpoint.get('method')}")
                md.append(f"- **Description**: {endpoint.get('description')}\n")
                
                if endpoint.get("input"):
                    md.append("**Input**:")
                    md.append("```json")
                    md.append(json.dumps(endpoint["input"], indent=2))
                    md.append("```\n")
                
                if endpoint.get("output"):
                    md.append("**Output**:")
                    md.append("```json")
                    md.append(json.dumps(endpoint["output"], indent=2))
                    md.append("```\n")
        
        elif schema_type == "contract":
            md.append(f"# {schema.get('agent_name', 'Agent')} Contract\n")
            md.append(f"**Version**: {schema.get('version', '1.0.0')}\n\n")
            
            md.append("## Message Format\n")
            msg_format = schema.get("message_format", {})
            md.append(f"- **Type**: {msg_format.get('type')}")
            md.append(f"- **Required Fields**: {', '.join(msg_format.get('required_fields', []))}\n")
            
            md.append("## Capabilities\n")
            for cap in schema.get("capabilities", []):
                md.append(f"### {cap.get('action')}\n")
                md.append(f"{cap.get('description')}\n")
        
        elif schema_type == "object":
            md.append(f"# {schema.get('object_name', 'Object')} Schema\n")
            md.append("## Properties\n")
            for prop_name, prop_def in schema.get("properties", {}).items():
                md.append(f"- **{prop_name}** ({prop_def.get('type', 'unknown')}): {prop_def.get('description', '')}")
                if prop_name in schema.get("required", []):
                    md.append(" *(required)*")
                md.append("\n")
        
        elif schema_type == "memory":
            md.append(f"# {schema.get('model_name', 'Memory')} Model\n")
            md.append(f"**Version**: {schema.get('version', '1.0.0')}\n\n")
            
            md.append("## Structure\n")
            md.append("### Keys\n")
            md.append("```json")
            md.append(json.dumps(schema.get("key_structure", {}), indent=2))
            md.append("```\n")
            
            md.append("### Values\n")
            md.append("```json")
            md.append(json.dumps(schema.get("value_structure", {}), indent=2))
            md.append("```\n")
        
        return "\n".join(md)

