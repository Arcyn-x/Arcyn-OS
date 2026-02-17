# 🧠 Arcyn OS

**An AI-first, multi-agent operating system for intelligent software development.**

Arcyn OS orchestrates a pipeline of specialized AI agents that plan, build, validate, and evolve software systems — from natural language goals to production-ready code.

---

## 🏗️ Architecture

```
User Input
    │
    ▼
┌──────────────────┐
│  Persona (S-1)   │  ← Human interface: intent classification & routing
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  Architect (A-1) │  ← Plans: goals → tasks, milestones, dependencies
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  Builder (F-1)   │  ← Code generation: tasks → files
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ Sys Designer(F-2)│  ← Architectural validation & standards
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ Integrator (F-3) │  ← Compatibility, dependencies, standards enforcement
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ Knowledge (S-2)  │  ← Persistent memory, embeddings, cross-project learning
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ Evolution (S-3)  │  ← Strategic analysis, health monitoring, recommendations
└──────────────────┘
```

---

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- A Google Gemini API key ([get one here](https://aistudio.google.com/app/apikey))

### Installation

```bash
# Clone the repository
git clone <repo-url>
cd "Arcyn OS"

# Create virtual environment
python -m venv .venv
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # macOS/Linux

# Install dependencies
pip install -r requirements.txt

# For development
pip install -r requirements.txt -r requirements-dev.txt
```

### Configuration

```bash
# Copy the example environment file
cp .env.example .env

# Edit .env and add your Gemini API key
# GEMINI_API_KEY=your-key-here
```

### Usage

#### Main CLI (recommended)

```bash
# Interactive mode
python main.py

# Execute a goal through the full agent pipeline
python main.py "Build a REST API for task management"

# Check system status (all 7 agents)
python main.py --status

# Run Evolution Agent cycle
python main.py --evolution

# Verbose output
python main.py -v "Create a user authentication system"
```

#### Command Trigger (Legacy CLI)

```bash
python -m core.command_trigger "system status"
python -m core.command_trigger "explain architecture"
```

#### Pipeline Orchestrator

```python
from core.orchestrator import Orchestrator

# Initialize the full pipeline
orch = Orchestrator()

# Execute a goal through the full agent pipeline
result = orch.execute("Build a REST API for task management with authentication")

# Or step-by-step
classified = orch.classify("Build a REST API")
plan = orch.plan(classified)
code = orch.build(plan)
validated = orch.validate(code, plan)
integrated = orch.integrate(validated)
```

#### Evolution Agent (System Monitor)

```bash
# Interactive CLI
python agents/evolution/run.py

# Run full analysis cycle
python agents/evolution/run.py --command cycle
```

#### API Server

```bash
# Start the REST API server
python main.py --api

# Or with custom port
python main.py --api --port 8080

# API endpoints:
#   http://localhost:8000          Root info
#   http://localhost:8000/docs     Interactive docs (Swagger)
#   POST /api/execute              Run full pipeline
#   POST /api/classify             Classify intent
#   POST /api/plan                 Create plan
#   GET  /api/status               System status
#   GET  /api/health               Health check
#   GET  /api/memory/search        Search memory
```

---

## 📁 Project Structure

```
Arcyn OS/
├── core/                          # Core system modules
│   ├── __init__.py                # Core exports
│   ├── memory.py                  # Persistent memory (JSON + SQLite)
│   ├── logger.py                  # Structured logging
│   ├── context_manager.py         # Agent state & context sharing
│   ├── command_trigger.py         # CLI command interface
│   ├── intent_router.py           # Intent classification
│   ├── dispatcher.py              # Intent-to-action routing
│   ├── orchestrator.py            # Pipeline orchestrator
│   ├── llm_provider.py            # Gemini LLM interface
│   └── llm_gateway/               # LLM Gateway (rate limiting, cost tracking)
│       ├── gateway.py             # Central gateway
│       ├── policy.py              # Request policies
│       ├── rate_limiter.py        # Rate limiting
│       ├── cost_tracker.py        # Cost tracking
│       ├── logger.py              # Gateway logging
│       └── providers/
│           ├── base.py            # Provider interface
│           └── gemini.py          # Gemini provider
│
├── agents/                        # Agent implementations
│   ├── persona/                   # S-1: Human interface agent
│   │   ├── persona_agent.py
│   │   ├── intent_classifier.py
│   │   ├── command_router.py
│   │   ├── response_formatter.py
│   │   └── session_manager.py
│   │
│   ├── architect/                 # A-1: Planning agent
│   │   ├── architect_agent.py
│   │   ├── planner.py
│   │   ├── task_graph.py
│   │   └── evaluator.py
│   │
│   ├── builder/                   # F-1: Code generation agent
│   │   ├── builder_agent.py
│   │   ├── code_writer.py
│   │   ├── file_manager.py
│   │   ├── refactor_engine.py
│   │   └── validator.py
│   │
│   ├── system_designer/           # F-2: Architecture validation agent
│   │   ├── system_designer_agent.py
│   │   ├── architecture_engine.py
│   │   ├── schema_generator.py
│   │   ├── standards.py
│   │   └── dependency_mapper.py
│   │
│   ├── integrator/                # F-3: Integration validation agent
│   │   ├── integrator_agent.py
│   │   ├── contract_validator.py
│   │   ├── dependency_checker.py
│   │   ├── standards_enforcer.py
│   │   └── integration_report.py
│   │
│   ├── knowledge_engine/          # S-2: Knowledge management agent
│   │   ├── knowledge_engine.py
│   │   ├── memory_store.py
│   │   ├── retriever.py
│   │   ├── embedder.py
│   │   └── provenance.py
│   │
│   └── evolution/                 # S-3: System monitor agent
│       ├── evolution_agent.py
│       ├── system_monitor.py
│       ├── analyzer.py
│       ├── recommender.py
│       ├── health_metrics.py
│       └── run.py
│
├── api/                           # REST API
│   ├── __init__.py
│   └── server.py
│
├── tests/                         # Test suite (98 tests)
│   ├── test_memory.py             # Memory CRUD, SQLite, search
│   ├── test_context_manager.py    # State, sharing, versioning
│   ├── test_orchestrator.py       # Pipeline stages, execution
│   ├── test_agents.py             # All 7 agents init & methods
│   ├── test_api.py                # REST API endpoints
│   └── integration/               # LLM integration tests (requires API key)
│       ├── test_llm_gateway.py
│       ├── test_llm_provider.py
│       └── forge_test.py
│
├── design/                        # Architecture documents
│   ├── architecture.json
│   ├── architecture.md
│   ├── standards.json
│   ├── standards.md
│   └── dependencies.json
│
├── knowledge/                     # Knowledge database
├── memory/                        # Persistent memory storage
├── logs/                          # System logs
│
├── main.py                        # Main entry point (CLI + API)
├── .env.example                   # Environment template
├── .gitignore
├── pyproject.toml                 # Pytest, ruff, mypy config
├── requirements.txt               # Production dependencies
├── requirements-dev.txt           # Development dependencies
└── README.md                      # This file
```

---

## 🤖 Agents

| Agent | ID | Role | Responsibility |
|-------|-----|------|----------------|
| **Persona** | S-1 | Interface | Translates human intent ↔ system commands |
| **Architect** | A-1 | Planner | Goals → tasks, milestones, dependencies |
| **Builder** | F-1 | Creator | Tasks → code files with validation |
| **System Designer** | F-2 | Validator | Architectural compliance & standards |
| **Integrator** | F-3 | Enforcer | Compatibility, dependencies, standards |
| **Knowledge Engine** | S-2 | Memory | Persistent storage, embeddings, retrieval |
| **Evolution** | S-3 | Advisor | System monitoring & improvement suggestions |

---

## 🔌 LLM Gateway

All LLM operations go through the centralized **LLM Gateway** — no agent calls providers directly.

The gateway provides:
- **Rate Limiting** — Per-agent and global request throttling
- **Cost Tracking** — Token usage and cost monitoring
- **Policy Engine** — Request validation and budget enforcement
- **Logging** — Full audit trail of all LLM operations
- **Provider Abstraction** — Currently Gemini; extensible to OpenAI, Anthropic

---

## 🧪 Testing

```bash
# Run all unit tests (98 tests)
pytest

# Run with coverage
pytest --cov=core --cov=agents --cov-report=html

# Run specific test file
pytest tests/test_orchestrator.py -v

# Run integration tests (requires GEMINI_API_KEY in .env)
python tests/integration/test_llm_gateway.py
python tests/integration/forge_test.py
```

### Test Coverage

| Module | Tests | Status |
|--------|-------|--------|
| `core.memory` | 19 | ✅ |
| `core.context_manager` | 22 | ✅ |
| `core.orchestrator` | 19 | ✅ |
| All 7 agents | 29 | ✅ |
| API endpoints | 8 | ✅ |
| **Total** | **98** | **All pass** |

---

## 📜 License

Proprietary — Arcyn OS © 2026
