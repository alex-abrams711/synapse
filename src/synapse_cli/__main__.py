
#!/usr/bin/env python3
"""Main entry point for synapse_cli module."""

import sys

if __name__ == "__main__":
    try:
        # Try to use the new modular CLI
        from synapse_cli import cli_main
        sys.exit(cli_main())
    except (ImportError, AttributeError):
        # Fall back to legacy main if new CLI isn't available
        from synapse_cli import main
        main()
