"""
Dispatcher for Arcyn OS Command Trigger.

Routes classified intents to their corresponding generator functions.
Returns complete, copy-paste-ready outputs.

This dispatcher does not think - it routes.

Future Integration Points:
    # TODO: Voice trigger - dispatcher.dispatch(voice_intent)
    # TODO: UI button - dispatcher.dispatch_action(button_id)  
    # TODO: API endpoint - POST /api/dispatch {intent: "...", params: {...}}
"""

from typing import Any, Callable, Dict, Optional
from .intent_router import Intent, IntentMatch


class Dispatcher:
    """
    Intent-to-action dispatcher.
    
    Routes classified intents to generator functions and returns
    complete system outputs. Never returns partial responses.
    
    Example:
        >>> dispatcher = Dispatcher()
        >>> intent_match = IntentMatch(Intent.LOOP_TEST_REQUEST, ...)
        >>> output = dispatcher.dispatch(intent_match)
        >>> print(output)  # Complete, copy-paste-ready prompt
    """
    
    def __init__(self):
        """Initialize dispatcher with route mappings."""
        self._routes: Dict[Intent, Callable[[IntentMatch], str]] = {
            Intent.LOOP_TEST_REQUEST: self._generate_loop_test_prompt,
            Intent.AGENT_PROMPT_REQUEST: self._generate_agent_prompt,
            Intent.SYSTEM_STATUS: self._generate_system_status,
            Intent.ARCHITECTURE_EXPLANATION: self._generate_architecture_explanation,
            Intent.EVOLUTION_CYCLE: self._run_evolution_cycle,
            Intent.HELP_REQUEST: self._generate_help,
            Intent.UNKNOWN_COMMAND: self._handle_unknown,
        }
    
    def dispatch(self, intent_match: IntentMatch) -> str:
        """
        Dispatch an intent to its handler and return output.
        
        Args:
            intent_match: Classified intent with parameters
            
        Returns:
            Complete, copy-paste-ready output string
        """
        handler = self._routes.get(intent_match.intent, self._handle_unknown)
        return handler(intent_match)
    
    def _generate_loop_test_prompt(self, match: IntentMatch) -> str:
        """Generate the full Arcyn OS loop test prompt."""
        return '''# Arcyn OS Full System Loop Test Prompt

You are testing Arcyn OS, an AI-first, multi-agent operating system.

Execute the following loop to verify all agents are functioning correctly.
This test validates the COMPLETE agent pipeline including failure handling.

---

## STEP 1: Persona Agent (S-1) - User Intent Processing

The Persona Agent receives the user's request, classifies intent, and handles ambiguity.

**Input:**
```
User Request: "Build a REST API for task management with authentication"
```

**Expected Output:**
```json
{
  "intent": "BUILD_REQUEST",
  "extracted_params": {
    "type": "REST API",
    "domain": "task management",
    "features": ["authentication"]
  },
  "confidence": 0.92,
  "assumptions": [
    "Authentication means user-based auth, not API keys",
    "Task management implies CRUD operations",
    "REST implies HTTP/JSON, not GraphQL"
  ],
  "missing_info": [
    "Preferred language/framework not specified",
    "Database preference not specified",
    "Auth method (JWT/OAuth/Session) not specified"
  ],
  "risk_flags": [
    {
      "flag": "AMBIGUOUS_SCOPE",
      "detail": "'Task management' could mean simple todos or complex project management",
      "mitigation": "Assuming simple CRUD; escalate if user mentions subtasks/assignments"
    }
  ],
  "clarification_required": false,
  "clarification_prompt": null,
  "route_to": "architect_agent",
  "fallback_route": "persona_agent_clarify"
}
```

**Validation Criteria:**
- [ ] Confidence score is realistic (not always 1.0)
- [ ] Assumptions are explicit and traceable
- [ ] Missing info is flagged for downstream agents
- [ ] Risk flags identify potential misinterpretations

---

## STEP 2: Architect Agent (A-1) - Planning with Tradeoffs

The Architect Agent creates a structured plan WITH explicit decisions and rejected alternatives.

**Input:**
```json
{
  "goal": "Build a REST API for task management with authentication",
  "assumptions": ["User-based auth", "CRUD operations", "HTTP/JSON"],
  "missing_info": ["framework", "database", "auth_method"]
}
```

**Expected Output:**
```json
{
  "goal": "Build a REST API for task management with authentication",
  "decisions": {
    "language": {
      "choice": "Python",
      "reasoning": "Team familiarity, ecosystem maturity, async support"
    },
    "framework": {
      "choice": "FastAPI",
      "reasoning": "Native async, automatic OpenAPI, type hints, performance"
    },
    "auth_method": {
      "choice": "JWT",
      "reasoning": "Stateless, scalable, standard for REST APIs"
    },
    "database": {
      "choice": "PostgreSQL",
      "reasoning": "ACID compliance, JSON support, proven reliability"
    },
    "orm": {
      "choice": "SQLAlchemy",
      "reasoning": "Mature, flexible, async support via encode/databases"
    }
  },
  "rejected_options": [
    {
      "category": "framework",
      "option": "Flask",
      "reason": "Sync-first architecture, less performant for concurrent requests"
    },
    {
      "category": "framework",
      "option": "Django REST",
      "reason": "Heavier footprint, monolithic structure not needed"
    },
    {
      "category": "auth_method",
      "option": "Session-based",
      "reason": "Stateful, harder to scale horizontally"
    },
    {
      "category": "auth_method",
      "option": "OAuth2 only",
      "reason": "Overkill for MVP, can add later as extension"
    },
    {
      "category": "database",
      "option": "MongoDB",
      "reason": "Relational data model fits better for tasks with users"
    }
  ],
  "milestones": [
    {"id": "M1", "name": "Foundation & Auth", "tasks": ["T1", "T2", "T3", "T4"]},
    {"id": "M2", "name": "Core CRUD", "tasks": ["T5", "T6", "T7"]},
    {"id": "M3", "name": "Integration & Polish", "tasks": ["T8", "T9", "T10"]}
  ],
  "tasks": [
    {"id": "T1", "name": "Project scaffolding", "type": "setup", "effort": "low"},
    {"id": "T2", "name": "Database models (User, Task)", "type": "model", "effort": "medium"},
    {"id": "T3", "name": "JWT auth module", "type": "feature", "effort": "medium"},
    {"id": "T4", "name": "Auth middleware", "type": "feature", "effort": "low"},
    {"id": "T5", "name": "Task CRUD endpoints", "type": "feature", "effort": "medium"},
    {"id": "T6", "name": "User registration/login", "type": "feature", "effort": "medium"},
    {"id": "T7", "name": "Input validation (Pydantic)", "type": "feature", "effort": "low"},
    {"id": "T8", "name": "Error handling middleware", "type": "feature", "effort": "low"},
    {"id": "T9", "name": "API documentation", "type": "docs", "effort": "low"},
    {"id": "T10", "name": "Integration tests", "type": "test", "effort": "high"}
  ],
  "execution_order": ["T1", "T2", "T3", "T4", "T6", "T5", "T7", "T8", "T9", "T10"],
  "architectural_constraints": [
    "All endpoints must be async",
    "Auth must be injectable/mockable for testing",
    "Database layer must be abstracted behind repository pattern"
  ],
  "open_questions": [
    "Should we include rate limiting in MVP?",
    "Is email verification required for user registration?"
  ]
}
```

**Validation Criteria:**
- [ ] Decisions include reasoning, not just choices
- [ ] Rejected options show the Architect considered alternatives
- [ ] Constraints are explicit for F-2 to enforce
- [ ] Open questions are surfaced, not hidden

---

## STEP 3A: Forge F-1 (Builder) - Raw Code Generation

F-1 generates the raw implementation WITHOUT architectural validation.

**Input (Task T3):**
```json
{
  "task": "JWT auth module",
  "context": {
    "framework": "FastAPI",
    "decisions": {"auth_method": "JWT"}
  }
}
```

**F-1 Output (Raw Module):**
```python
# auth/jwt_handler.py
from datetime import datetime, timedelta
from typing import Optional
from jose import jwt, JWTError
from passlib.context import CryptContext
from pydantic import BaseModel

# Configuration - TODO: Move to environment
SECRET_KEY = "your-secret-key-here"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class TokenData(BaseModel):
    user_id: Optional[int] = None
    email: Optional[str] = None

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def verify_token(token: str) -> Optional[TokenData]:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        email = payload.get("email")
        if user_id is None:
            return None
        return TokenData(user_id=int(user_id), email=email)
    except JWTError:
        return None

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def hash_password(password: str) -> str:
    return pwd_context.hash(password)
```

**F-1 Metadata:**
```json
{
  "files_generated": ["auth/jwt_handler.py"],
  "dependencies": ["python-jose", "passlib", "bcrypt", "pydantic"],
  "patterns_used": ["token_creation", "password_hashing"],
  "validation_status": "PENDING_F2_REVIEW"
}
```

---

## STEP 3B: Forge F-2 (System Designer) - Architectural Validation

F-2 validates that F-1 output conforms to architectural constraints.

**F-2 Input:**
```json
{
  "code": "<F-1 output>",
  "constraints": [
    "Auth must be injectable/mockable for testing",
    "Database layer must be abstracted"
  ]
}
```

**F-2 Output (Architectural Review):**
```json
{
  "validation_status": "REQUIRES_CHANGES",
  "architectural_compliance": {
    "injectable_auth": {
      "status": "FAIL",
      "issue": "SECRET_KEY is hardcoded, not injectable",
      "fix": "Use dependency injection or config class"
    },
    "testability": {
      "status": "WARN",
      "issue": "No interface abstraction for jwt operations",
      "fix": "Create AuthService protocol/interface"
    },
    "separation_of_concerns": {
      "status": "PASS",
      "note": "Password hashing is separate from token logic"
    }
  },
  "pattern_violations": [
    {
      "pattern": "Configuration Management",
      "violation": "Hardcoded secrets",
      "severity": "HIGH",
      "line": 8
    }
  ],
  "recommended_refactors": [
    {
      "type": "Extract Configuration",
      "description": "Move SECRET_KEY, ALGORITHM, EXPIRE to Settings class",
      "effort": "low"
    },
    {
      "type": "Add Interface",
      "description": "Create AuthServiceProtocol for mockability",
      "effort": "medium"
    }
  ],
  "approval": "CONDITIONAL",
  "conditions": ["Must fix hardcoded secrets before integration"]
}
```

---

## STEP 3C: Forge F-3 (Integrator) - Compatibility & Standards

F-3 validates compatibility with existing modules and enforces standards.

**F-3 Input:**
```json
{
  "new_module": "auth/jwt_handler.py",
  "existing_modules": ["models/user.py", "config/settings.py"],
  "standards": {
    "linting": "ruff",
    "type_hints": "required",
    "test_coverage": "80%"
  }
}
```

**F-3 Output (Integration Report):**
```json
{
  "integration_status": "BLOCKED",
  "blocking_issues": [
    {
      "type": "MISSING_DEPENDENCY",
      "detail": "config/settings.py does not exist but is required for SECRET_KEY",
      "resolution": "Generate config module first OR use environment variables"
    }
  ],
  "compatibility_checks": {
    "import_resolution": "PASS",
    "type_consistency": "PASS",
    "circular_dependencies": "PASS",
    "api_contract": "PENDING"
  },
  "standards_compliance": {
    "linting": {
      "status": "FAIL",
      "issues": ["Line 8: Magic string detected", "Line 10: Unused import warning"]
    },
    "type_hints": {
      "status": "PASS",
      "coverage": "95%"
    },
    "test_coverage": {
      "status": "NOT_TESTED",
      "note": "No tests generated yet for this module"
    }
  },
  "dependency_analysis": {
    "new_dependencies": ["python-jose", "passlib", "bcrypt"],
    "conflicts": [],
    "security_advisories": [
      {
        "package": "python-jose",
        "advisory": "Ensure version >= 3.3.0 for CVE-2022-29217 fix"
      }
    ]
  },
  "integration_order": "AFTER config/settings.py",
  "rollback_plan": "Remove auth/ directory, revert requirements.txt"
}
```

---

## STEP 4: Knowledge Engine (S-2) - Intelligent Storage

The Knowledge Engine stores with embeddings, decay scoring, and cross-project learning.

**Store Operation:**
```json
{
  "key": "project_taskapi_2026_auth_module",
  "data": {
    "code": "<jwt_handler.py content>",
    "plan_context": "<architect decisions>",
    "integration_result": "<F-3 report>"
  },
  "metadata": {
    "confidence": 0.88,
    "reuse_score": 0.76,
    "decay_rate": 0.02,
    "embeddings": {
      "semantic_vector": "[0.23, -0.45, 0.12, ...]",
      "code_structure": "[0.89, 0.12, -0.34, ...]"
    },
    "tags": ["auth", "jwt", "fastapi", "rest-api", "python"],
    "derived_from": [],
    "contributes_to": [],
    "version": 1,
    "last_accessed": "2026-01-03T12:00:00Z",
    "access_count": 0
  }
}
```

**Retrieve Operation:**
```json
{
  "query": "How do I implement JWT authentication in FastAPI?",
  "retrieval_config": {
    "semantic_threshold": 0.75,
    "max_results": 5,
    "include_cross_project": true,
    "decay_penalty": true
  }
}
```

**Retrieval Output:**
```json
{
  "results": [
    {
      "key": "project_taskapi_2026_auth_module",
      "relevance_score": 0.94,
      "reuse_score": 0.76,
      "decay_adjusted_score": 0.92,
      "snippet": "JWT auth using python-jose with FastAPI dependency injection",
      "file": "auth/jwt_handler.py",
      "provenance": {
        "project": "TaskAPI 2026",
        "architect_plan": "M1-T3",
        "created": "2026-01-03",
        "author_agent": "builder_f1"
      }
    }
  ],
  "cross_project_insights": [
    {
      "source_project": "UserService 2025",
      "pattern": "Similar JWT implementation with refresh tokens",
      "applicability": 0.72,
      "suggestion": "Consider adding refresh token support"
    }
  ],
  "knowledge_gaps": [
    "No examples of OAuth2 integration with this pattern",
    "No rate limiting examples in JWT context"
  ]
}
```

---

## STEP 5: Evolution Agent (S-3) - Strategic Analysis

The Evolution Agent provides STRATEGIC critique, not just safe observations.

**Input:**
```json
{
  "observation": {
    "agents": 6,
    "activities": 12,
    "execution_time": "45s",
    "decisions_made": "<Architect decisions>",
    "code_generated": "<F-1 output>",
    "integration_status": "BLOCKED"
  }
}
```

**Expected Output:**
```json
{
  "risks": [
    {
      "component": "auth_architecture",
      "issue": "Tight coupling to JWT implementation",
      "detail": "No abstraction layer for authentication strategy",
      "impact": "Adding OAuth or API key auth later requires significant refactoring",
      "recommendation": "Introduce AuthStrategy interface now",
      "risk_level": "medium",
      "effort_to_fix_now": "low",
      "effort_to_fix_later": "high"
    },
    {
      "component": "secret_management",
      "issue": "No secrets rotation strategy",
      "detail": "SECRET_KEY change would invalidate all tokens",
      "impact": "Security incident response is blocked",
      "recommendation": "Support key versioning with 'kid' header",
      "risk_level": "medium",
      "effort_to_fix_now": "medium",
      "effort_to_fix_later": "high"
    }
  ],
  "inefficiencies": [
    {
      "component": "forge_pipeline",
      "issue": "Sequential F-1 -> F-2 -> F-3 execution",
      "detail": "Independent tasks (T1-T4) could be parallelized",
      "recommendation": "Enable parallel code generation for tasks with no dependencies",
      "estimated_speedup": "40%"
    }
  ],
  "architectural_concerns": [
    {
      "pattern": "Repository Pattern - Missing",
      "impact": "Direct ORM usage in endpoints will complicate testing",
      "recommendation": "Architect should mandate repository layer for M2 tasks"
    },
    {
      "pattern": "Error Handling - Inconsistent",
      "impact": "No global error strategy defined",
      "recommendation": "Establish error response schema before CRUD endpoints"
    }
  ],
  "scalability_limits": [
    {
      "limit": "Synchronous password hashing",
      "threshold": "~1000 concurrent login requests",
      "recommendation": "Consider async bcrypt or move to auth service"
    }
  ],
  "maintenance_forecast": {
    "6_months": "Stable if abstraction recommendations adopted",
    "12_months": "Technical debt accumulates without auth interface",
    "risk_trajectory": "INCREASING if F-2 recommendations ignored"
  },
  "suggested_changes": [
    {
      "title": "Abstract authentication interface",
      "scope": "auth module",
      "risk": "low",
      "effort": "medium",
      "priority": "high",
      "rationale": "Future-proofs for OAuth, API keys, SSO"
    },
    {
      "title": "Add configuration management module",
      "scope": "core infrastructure",
      "risk": "low",
      "effort": "low",
      "priority": "high",
      "rationale": "Blocks current integration; prerequisite for all modules"
    }
  ],
  "priority": "high",
  "confidence": 0.87,
  "verdict": "PROCEED_WITH_CONDITIONS",
  "conditions": [
    "Resolve config module blocker before continuing",
    "Adopt auth interface before M2 tasks"
  ]
}
```

---

## FAILURE HANDLING

Arcyn OS must degrade gracefully. Here are the failure paths:

### On Persona Failure (Low Confidence / High Ambiguity)
```json
{
  "trigger": "confidence < 0.6 OR risk_flags.length > 2",
  "action": "CLARIFY",
  "response": {
    "status": "CLARIFICATION_REQUIRED",
    "prompt": "Could you specify: [missing_info items]?",
    "retry_allowed": true,
    "fallback": "Route to human operator"
  }
}
```

### On Architect Failure (Conflicting Constraints)
```json
{
  "trigger": "Cannot satisfy all constraints",
  "action": "ESCALATE",
  "response": {
    "status": "CONSTRAINT_CONFLICT",
    "conflicts": ["Async required but chosen library is sync-only"],
    "options": [
      {"choice": "Relax async constraint", "impact": "..."},
      {"choice": "Choose different library", "impact": "..."}
    ],
    "escalate_to": "human_architect",
    "auto_resolve": false
  }
}
```

### On Builder (F-1) Failure (Invalid Code)
```json
{
  "trigger": "Syntax error OR F-2 rejects code",
  "action": "ROLLBACK_AND_RETRY",
  "response": {
    "status": "BUILD_FAILED",
    "task_id": "T3",
    "error": "F-2 rejection: hardcoded secrets",
    "rollback": ["Remove auth/jwt_handler.py"],
    "retry_strategy": {
      "max_retries": 2,
      "with_context": "F-2 feedback included in prompt"
    },
    "notify": ["architect_agent"],
    "block_downstream": true
  }
}
```

### On Integrator (F-3) Failure (Compatibility Break)
```json
{
  "trigger": "BLOCKING_ISSUES detected",
  "action": "BLOCK_INTEGRATION",
  "response": {
    "status": "INTEGRATION_BLOCKED",
    "blocking_issues": ["config/settings.py missing"],
    "knowledge_write": "BLOCKED",
    "resolution_options": [
      "Generate missing dependency first",
      "Refactor to remove dependency"
    ],
    "auto_resolve_if": "Missing module is in current task queue"
  }
}
```

### On Knowledge Engine Conflict
```json
{
  "trigger": "Conflicting entries for same pattern",
  "action": "REQUEST_RESOLUTION",
  "response": {
    "status": "KNOWLEDGE_CONFLICT",
    "conflict_type": "PATTERN_DIVERGENCE",
    "entries": [
      {"key": "auth_jwt_v1", "approach": "Simple JWT"},
      {"key": "auth_jwt_v2", "approach": "JWT with refresh tokens"}
    ],
    "resolution_options": [
      {"merge": "Combine into configurable pattern"},
      {"deprecate": "Mark v1 as legacy"},
      {"fork": "Maintain both for different use cases"}
    ],
    "auto_resolve": false,
    "escalate_to": "evolution_agent"
  }
}
```

### On Evolution Agent Disagreement (Recommendations Rejected)
```json
{
  "trigger": "Critical recommendation ignored by user/architect",
  "action": "LOG_AND_TRACK",
  "response": {
    "status": "RECOMMENDATION_OVERRIDDEN",
    "recommendation_id": "rec_001",
    "override_reason": "User decision: Ship faster",
    "risk_accepted": true,
    "future_reminder": {
      "trigger": "Next project with similar pattern",
      "message": "Previous project ignored this - check if issues manifested"
    }
  }
}
```

---

## VERIFICATION CHECKLIST

### Persona Agent (S-1)
- [ ] Outputs confidence score (not always 1.0)
- [ ] Lists explicit assumptions
- [ ] Identifies missing information
- [ ] Flags risks with mitigation strategies
- [ ] Handles clarification flow

### Architect Agent (A-1)
- [ ] Makes explicit technology decisions with reasoning
- [ ] Shows rejected alternatives
- [ ] Defines architectural constraints for Forge
- [ ] Surfaces open questions

### Forge F-1 (Builder)
- [ ] Generates complete, runnable code
- [ ] Lists dependencies
- [ ] Marks output as pending validation

### Forge F-2 (System Designer)
- [ ] Validates against architectural constraints
- [ ] Identifies pattern violations
- [ ] Provides specific fix recommendations
- [ ] Approves/blocks with conditions

### Forge F-3 (Integrator)
- [ ] Checks compatibility with existing modules
- [ ] Enforces coding standards
- [ ] Detects security advisories
- [ ] Provides rollback plan

### Knowledge Engine (S-2)
- [ ] Stores with embeddings and metadata
- [ ] Calculates reuse and decay scores
- [ ] Retrieves cross-project insights
- [ ] Identifies knowledge gaps

### Evolution Agent (S-3)
- [ ] Provides STRATEGIC critique (not just "looks good")
- [ ] Identifies architectural rigidity
- [ ] Forecasts scalability limits
- [ ] Tracks maintenance risk trajectory
- [ ] Recommends with effort/priority tradeoffs

### Failure Handling
- [ ] Each agent has explicit failure path
- [ ] Rollback strategies are defined
- [ ] Escalation paths are clear
- [ ] Auto-resolve conditions are specified

---

## SUCCESS CRITERIA

[OK] Persona handles ambiguity intelligently
[OK] Architect shows decision-making process
[OK] Forge pipeline has clear separation of concerns
[OK] Knowledge Engine enables compound learning
[OK] Evolution provides strategic guidance
[OK] System degrades gracefully under failure

---

**END OF LOOP TEST PROMPT**

Copy this entire prompt and execute it to validate the Arcyn OS multi-agent loop.
The system should demonstrate both the happy path AND failure handling.
'''
    
    def _generate_agent_prompt(self, match: IntentMatch) -> str:
        """Generate prompt for a specific agent or ask which one."""
        agent_name = match.extracted_params.get("agent_name")
        
        if not agent_name:
            return self._generate_agent_selection_prompt()
        
        return self._get_agent_prompt(agent_name)
    
    def _generate_agent_selection_prompt(self) -> str:
        """Generate prompt asking which agent."""
        return '''# Arcyn OS Agent Prompt Request

Which agent prompt would you like?

Available Agents:
- **Persona (S-1)** - User intent classification and routing
- **Architect (A-1)** - Development planning and task breakdown
- **Builder/Forge (F-1)** - Code generation and implementation
- **Integrator (I-1)** - Validation and integration
- **Knowledge Engine (S-2)** - Memory and retrieval
- **Evolution (S-3)** - System monitoring and recommendations
- **System Designer (D-1)** - Architecture design

Specify your request:
Example: "Give me the architect agent prompt"
'''
    
    def _get_agent_prompt(self, agent_name: str) -> str:
        """Get the prompt for a specific agent."""
        prompts = {
            "persona": self._persona_prompt(),
            "architect": self._architect_prompt(),
            "builder": self._builder_prompt(),
            "integrator": self._integrator_prompt(),
            "knowledge": self._knowledge_prompt(),
            "evolution": self._evolution_prompt(),
            "system_designer": self._system_designer_prompt(),
        }
        return prompts.get(agent_name, f"Agent '{agent_name}' prompt not found.")
    
    def _persona_prompt(self) -> str:
        return '''# Persona Agent (S-1) Build Prompt

You are building the Persona Agent for Arcyn OS.

## Responsibilities
- Receive natural language input from users
- Classify user intent
- Extract parameters from requests
- Route to appropriate downstream agents
- Format responses for users

## Interface
```python
class PersonaAgent:
    def process(self, user_input: str) -> dict:
        """
        Process user input and return routing decision.
        
        Returns:
            {
                "intent": str,
                "params": dict,
                "route_to": str,
                "confidence": float
            }
        """
```

## Constraints
- Must be deterministic
- Must handle ambiguous input gracefully
- Must not execute actions directly
- Must maintain conversation context
'''
    
    def _architect_prompt(self) -> str:
        return '''# Architect Agent (A-1) Build Prompt

You are building the Architect Agent for Arcyn OS.

## Responsibilities
- Accept high-level goals
- Generate structured development plans
- Break down into milestones and tasks
- Define task dependencies
- Estimate complexity

## Interface
```python
class ArchitectAgent:
    def plan(self, goal: str) -> dict:
        """
        Generate development plan from goal.
        
        Returns:
            {
                "goal": str,
                "milestones": [...],
                "tasks": [...],
                "execution_order": [...],
                "metadata": {...}
            }
        """
    
    def breakdown(self, task: str) -> dict:
        """Break down a single task into subtasks."""
    
    def evaluate(self, progress: dict) -> dict:
        """Evaluate progress against the plan."""
```

## Constraints
- Does not write code
- Outputs JSON only
- Must be deterministic
'''
    
    def _builder_prompt(self) -> str:
        return '''# Builder/Forge Agent (F-1, F-2, F-3) Build Prompt

You are building the Builder Agent for Arcyn OS.

## Responsibilities
- Accept task specifications
- Generate production-ready code
- Follow project conventions
- Include documentation
- Handle errors gracefully

## Interface
```python
class BuilderAgent:
    def build(self, task: dict, context: dict) -> dict:
        """
        Generate code for a task.
        
        Returns:
            {
                "files": [{"path": str, "content": str}],
                "dependencies": [...],
                "tests": [...],
                "status": str
            }
        """
    
    def refactor(self, code: str, instructions: str) -> str:
        """Refactor existing code."""
    
    def validate(self, code: str) -> dict:
        """Validate code syntax and style."""
```

## Constraints
- Must generate complete, runnable code
- Must include type hints
- Must follow project standards
'''
    
    def _integrator_prompt(self) -> str:
        return '''# Integrator Agent (I-1) Build Prompt

You are building the Integrator Agent for Arcyn OS.

## Responsibilities
- Validate generated code
- Check dependency compatibility
- Enforce project standards
- Produce integration reports
- Detect conflicts

## Interface
```python
class IntegratorAgent:
    def integrate(self, modules: list, standards: dict) -> dict:
        """
        Validate and integrate modules.
        
        Returns:
            {
                "status": "PASSED" | "FAILED",
                "modules_validated": int,
                "conflicts": [...],
                "compliance": {...},
                "warnings": [...]
            }
        """
```

## Constraints
- Must not modify code directly
- Must produce deterministic reports
- Must be comprehensive
'''
    
    def _knowledge_prompt(self) -> str:
        return '''# Knowledge Engine (S-2) Build Prompt

You are building the Knowledge Engine for Arcyn OS.

## Responsibilities
- Store build context and history
- Retrieve relevant information
- Track provenance
- Support semantic search
- Maintain knowledge graph

## Interface
```python
class KnowledgeEngine:
    def store(self, key: str, data: Any, metadata: dict) -> bool:
        """Store data with provenance tracking."""
    
    def retrieve(self, query: str, limit: int = 5) -> list:
        """Retrieve relevant entries by query."""
    
    def get_provenance(self, key: str) -> dict:
        """Get full provenance chain for an entry."""
```

## Constraints
- Must track all data sources
- Must support versioning
- Must be queryable by natural language
'''
    
    def _evolution_prompt(self) -> str:
        return '''# Evolution Agent (S-3) Build Prompt

You are building the Evolution Agent for Arcyn OS.

## Responsibilities
- Monitor system performance
- Analyze agent behavior
- Detect inefficiencies
- Recommend improvements
- Track health metrics

## Interface
```python
class EvolutionAgent:
    def observe(self, snapshot: dict = None) -> dict:
        """Collect system observation."""
    
    def analyze(self, observations: dict) -> dict:
        """Analyze observations for issues."""
    
    def recommend(self, analysis: dict) -> dict:
        """
        Generate recommendations.
        
        Returns:
            {
                "risks": [...],
                "inefficiencies": [...],
                "suggested_changes": [...],
                "priority": "low" | "medium" | "high",
                "confidence": float
            }
        """
```

## Constraints
- ADVISORY-ONLY mode
- Does NOT modify production code
- Does NOT act autonomously
- Observes -> Analyzes -> Recommends
'''
    
    def _system_designer_prompt(self) -> str:
        return '''# System Designer Agent (D-1) Build Prompt

You are building the System Designer Agent for Arcyn OS.

## Responsibilities
- Design system architecture
- Generate schema definitions
- Map dependencies
- Enforce architectural standards
- Produce architecture documentation

## Interface
```python
class SystemDesignerAgent:
    def design(self, requirements: dict) -> dict:
        """Generate system architecture from requirements."""
    
    def generate_schema(self, entities: list) -> dict:
        """Generate data schemas for entities."""
    
    def map_dependencies(self, components: list) -> dict:
        """Map component dependencies."""
```

## Constraints
- Must follow established patterns
- Must be technology-agnostic where possible
- Must document all decisions
'''
    
    def _generate_system_status(self, match: IntentMatch) -> str:
        """Generate system status report."""
        try:
            import sys
            from pathlib import Path
            project_root = Path(__file__).parent.parent
            sys.path.insert(0, str(project_root))
            
            from agents.evolution import EvolutionAgent
            agent = EvolutionAgent()
            status = agent.get_status()
            health = agent.get_health_report()
            
            return f'''# Arcyn OS System Status

**Agent ID:** {status.get("agent_id", "unknown")}
**State:** {status.get("state", "unknown")}

## Health Score
- **Overall:** {health.get("health_score", {}).get("overall_score", 0):.1%}
- **Status:** {health.get("health_score", {}).get("overall_status", "unknown")}

## System Components
- Evolution Agent (S-3): Active
- Command Trigger: Active

Status check completed at system time.
'''
        except Exception as e:
            return f'''# Arcyn OS System Status

System status check encountered an error: {str(e)}

Basic components:
- Command Trigger: Active
- Intent Router: Active
- Dispatcher: Active
'''
    
    def _generate_architecture_explanation(self, match: IntentMatch) -> str:
        """Generate architecture explanation."""
        return '''# Arcyn OS Architecture

Arcyn OS is an AI-first, multi-agent operating system.

## Core Agents

| Agent | ID | Responsibility |
|-------|-----|----------------|
| Persona | S-1 | User intent processing |
| Architect | A-1 | Development planning |
| Builder/Forge | F-1 | Code generation |
| Integrator | I-1 | Validation & integration |
| Knowledge Engine | S-2 | Memory & retrieval |
| Evolution | S-3 | Monitoring & recommendations |
| System Designer | D-1 | Architecture design |

## Data Flow

```
User Request
    |
    v
+------------------+
|  Persona (S-1)   | --- Intent Classification
+--------+---------+
         |
         v
+------------------+
| Architect (A-1)  | --- Planning
+--------+---------+
         |
         v
+------------------+
|  Builder (F-1)   | --- Code Generation
+--------+---------+
         |
         v
+------------------+
| Integrator (I-1) | --- Validation
+--------+---------+
         |
         v
+------------------+
| Knowledge (S-2)  | --- Storage
+--------+---------+
         |
         v
+------------------+
| Evolution (S-3)  | --- Analysis
+------------------+
```

## Core Infrastructure

- **Memory**: Persistent storage across sessions
- **Logger**: Structured logging for all agents
- **Context Manager**: State management
- **Command Trigger**: Single-entry execution interface

## Design Principles

1. **Advisory-Only**: Agents recommend, humans approve
2. **Deterministic**: Same input -> same output
3. **Traceable**: All actions are logged
4. **Modular**: Agents are independent
5. **Safe**: No autonomous mutations
'''
    
    def _run_evolution_cycle(self, match: IntentMatch) -> str:
        """Run the evolution agent cycle."""
        try:
            import sys
            from pathlib import Path
            project_root = Path(__file__).parent.parent
            sys.path.insert(0, str(project_root))
            
            from agents.evolution import EvolutionAgent
            agent = EvolutionAgent()
            result = agent.run_full_cycle()
            
            obs = result["observation"]
            analysis = result["analysis"]
            recs = result["recommendations"]
            health = result["health_score"]
            
            output = f'''# Arcyn OS Evolution Cycle Report

## Observation
- Agents Observed: {len(obs.get("agents", {}))}
- Activities Recorded: {len(obs.get("recent_activities", []))}
- Warnings: {len(obs.get("warnings", []))}
- Errors: {len(obs.get("errors", []))}

## Analysis
- Total Issues: {analysis.get("summary", {}).get("total_issues", 0)}
- System Health: {analysis.get("summary", {}).get("health", "unknown")}
- Bottlenecks: {len(analysis.get("bottlenecks", []))}
- Technical Debt Items: {len(analysis.get("technical_debt", []))}

## Recommendations
- Total: {len(recs.get("recommendations", []))}
- Priority: {recs.get("priority", "unknown")}
- Confidence: {recs.get("confidence", 0):.0%}

## Health Score
- Overall: {health.get("overall_score", 0):.1%}
- Status: {health.get("overall_status", "unknown")}

'''
            if recs.get("recommendations"):
                output += "## Top Recommendations\n"
                for rec in recs["recommendations"][:5]:
                    output += f'- [{rec.get("priority", "?")}] {rec.get("title", "Unknown")}\n'
                    output += f'  Effort: {rec.get("effort", "?")}, Risk: {rec.get("risk", "?")}\n'
            
            return output
            
        except Exception as e:
            return f'''# Arcyn OS Evolution Cycle

Evolution cycle encountered an error: {str(e)}

Try running directly:
```
python agents/evolution/run.py --command cycle
```
'''
    
    def _generate_help(self, match: IntentMatch) -> str:
        """Generate help message."""
        return '''# Arcyn OS Command Trigger - Help

## Available Commands

| Command | Description |
|---------|-------------|
| "Give me the full Arcyn OS loop test" | Get complete system loop test prompt |
| "Agent prompt for [name]" | Get prompt for specific agent |
| "System status" | Check system health |
| "Explain architecture" | Get architecture overview |
| "Run evolution cycle" | Run system analysis |
| "Help" | Show this help message |

## Agent Names
- Persona, S-1
- Architect, A-1
- Builder, Forge, F-1
- Integrator, I-1
- Knowledge Engine, S-2
- Evolution, S-3
- System Designer, D-1

## Examples
```
"Give me the full Arcyn OS loop test prompt"
"Build agent prompt for the architect"
"What is the system status?"
"Explain how Arcyn OS works"
"Run the evolution cycle"
```
'''
    
    def _handle_unknown(self, match: IntentMatch) -> str:
        """Handle unknown commands."""
        return '''Command not recognized by Arcyn OS.

Type "help" to see available commands.

Available intents:
- Loop test request
- Agent prompt request
- System status
- Architecture explanation
- Evolution cycle
- Help
'''
