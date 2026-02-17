"""
REST API Server for Arcyn OS.

Provides HTTP endpoints for the Arcyn OS pipeline and agent system.

Endpoints:
    POST /api/execute       — Execute a goal through the full pipeline
    POST /api/classify      — Classify user intent (Persona only)
    POST /api/plan          — Create a plan (Architect only)
    GET  /api/status        — Get system status and agent health
    GET  /api/memory/search — Search memory entries
    GET  /api/health        — Health check

Usage:
    python -m api.server
    # http://localhost:8000/docs for interactive API docs
"""

import sys
import logging
from pathlib import Path
from typing import Any, Dict, Optional
from datetime import datetime

# Ensure project root on path
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

try:
    from fastapi import FastAPI, HTTPException
    from fastapi.middleware.cors import CORSMiddleware
    from pydantic import BaseModel, Field
    import uvicorn
    HAS_FASTAPI = True
except ImportError:
    HAS_FASTAPI = False

from core.orchestrator import Orchestrator


# =============================================================================
# Request/Response Models
# =============================================================================

if HAS_FASTAPI:

    class ExecuteRequest(BaseModel):
        """Request body for pipeline execution."""
        goal: str = Field(..., description="Natural language goal", min_length=1)
        verbose: bool = Field(False, description="Include detailed stage outputs")

    class ClassifyRequest(BaseModel):
        """Request body for intent classification."""
        input: str = Field(..., description="User input to classify", min_length=1)

    class PlanRequest(BaseModel):
        """Request body for plan creation."""
        goal: str = Field(..., description="Goal to plan for", min_length=1)

    class SearchRequest(BaseModel):
        """Request body for memory search."""
        pattern: str = Field(..., description="Search pattern")
        namespace: Optional[str] = Field(None, description="Namespace filter")
        limit: int = Field(50, description="Max results", ge=1, le=200)

    class CommandRequest(BaseModel):
        """Request body for command trigger."""
        command: str = Field(..., description="Command to execute", min_length=1)


# =============================================================================
# App Factory
# =============================================================================

def create_app() -> Any:
    """Create and configure the FastAPI application."""
    if not HAS_FASTAPI:
        raise ImportError(
            "FastAPI is required for the API server. "
            "Install with: pip install fastapi uvicorn"
        )

    app = FastAPI(
        title="Arcyn OS API",
        description="Multi-agent operating system for intelligent software development",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Shared orchestrator instance
    orch = Orchestrator(log_level=logging.INFO)

    # =========================================================================
    # Routes
    # =========================================================================

    @app.get("/")
    async def root():
        """Root endpoint."""
        return {
            "name": "Arcyn OS",
            "version": "1.0.0",
            "description": "AI-first multi-agent operating system",
            "docs": "/docs",
        }

    @app.get("/api/health")
    async def health():
        """Health check endpoint."""
        return {"status": "healthy", "timestamp": datetime.now().isoformat()}

    @app.get("/api/status")
    async def status():
        """Get system status and agent health."""
        try:
            return orch.get_status()
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @app.post("/api/execute")
    async def execute(request: ExecuteRequest):
        """Execute a goal through the full agent pipeline."""
        try:
            result = orch.execute(request.goal)
            if not request.verbose:
                # Strip large outputs for conciseness
                result.pop('outputs', None)
            return result
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @app.post("/api/classify")
    async def classify(request: ClassifyRequest):
        """Classify user intent via Persona Agent."""
        try:
            orch._ensure_agents()
            result = orch.classify(request.input)
            result.pop('_stage', None)
            return result
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @app.post("/api/plan")
    async def plan(request: PlanRequest):
        """Create a structured plan via Architect Agent."""
        try:
            orch._ensure_agents()
            classification = orch.classify(request.goal)
            result = orch.plan(classification)
            result.pop('_stage', None)
            return result
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @app.post("/api/command")
    async def command(request: CommandRequest):
        """Execute a command through the Command Trigger."""
        try:
            from core.command_trigger import trigger
            output = trigger(request.command)
            return {"command": request.command, "output": output}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @app.get("/api/memory/search")
    async def memory_search(pattern: str = "", namespace: Optional[str] = None,
                            limit: int = 50):
        """Search memory entries."""
        try:
            results = orch.memory.search(pattern, namespace=namespace, limit=limit)
            return {"results": results, "count": len(results)}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @app.get("/api/memory/stats")
    async def memory_stats():
        """Get memory usage statistics."""
        try:
            return orch.memory.get_stats()
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    return app


# =============================================================================
# Entry Point
# =============================================================================

def main():
    """Start the API server."""
    import argparse

    parser = argparse.ArgumentParser(description="Arcyn OS API Server")
    parser.add_argument('--host', default='0.0.0.0', help='Host to bind to')
    parser.add_argument('--port', type=int, default=8000, help='Port to listen on')
    parser.add_argument('--reload', action='store_true', help='Enable auto-reload')

    args = parser.parse_args()

    if not HAS_FASTAPI:
        print("ERROR: FastAPI is required. Install with:")
        print("  pip install fastapi uvicorn")
        sys.exit(1)

    app = create_app()

    print(f"\n{'=' * 60}")
    print(f"  Arcyn OS API Server")
    print(f"  http://{args.host}:{args.port}")
    print(f"  Docs: http://localhost:{args.port}/docs")
    print(f"{'=' * 60}\n")

    uvicorn.run(app, host=args.host, port=args.port, reload=args.reload)


if __name__ == '__main__':
    main()
