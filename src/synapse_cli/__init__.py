#!/usr/bin/env python3
"""Synapse CLI - AI-first workflow system with quality gates.

This package provides a modular, clean architecture for managing
AI coding workflows with built-in quality gates and best practices.
"""

__version__ = "0.1.0"

# Public API exports
from .cli import main as cli_main
from .infrastructure.config_store import get_config_store
from .infrastructure.resources import get_resource_manager
from .services.workflow_service import get_workflow_service

# Backward compatibility alias
def main():
    """Main entry point (delegates to CLI)."""
    import sys
    sys.exit(cli_main())


# Export list for public API
__all__ = [
    # Entry points
    'main',
    'cli_main',
    # Infrastructure
    'get_config_store',
    'get_resource_manager',
    # Services
    'get_workflow_service',
    # Version
    '__version__'
]


if __name__ == "__main__":
    main()
