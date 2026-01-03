# Evolution Agent (S-3)

**Arcyn OS System Monitor & Improvement Advisor**

The Evolution Agent is responsible for monitoring, analysis, and improvement suggestions across the entire Arcyn OS system. It operates as a **senior reviewer** — observing, analyzing, and recommending, but never directly modifying production code.

---

## 🚨 Advisory-Only Mode

The Evolution Agent is **ADVISORY-ONLY** by default.

It does **NOT**:
- ❌ Directly modify production code
- ❌ Override other agents
- ❌ Act autonomously without approval
- ❌ Make external API calls
- ❌ Execute autonomous loops

It **DOES**:
- ✅ Observe system state
- ✅ Analyze agent behavior
- ✅ Detect inefficiencies and risks
- ✅ Recommend improvements
- ✅ Track health metrics over time

---

## 📁 Structure

```
agents/evolution/
├── __init__.py          # Package initialization
├── evolution_agent.py   # Main agent class
├── system_monitor.py    # System snapshot & activity tracking
├── analyzer.py          # Rule-based issue detection
├── recommender.py       # Improvement recommendations
├── health_metrics.py    # Health indicators & trends
├── run.py               # CLI interface
├── test_agent.py        # Test script
└── README.md            # This file
```

---

## 🚀 Quick Start

### CLI Usage

```bash
# Start interactive CLI
python agents/evolution/run.py

# Run single command
python agents/evolution/run.py --command cycle
```

### CLI Commands

| Command | Description |
|---------|-------------|
| `observe` | Take a system snapshot |
| `analyze` | Analyze the last observation |
| `recommend` | Generate recommendations |
| `cycle` | Run full observe → analyze → recommend |
| `status` | Show agent status |
| `health` | Show health report |
| `history` | Show recent agent history |
| `help` | Show available commands |
| `exit` | Exit the CLI |

### Programmatic Usage

```python
from agents.evolution import EvolutionAgent

# Initialize
agent = EvolutionAgent()

# Run full cycle
result = agent.run_full_cycle()

# Or step by step:
snapshot = agent.observe()
analysis = agent.analyze(snapshot)
recommendations = agent.recommend(analysis)

# Check output
print(recommendations["priority"])      # "low | medium | high"
print(recommendations["confidence"])    # 0.0 - 1.0
print(recommendations["risks"])         # High-risk items
print(recommendations["suggested_changes"])
```

---

## 📊 Output Format

The agent produces recommendations in this format:

```json
{
  "risks": [],
  "inefficiencies": [],
  "suggested_changes": [],
  "priority": "low | medium | high",
  "confidence": 0.0
}
```

### Recommendation Structure

Each recommendation includes:

```json
{
  "rec_id": "rec_00001",
  "title": "Improve reliability of builder_agent",
  "description": "Address high failure rate",
  "recommendation_type": "refactor | optimization | deprecation | new_module | new_agent",
  "scope": "Affects 1 component(s)",
  "risk": "minimal | low | medium | high | critical",
  "effort": "trivial | low | medium | high | significant",
  "priority": "low | medium | high",
  "confidence": 0.8,
  "rationale": "Why this is recommended",
  "affected_components": ["builder_agent"],
  "dependencies": [],
  "prerequisites": [],
  "expected_benefits": ["Improved reliability"],
  "implementation_hints": ["Add error handling", "Implement retry logic"]
}
```

---

## 🔧 Components

### EvolutionAgent

Main orchestrator that chains observe → analyze → recommend.

```python
agent = EvolutionAgent(
    agent_id="custom_id",      # Optional custom ID
    log_level=20,               # INFO level
    agents_path="/path/to/agents",  # Custom agents path
    storage_path="/path/to/memory"  # Custom memory storage
)
```

### SystemMonitor

Collects batch snapshots (not real-time).

```python
from agents.evolution.system_monitor import SystemMonitor

monitor = SystemMonitor()
monitor.record_activity("agent_id", "type", "action", "success", 150)
snapshot = monitor.take_snapshot()
```

### Analyzer

Rule-based analysis with LLM hooks (TODOs).

```python
from agents.evolution.analyzer import Analyzer

analyzer = Analyzer()
result = analyzer.analyze(observations)
# Returns: issues, patterns, bottlenecks, technical_debt
```

### Recommender

Generates recommendations with full metadata.

```python
from agents.evolution.recommender import Recommender

recommender = Recommender()
result = recommender.recommend(analysis)
# Includes: scope, risk, effort, dependencies
```

### HealthMetrics

Tracks health indicators over time.

```python
from agents.evolution.health_metrics import HealthMetrics

metrics = HealthMetrics()
metrics.record_indicator("failure_rate", 0.05)
score = metrics.get_health_score()
```

---

## 🔒 Design Constraints

1. **No direct file writes** outside logs
2. **No autonomous execution loops**
3. **No external API calls**
4. **Local-only execution**
5. **Deterministic behavior**
6. **Conservative recommendations**
7. **Fail-safe operation**

---

## 🔮 Future Autonomy (Gated)

The following features are **explicitly gated** and require approval:

- `_auto_remediate()` - Automatically implement recommendations
- `_continuous_monitoring()` - Background monitoring loop
- `_llm_analyze_patterns()` - LLM-powered pattern detection
- `_llm_suggest_root_causes()` - LLM root cause analysis

These are implemented as TODOs and will require:
- Explicit configuration flag
- Human approval workflow
- Rate limiting and circuit breakers

---

## 📝 Integration with Core

The Evolution Agent integrates with:

```python
from core.memory import Memory      # Persistent storage
from core.logger import Logger      # Structured logging
from core.context_manager import ContextManager  # State management
```

All observations, analyses, and recommendations are:
- Logged to `logs/evolution_*.log`
- Saved to memory as JSON
- Traceable through context history

---

## 🧪 Testing

```bash
# Run test script
python agents/evolution/test_agent.py

# Import test
python -c "from agents.evolution import EvolutionAgent; print('OK')"
```

---

## 📋 Responsibilities

| Responsibility | Status |
|----------------|--------|
| Monitor system performance | ✅ Implemented |
| Analyze agent behavior | ✅ Implemented |
| Detect inefficiencies and risks | ✅ Implemented |
| Suggest architectural improvements | ✅ Implemented |
| Propose refactors and upgrades | ✅ Implemented |
| Track system health over time | ✅ Implemented |
| Direct code modification | ❌ Not allowed |
| Autonomous execution | ❌ Not allowed |

---

This agent behaves like a **senior reviewer**, not an auto-rewriter.
