"""
Tests for new enhancements:
- PolicyEngine override merging
- CodeWriter add_class, add_import, generate_from_spec
- WebhookTrigger integration hooks
"""

import pytest
import tempfile
import os
from pathlib import Path


# ═══════════════════════════════════════════════════════════════════
# Policy Engine Override Merging
# ═══════════════════════════════════════════════════════════════════

class TestPolicyOverrideMerging:
    """Test that agent-specific overrides are properly merged."""

    def test_no_override_returns_base_policy(self):
        from core.llm_gateway.policy import PolicyEngine, Policy
        engine = PolicyEngine()
        effective = engine._get_effective_policy("Persona")
        assert effective is engine.policy

    def test_override_applies_max_tokens(self):
        from core.llm_gateway.policy import PolicyEngine, Policy
        engine = PolicyEngine()
        engine.set_agent_override("Builder", {"max_tokens_per_request": 16384})
        effective = engine._get_effective_policy("Builder")
        assert effective.max_tokens_per_request == 16384
        # Base policy unchanged
        assert engine.policy.max_tokens_per_request == 8192

    def test_override_applies_temperature(self):
        from core.llm_gateway.policy import PolicyEngine, Policy
        engine = PolicyEngine()
        engine.set_agent_override("Architect", {
            "max_temperature": 0.5,
            "default_temperature": 0.3
        })
        effective = engine._get_effective_policy("Architect")
        assert effective.max_temperature == 0.5
        assert effective.default_temperature == 0.3

    def test_override_ignores_invalid_fields(self):
        from core.llm_gateway.policy import PolicyEngine
        engine = PolicyEngine()
        engine.set_agent_override("Test", {
            "max_tokens_per_request": 4096,
            "nonexistent_field": "ignored"
        })
        effective = engine._get_effective_policy("Test")
        assert effective.max_tokens_per_request == 4096

    def test_override_with_no_valid_fields_returns_base(self):
        from core.llm_gateway.policy import PolicyEngine
        engine = PolicyEngine()
        engine.set_agent_override("Test", {"bogus": 42})
        effective = engine._get_effective_policy("Test")
        assert effective is engine.policy

    def test_multiple_agent_overrides_independent(self):
        from core.llm_gateway.policy import PolicyEngine
        engine = PolicyEngine()
        engine.set_agent_override("Builder", {"max_tokens_per_request": 16384})
        engine.set_agent_override("Knowledge", {"max_tokens_per_request": 32768})

        builder = engine._get_effective_policy("Builder")
        knowledge = engine._get_effective_policy("Knowledge")

        assert builder.max_tokens_per_request == 16384
        assert knowledge.max_tokens_per_request == 32768
        assert engine.policy.max_tokens_per_request == 8192


# ═══════════════════════════════════════════════════════════════════
# CodeWriter New Methods
# ═══════════════════════════════════════════════════════════════════

class TestCodeWriterAddImport:
    """Test CodeWriter.add_import method."""

    def setup_method(self):
        from agents.builder.code_writer import CodeWriter
        self.writer = CodeWriter()
        self.tmpdir = tempfile.mkdtemp()

    def _create_temp_file(self, content: str) -> str:
        path = os.path.join(self.tmpdir, "test_module.py")
        with open(path, "w") as f:
            f.write(content)
        return path

    def test_add_import_to_existing_file(self):
        path = self._create_temp_file("import os\n\nprint('hello')\n")
        result = self.writer.add_import(path, "import sys")
        assert result["success"]

        with open(path) as f:
            content = f.read()
        assert "import sys" in content

    def test_add_duplicate_import_is_idempotent(self):
        path = self._create_temp_file("import os\n\nprint('hello')\n")
        result = self.writer.add_import(path, "import os")
        assert result["success"]
        assert any("already exists" in w for w in result["warnings"])

    def test_add_import_to_file_without_imports(self):
        path = self._create_temp_file('"""Module."""\n\nprint("hello")\n')
        result = self.writer.add_import(path, "from typing import Dict")
        assert result["success"]

        with open(path) as f:
            content = f.read()
        assert "from typing import Dict" in content


class TestCodeWriterAddClass:
    """Test CodeWriter.add_class method."""

    def setup_method(self):
        from agents.builder.code_writer import CodeWriter
        self.writer = CodeWriter()
        self.tmpdir = tempfile.mkdtemp()

    def _create_temp_file(self, content: str) -> str:
        path = os.path.join(self.tmpdir, "test_module.py")
        with open(path, "w") as f:
            f.write(content)
        return path

    def test_add_class_to_file(self):
        path = self._create_temp_file("import os\n\n")
        class_code = "class NewClass:\n    pass"
        result = self.writer.add_class(path, class_code)
        assert result["success"]

        with open(path) as f:
            content = f.read()
        assert "class NewClass:" in content

    def test_add_duplicate_class_fails(self):
        path = self._create_temp_file("class Existing:\n    pass\n")
        result = self.writer.add_class(path, "class Existing:\n    pass")
        assert not result["success"]
        assert any("already exists" in e for e in result["errors"])


class TestCodeWriterGenerateFromSpec:
    """Test CodeWriter.generate_from_spec method."""

    def setup_method(self):
        from agents.builder.code_writer import CodeWriter
        self.writer = CodeWriter()
        self.tmpdir = tempfile.mkdtemp()

    def test_generate_simple_module(self):
        spec = {
            "file_path": os.path.join(self.tmpdir, "generated.py"),
            "module_docstring": "Auto-generated module.",
            "imports": ["from typing import Dict"],
            "classes": [{
                "name": "MyService",
                "docstring": "A service class.",
                "methods": [{
                    "name": "__init__",
                    "args": "self",
                    "docstring": "Initialize.",
                    "body": "self.ready = True"
                }]
            }]
        }
        result = self.writer.generate_from_spec(spec)
        assert result["success"]

        with open(spec["file_path"]) as f:
            content = f.read()
        assert "class MyService" in content
        assert "self.ready = True" in content
        assert "from typing import Dict" in content

    def test_generate_requires_file_path(self):
        result = self.writer.generate_from_spec({})
        assert not result["success"]


# ═══════════════════════════════════════════════════════════════════
# WebhookTrigger Integration Hooks
# ═══════════════════════════════════════════════════════════════════

class TestWebhookTrigger:
    """Test WebhookTrigger integration hooks."""

    def setup_method(self):
        from core.command_trigger import WebhookTrigger
        self.hook = WebhookTrigger()

    def test_from_voice(self):
        result = self.hook.from_voice("system status")
        assert result["success"]
        assert result["source"] == "voice"
        assert result["output"]

    def test_from_voice_empty(self):
        result = self.hook.from_voice("")
        assert not result["success"]
        assert result["source"] == "voice"

    def test_from_ui_button_known(self):
        result = self.hook.from_ui_button("btn_status")
        assert result["success"]
        assert result["source"] == "ui"
        assert result["command"] == "system status"

    def test_from_ui_button_unknown(self):
        result = self.hook.from_ui_button("btn_nonexistent")
        assert not result["success"]
        assert "available_buttons" in result

    def test_from_webhook(self):
        result = self.hook.from_webhook({
            "command": "system status",
            "source": "github"
        })
        assert result["success"]
        assert result["source"] == "github"
        assert result["output"]

    def test_from_webhook_missing_command(self):
        result = self.hook.from_webhook({"source": "test"})
        assert not result["success"]

    def test_from_chat_bot(self):
        result = self.hook.from_chat_bot("@arcyn system status", platform="slack")
        assert result["success"]
        assert result["source"] == "slack"

    def test_from_chat_bot_empty_after_strip(self):
        result = self.hook.from_chat_bot("@arcyn")
        assert not result["success"]

    def test_register_button(self):
        self.hook.register_button("btn_custom", "system status")
        result = self.hook.from_ui_button("btn_custom")
        assert result["success"]
        assert result["command"] == "system status"
