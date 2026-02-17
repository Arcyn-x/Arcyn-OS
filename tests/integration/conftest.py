"""
Integration test configuration.

These tests require a live Gemini API key and make real API calls.
They are NOT run by default with `pytest tests/`.

To run integration tests:
    python tests/integration/test_llm_gateway.py
    python tests/integration/forge_test.py
"""

import sys
from pathlib import Path

project_root = str(Path(__file__).parent.parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)
