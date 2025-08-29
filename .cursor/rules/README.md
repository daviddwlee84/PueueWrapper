# Cursor Rules for PueueWrapper

This directory contains Cursor Rules to help with PueueWrapper development. These rules provide guidance on project structure, coding standards, and development workflow.

## Available Rules

1. **project-structure.mdc** - Project layout and organization guidelines
2. **python-development.mdc** - Python-specific development standards  
3. **pueue-wrapper-architecture.mdc** - Architecture and implementation details
4. **uv-commands.mdc** - UV package manager commands and workflow
5. **code-style.mdc** - Code style and documentation guidelines

## Rule Application

- **Always Applied**: `project-structure.mdc` is automatically applied to all requests
- **Python Files**: `python-development.mdc` and `code-style.mdc` apply to `.py` files
- **Manual**: Architecture and UV command rules can be manually triggered when needed

## Key Guidelines Summary

- **Comments**: Write in English
- **User-facing text**: Use Traditional Chinese (繁體中文)
- **Package Manager**: Use UV exclusively
- **Virtual Environment**: Always activate with `source .venv/bin/activate` before running scripts
- **Code Organization**:
  - Source code in `src/`
  - Documentation in `docs/`
  - Examples in `examples/`
