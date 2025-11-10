#!/usr/bin/env python3
"""
Emergency repair script for when validation is completely stuck.
This should rarely be needed.
"""

import sys
import json
from pathlib import Path

def reset_validation_state():
    """Reset all validation state to allow work to continue"""
    synapse_dir = Path('.synapse')

    # Remove validation state
    state_file = synapse_dir / 'validation-state.json'
    if state_file.exists():
        state_file.unlink()
        print("✓ Removed validation state")

    # Remove continuation directive
    directive_file = synapse_dir / 'continue-directive.md'
    if directive_file.exists():
        directive_file.unlink()
        print("✓ Removed continuation directive")

    # Clear any validation logs
    log_file = synapse_dir / 'validation-log.txt'
    if log_file.exists():
        log_file.unlink()
        print("✓ Cleared validation log")

    print("\n✅ Validation state reset. You can now continue working.")
    print("⚠️  Warning: Quality issues may still exist and should be addressed.")

if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == '--force':
        reset_validation_state()
    else:
        print("Emergency Repair Tool")
        print("=" * 40)
        print("\nThis will reset validation state to escape a validation loop.")
        print("Use only if validation is stuck after multiple attempts.")
        print("\nUsage: python3 emergency_repair.py --force")
        print("\n⚠️  This does not fix the underlying issues!")
