# Arcyn OS Standards

This document defines system-wide standards for Arcyn OS.

## Naming Conventions

### Modules

- **Pattern**: snake_case
- **Description**: Module files use snake_case (e.g., memory_manager.py)
- **Examples**: memory_manager.py, context_manager.py, task_graph.py

### Classes

- **Pattern**: PascalCase
- **Description**: Classes use PascalCase (e.g., MemoryManager)
- **Examples**: MemoryManager, ContextManager, TaskGraph

### Functions

- **Pattern**: snake_case
- **Description**: Functions use snake_case (e.g., read_memory)
- **Examples**: read_memory, write_context, validate_task

### Constants

- **Pattern**: UPPER_SNAKE_CASE
- **Description**: Constants use UPPER_SNAKE_CASE (e.g., MAX_SIZE)
- **Examples**: MAX_SIZE, DEFAULT_TIMEOUT, API_VERSION

### Agents

- **Pattern**: PascalCase with Agent suffix
- **Description**: Agent classes end with 'Agent' (e.g., ArchitectAgent)
- **Examples**: ArchitectAgent, BuilderAgent, SystemDesignerAgent

## Folder Structure

### core

- **Path**: `core/`
- **Description**: Core system modules

### agents

- **Path**: `agents/{agent_name}/`
- **Description**: Agent implementations

### design

- **Path**: `design/`
- **Description**: Design artifacts and documentation

### backups

- **Path**: `backups/`
- **Description**: File backups

## Module Interfaces

### Required Exports

- **description**: All modules must export public API via __all__
- **pattern**: __all__ = ['Class1', 'Class2', 'function1']

### Docstrings

- **required**: True
- **format**: Google style
- **description**: All public classes and functions must have docstrings

### Type Hints

- **required**: True
- **description**: All function signatures must include type hints

## Versioning

### Semantic Versioning

- **pattern**: MAJOR.MINOR.PATCH
- **description**: Use semantic versioning (e.g., 1.2.3)
- **breaking_changes**: Increment MAJOR
- **new_features**: Increment MINOR
- **bug_fixes**: Increment PATCH

### Agent Versioning

- **format**: {agent_id}_v{version}
- **example**: architect_agent_v1.0.0

## Deprecation Policy

- **notice_period**: 2 minor versions

- **description**: Deprecated features must be announced 2 minor versions before removal

### Warnings

- **required**: True
- **format**: DeprecationWarning in code and documentation

### Migration Guide

- **required**: True
- **description**: Must provide migration guide for deprecated features
