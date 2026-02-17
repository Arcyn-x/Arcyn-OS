"""
Tests for Phase-2 enhancements:
- Knowledge Engine: ingest_with_embedding, semantic_search, cross_project_learn
- Evolution Agent: _auto_remediate, _continuous_monitoring
- RefactorEngine: extract_functions, extract_imports, analyze_complexity, remove_unused_imports
"""

import pytest
import tempfile
import os
import sys
from unittest.mock import MagicMock, patch
from pathlib import Path


# ═══════════════════════════════════════════════════════════════════
# Knowledge Engine — Semantic Search & Cross-Project Learning
# ═══════════════════════════════════════════════════════════════════

class TestKnowledgeEngineIngestWithEmbedding:
    """Test ingest_with_embedding generates embeddings alongside storage."""

    def setup_method(self):
        from agents.knowledge_engine.knowledge_engine import KnowledgeEngine
        self.engine = KnowledgeEngine(agent_id="test_ke", log_level=50)

    def test_ingest_with_embedding_success(self):
        """Embedding should be stored when embedder returns a non-zero vector."""
        self.engine.embedder.embed = MagicMock(return_value=[0.1, 0.2, 0.3])

        result = self.engine.ingest_with_embedding({
            "namespace": "test",
            "key": "item_1",
            "content": "some knowledge content",
            "source_agent": "tester"
        })

        assert result["success"]
        assert result["embedded"]
        assert result["record_id"] is not None
        assert result["record_id"] in self.engine._embedding_index

    def test_ingest_with_embedding_zero_vector(self):
        """Embedding should not be stored when embedder returns all zeros."""
        self.engine.embedder.embed = MagicMock(return_value=[0.0, 0.0, 0.0])

        result = self.engine.ingest_with_embedding({
            "namespace": "test",
            "key": "item_2",
            "content": "content",
            "source_agent": "tester"
        })

        assert result["success"]
        assert not result["embedded"]

    def test_ingest_with_embedding_dict_content(self):
        """Dict content should be JSON-serialized for embedding."""
        self.engine.embedder.embed = MagicMock(return_value=[0.5, 0.5])

        result = self.engine.ingest_with_embedding({
            "namespace": "test",
            "key": "item_3",
            "content": {"detail": "structured data"},
            "source_agent": "tester"
        })

        assert result["success"]
        assert result["embedded"]

    def test_ingest_with_embedding_custom_embed_text(self):
        """Custom embed_text should override auto-generated text."""
        self.engine.embedder.embed = MagicMock(return_value=[0.1])

        result = self.engine.ingest_with_embedding({
            "namespace": "test",
            "key": "item_4",
            "content": "original content",
            "source_agent": "tester",
            "embed_text": "custom text for embedding"
        })

        assert result["embedded"]
        self.engine.embedder.embed.assert_called_with("custom text for embedding", task_id="ingest_embed")

    def test_ingest_with_embedding_failure_still_ingests(self):
        """If embedding fails, the knowledge should still be ingested."""
        self.engine.embedder.embed = MagicMock(side_effect=Exception("embedding error"))

        result = self.engine.ingest_with_embedding({
            "namespace": "test",
            "key": "item_5",
            "content": "important data",
            "source_agent": "tester"
        })

        assert result["success"]
        assert not result["embedded"]

    def test_ingest_with_embedding_missing_fields(self):
        """Missing required fields should prevent both ingest and embedding."""
        result = self.engine.ingest_with_embedding({
            "namespace": "test",
            "key": "item_6"
        })

        assert not result["success"]
        assert not result["embedded"]


class TestKnowledgeEngineSemanticSearch:
    """Test semantic_search with embedding similarity."""

    def setup_method(self):
        from agents.knowledge_engine.knowledge_engine import KnowledgeEngine
        self.engine = KnowledgeEngine(agent_id="test_ss", log_level=50)

    def test_semantic_search_empty_index(self):
        """Semantic search on empty index returns empty results."""
        result = self.engine.semantic_search("anything")
        assert result["count"] == 0
        assert not result["query_embedded"]

    def test_semantic_search_with_results(self):
        """Semantic search should return matching entries above threshold."""
        self.engine._embedding_index = {
            "rec_1": [1.0, 0.0, 0.0],
            "rec_2": [0.0, 1.0, 0.0],
            "rec_3": [0.5, 0.5, 0.0]
        }
        self.engine._embedding_metadata = {
            "rec_1": {"namespace": "test", "key": "k1", "content_preview": "item 1", "source_agent": "t"},
            "rec_2": {"namespace": "test", "key": "k2", "content_preview": "item 2", "source_agent": "t"},
            "rec_3": {"namespace": "other", "key": "k3", "content_preview": "item 3", "source_agent": "t"}
        }

        self.engine.embedder.embed = MagicMock(return_value=[0.9, 0.1, 0.0])
        self.engine.embedder.search_similar = MagicMock(return_value=[
            {"index": 0, "similarity": 0.95},
            {"index": 2, "similarity": 0.70},
            {"index": 1, "similarity": 0.10}
        ])

        result = self.engine.semantic_search("query text", threshold=0.3)

        assert result["query_embedded"]
        assert result["count"] == 2
        assert result["results"][0]["record_id"] == "rec_1"
        assert result["results"][0]["similarity"] == 0.95

    def test_semantic_search_namespace_filter(self):
        """Namespace filter should restrict results."""
        self.engine._embedding_index = {
            "rec_1": [1.0, 0.0],
            "rec_2": [0.9, 0.1]
        }
        self.engine._embedding_metadata = {
            "rec_1": {"namespace": "alpha", "key": "k1", "content_preview": "a", "source_agent": "t"},
            "rec_2": {"namespace": "beta", "key": "k2", "content_preview": "b", "source_agent": "t"}
        }

        self.engine.embedder.embed = MagicMock(return_value=[1.0, 0.0])
        self.engine.embedder.search_similar = MagicMock(return_value=[
            {"index": 0, "similarity": 0.99},
            {"index": 1, "similarity": 0.95}
        ])

        result = self.engine.semantic_search("query", namespace="beta", threshold=0.1)
        assert result["count"] == 1
        assert result["results"][0]["namespace"] == "beta"

    def test_semantic_search_top_k_limit(self):
        """Top-k should limit the number of results returned."""
        self.engine._embedding_index = {
            f"rec_{i}": [float(i) / 10] for i in range(10)
        }
        self.engine._embedding_metadata = {
            f"rec_{i}": {"namespace": "t", "key": f"k{i}", "content_preview": f"item {i}", "source_agent": "t"}
            for i in range(10)
        }

        self.engine.embedder.embed = MagicMock(return_value=[0.5])
        self.engine.embedder.search_similar = MagicMock(return_value=[
            {"index": i, "similarity": 0.9 - i * 0.05} for i in range(10)
        ])

        result = self.engine.semantic_search("query", top_k=3, threshold=0.0)
        assert result["count"] == 3

    def test_semantic_search_query_embed_failure(self):
        """Search should return empty when query embedding fails."""
        self.engine._embedding_index = {"rec_1": [1.0]}
        self.engine.embedder.embed = MagicMock(return_value=[0.0])

        result = self.engine.semantic_search("query")
        assert result["count"] == 0
        assert not result["query_embedded"]


class TestKnowledgeEngineCrossProjectLearn:
    """Test cross_project_learn pattern extraction."""

    def setup_method(self):
        from agents.knowledge_engine.knowledge_engine import KnowledgeEngine
        self.engine = KnowledgeEngine(agent_id="test_cpl", log_level=50)
        self.tmpdir = tempfile.mkdtemp()
        self.engine.embedder.embed = MagicMock(return_value=[0.1, 0.2])

    def _create_py_file(self, name: str, content: str) -> str:
        path = os.path.join(self.tmpdir, name)
        with open(path, "w") as f:
            f.write(content)
        return path

    def test_learn_extracts_class_patterns(self):
        path = self._create_py_file("module_a.py", 'class MyService:\n    """Service class."""\n    def run(self):\n        pass\n    def stop(self):\n        pass\n')
        result = self.engine.cross_project_learn([path], "test_project")
        assert result["success"]
        assert result["files_processed"] == 1
        assert result["patterns_extracted"] >= 1

    def test_learn_extracts_function_patterns(self):
        path = self._create_py_file("module_b.py", 'def helper_one(x):\n    """A helper."""\n    return x + 1\n\ndef helper_two(y):\n    return y * 2\n')
        result = self.engine.cross_project_learn([path], "test_project")
        assert result["success"]
        assert result["patterns_extracted"] >= 2

    def test_learn_handles_parse_errors(self):
        path = self._create_py_file("bad.py", "def broken(\n")
        result = self.engine.cross_project_learn([path], "test_project")
        assert len(result["errors"]) > 0

    def test_learn_handles_missing_files(self):
        result = self.engine.cross_project_learn(["/nonexistent/file.py"], "test_project")
        assert len(result["errors"]) > 0

    def test_learn_multiple_files(self):
        f1 = self._create_py_file("a.py", "class A:\n    pass\n")
        f2 = self._create_py_file("b.py", "def b():\n    pass\n")
        result = self.engine.cross_project_learn([f1, f2], "multi_project")
        assert result["files_processed"] == 2
        assert result["patterns_extracted"] >= 2


class TestKnowledgeEngineGetStatus:
    """Test get_status includes embedding count."""

    def test_status_includes_indexed_embeddings(self):
        from agents.knowledge_engine.knowledge_engine import KnowledgeEngine
        engine = KnowledgeEngine(agent_id="test_status", log_level=50)
        status = engine.get_status()
        assert "indexed_embeddings" in status
        assert status["indexed_embeddings"] == 0


# ═══════════════════════════════════════════════════════════════════
# Evolution Agent — Auto-Remediation & Continuous Monitoring
# ═══════════════════════════════════════════════════════════════════

class TestAutoRemediate:
    """Test _auto_remediate with gating and plan generation."""

    def setup_method(self):
        from agents.evolution.evolution_agent import EvolutionAgent
        self.agent = EvolutionAgent(log_level=50)

    def test_remediation_disabled_without_approval(self):
        result = self.agent._auto_remediate({
            "type": "refactor",
            "target": "core/module.py",
            "description": "Simplify logic",
            "priority": "medium"
        })
        assert not result["approved"]
        assert result["status"] == "disabled"

    def test_remediation_enabled_with_approval(self):
        result = self.agent._auto_remediate(
            {
                "type": "refactor",
                "target": "core/module.py",
                "description": "Extract helper function",
                "priority": "high"
            },
            config={"explicit_approval": True}
        )
        assert result["approved"]
        assert result["status"] == "queued"
        assert len(result["plan"]) > 0
        assert result["patches_queued"] == len(result["plan"])

    def test_remediation_fix_type(self):
        result = self.agent._auto_remediate(
            {
                "type": "fix",
                "target": "agents/builder.py",
                "description": "Fix null reference",
                "priority": "high"
            },
            config={"explicit_approval": True}
        )
        assert result["approved"]
        assert any(s["action"] == "diagnose" for s in result["plan"])

    def test_remediation_upgrade_type(self):
        result = self.agent._auto_remediate(
            {
                "type": "upgrade",
                "target": "requirements.txt",
                "description": "Upgrade google-genai to 2.0",
                "priority": "medium"
            },
            config={"explicit_approval": True}
        )
        assert result["approved"]
        assert any(s["action"] == "compatibility_check" for s in result["plan"])

    def test_remediation_unknown_type(self):
        result = self.agent._auto_remediate(
            {
                "type": "custom_action",
                "target": "anywhere",
                "description": "Something unusual",
                "priority": "low"
            },
            config={"explicit_approval": True}
        )
        assert result["approved"]
        assert any(s["action"] == "evaluate" for s in result["plan"])

    def test_remediation_max_patches_limit(self):
        result = self.agent._auto_remediate(
            {
                "type": "refactor",
                "target": "big_module.py",
                "description": "Major refactor",
                "priority": "high"
            },
            config={"explicit_approval": True, "max_patches": 2}
        )
        assert result["patches_queued"] <= 2

    def test_remediation_all_steps_reversible(self):
        result = self.agent._auto_remediate(
            {
                "type": "fix",
                "target": "core/something.py",
                "description": "Fix issue",
                "priority": "medium"
            },
            config={"explicit_approval": True}
        )
        for step in result["plan"]:
            assert step["reversible"] is True


class TestContinuousMonitoring:
    """Test _continuous_monitoring with gating and alert generation."""

    def setup_method(self):
        from agents.evolution.evolution_agent import EvolutionAgent
        self.agent = EvolutionAgent(log_level=50)

    def test_monitoring_disabled_without_approval(self):
        result = self.agent._continuous_monitoring()
        assert not result["monitoring_active"]
        assert result["status"] == "disabled"

    def test_monitoring_enabled_with_approval(self):
        self.agent.observe = MagicMock(return_value={
            "agents": {"builder": {}},
            "metrics": {"overall_failure_rate": 0.02},
            "recent_activities": []
        })
        self.agent.analyze = MagicMock(return_value={
            "summary": {"total_issues": 3, "health": "good"},
            "issues": []
        })
        self.agent.health_metrics.get_health_score = MagicMock(return_value=0.85)

        result = self.agent._continuous_monitoring(config={"explicit_approval": True})
        assert result["monitoring_active"]
        assert result["status"] == "active"
        assert result["health_score"] == 0.85
        assert result["issues_detected"] == 3

    def test_monitoring_generates_health_alert(self):
        self.agent.observe = MagicMock(return_value={
            "agents": {},
            "metrics": {"overall_failure_rate": 0.0},
            "recent_activities": []
        })
        self.agent.analyze = MagicMock(return_value={
            "summary": {"total_issues": 0},
            "issues": []
        })
        self.agent.health_metrics.get_health_score = MagicMock(return_value=0.25)

        result = self.agent._continuous_monitoring(
            config={"explicit_approval": True, "alert_threshold": 0.5}
        )

        assert len(result["alerts"]) >= 1
        health_alerts = [a for a in result["alerts"] if a["type"] == "health_degradation"]
        assert len(health_alerts) == 1
        assert health_alerts[0]["severity"] == "high"

    def test_monitoring_generates_error_rate_alert(self):
        self.agent.observe = MagicMock(return_value={
            "agents": {},
            "metrics": {"overall_failure_rate": 0.35},
            "recent_activities": []
        })
        self.agent.analyze = MagicMock(return_value={
            "summary": {"total_issues": 2},
            "issues": []
        })
        self.agent.health_metrics.get_health_score = MagicMock(return_value=0.9)

        result = self.agent._continuous_monitoring(config={"explicit_approval": True})

        error_alerts = [a for a in result["alerts"] if a["type"] == "error_rate"]
        assert len(error_alerts) == 1
        assert error_alerts[0]["severity"] == "critical"


# ═══════════════════════════════════════════════════════════════════
# RefactorEngine — AST-Based Analysis
# ═══════════════════════════════════════════════════════════════════

class TestRefactorEngineExtractFunctions:
    """Test extract_functions AST analysis."""

    def setup_method(self):
        from agents.builder.refactor_engine import RefactorEngine
        self.engine = RefactorEngine()

    def test_extract_functions_basic(self):
        code = 'def foo(x):\n    """Foo doc."""\n    return x\n\ndef bar(a, b):\n    return a + b\n\nasync def baz():\n    pass\n'
        result = self.engine.extract_functions(code)
        # extract_functions returns a List[Dict]
        assert len(result) == 3
        names = [f["name"] for f in result]
        assert "foo" in names
        assert "bar" in names
        assert "baz" in names

    def test_extract_functions_includes_args(self):
        code = 'def add(a, b):\n    return a + b\n'
        result = self.engine.extract_functions(code)
        assert len(result) == 1
        arg_names = [a["name"] for a in result[0]["args"]]
        assert "a" in arg_names
        assert "b" in arg_names

    def test_extract_functions_detects_async(self):
        code = 'async def async_fn():\n    pass\n'
        result = self.engine.extract_functions(code)
        assert result[0]["is_async"]

    def test_extract_functions_captures_docstring(self):
        code = 'def documented():\n    """My docstring."""\n    pass\n'
        result = self.engine.extract_functions(code)
        assert result[0]["docstring"] == "My docstring."


class TestRefactorEngineExtractImports:
    """Test extract_imports AST analysis."""

    def setup_method(self):
        from agents.builder.refactor_engine import RefactorEngine
        self.engine = RefactorEngine()

    def test_extract_simple_imports(self):
        code = 'import os\nimport sys\n'
        result = self.engine.extract_imports(code)
        modules = [i["module"] for i in result]
        assert "os" in modules
        assert "sys" in modules

    def test_extract_from_imports(self):
        code = 'from typing import Dict, List\n'
        result = self.engine.extract_imports(code)
        assert len(result) >= 1
        found = [i for i in result if i["module"] == "typing"]
        assert len(found) > 0
        assert "Dict" in found[0]["names"]
        assert "List" in found[0]["names"]

    def test_extract_aliased_imports(self):
        code = 'import numpy as np\n'
        result = self.engine.extract_imports(code)
        assert len(result) == 1
        assert result[0]["module"] == "numpy"
        assert result[0]["alias"] == "np"


class TestRefactorEngineAnalyzeComplexity:
    """Test analyze_complexity scoring."""

    def setup_method(self):
        from agents.builder.refactor_engine import RefactorEngine
        self.engine = RefactorEngine()

    def test_simple_function_low_complexity(self):
        code = 'def simple():\n    return 1\n'
        result = self.engine.analyze_complexity(code)
        assert "functions" in result
        assert len(result["functions"]) == 1
        assert result["functions"][0]["complexity"] >= 1

    def test_complex_function_higher_complexity(self):
        code = '''def complex_fn(x, items):
    total = 0
    for item in items:
        if item > 0:
            if item > 10:
                total += item
            else:
                total -= item
        elif item == 0:
            continue
        else:
            try:
                total += 1 / item
            except ZeroDivisionError:
                pass
    return total
'''
        result = self.engine.analyze_complexity(code)
        assert result["functions"][0]["complexity"] > 1

    def test_complexity_overall_metrics(self):
        code = 'def a():\n    if True:\n        pass\n\ndef b():\n    for x in range(10):\n        pass\n'
        result = self.engine.analyze_complexity(code)
        assert result["function_count"] == 2
        assert result["overall_complexity"] > 0
        assert result["max_complexity"] > 0


class TestRefactorEngineRemoveUnusedImports:
    """Test remove_unused_imports."""

    def setup_method(self):
        from agents.builder.refactor_engine import RefactorEngine
        self.engine = RefactorEngine()

    def test_remove_unused_import(self):
        code = 'import os\nimport sys\n\nprint(os.getcwd())\n'
        cleaned, removed = self.engine.remove_unused_imports(code)
        assert len(removed) > 0
        assert "sys" not in cleaned or "import sys" not in cleaned

    def test_keep_all_used_imports(self):
        code = 'import os\n\nprint(os.getcwd())\n'
        cleaned, removed = self.engine.remove_unused_imports(code)
        assert len(removed) == 0
        assert "import os" in cleaned

    def test_no_imports_returns_same(self):
        code = 'x = 1\nprint(x)\n'
        cleaned, removed = self.engine.remove_unused_imports(code)
        assert cleaned == code
        assert len(removed) == 0
