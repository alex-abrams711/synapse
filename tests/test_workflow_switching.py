"""Test workflow switching functionality."""
import json
import os
import shutil
import tempfile
from pathlib import Path
from datetime import datetime
from io import StringIO
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from synapse_cli import (
    workflow_apply,
    load_manifest,
    load_config,
    get_resources_dir,
    __version__,
)


def test_workflow_switching():
    """Test that applying a new workflow removes the old workflow's files."""
    # Create temporary directory for testing
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        os.chdir(tmpdir)

        print(f"Testing in: {tmpdir}")

        # Step 1: Initialize synapse (manually to avoid interactive prompt)
        print("\n=== Step 1: Initialize synapse ===")
        synapse_dir = tmpdir / ".synapse"
        synapse_dir.mkdir(parents=True)

        # Create minimal config.json
        config = {
            "synapse_version": __version__,
            "initialized_at": "2024-11-16T00:00:00Z",
            "agent": {"type": "claude_code", "description": "Claude Code"},
            "project": {
                "name": "test-project",
                "root_directory": str(tmpdir.absolute())
            },
            "workflows": {
                "active_workflow": None,
                "applied_workflows": []
            },
            "quality-config": {},
            "third_party_workflow": {}
        }

        config_path = synapse_dir / "config.json"
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)
            f.write('\n')

        assert config_path.exists()
        print("✓ Synapse initialized")

        # Step 2: Apply first workflow (feature-implementation-v2)
        print("\n=== Step 2: Apply feature-implementation-v2 ===")
        workflow_apply("feature-implementation-v2")

        # Verify first workflow files exist
        manifest1 = load_manifest(tmpdir)
        assert manifest1 is not None
        assert manifest1['workflow_name'] == 'feature-implementation-v2'

        # Check specific files from feature-implementation-v2
        stop_hook = tmpdir / ".claude" / "hooks" / "stop_qa_check.py"
        enforcer_hook = tmpdir / ".claude" / "hooks" / "active-tasks-enforcer.py"

        assert stop_hook.exists(), "stop_qa_check.py should exist"
        assert enforcer_hook.exists(), "active-tasks-enforcer.py should exist"

        files_from_workflow1 = {f['path'] for f in manifest1['files_copied']}
        print(f"✓ Workflow 1 applied with {len(files_from_workflow1)} files")
        print(f"  Files: {files_from_workflow1}")

        # Step 3: Apply second workflow (feature-planning)
        print("\n=== Step 3: Apply feature-planning (should remove workflow 1) ===")

        # Mock stdin to answer 'y' to the workflow switch prompt
        old_stdin = sys.stdin
        sys.stdin = StringIO("y\n")
        try:
            workflow_apply("feature-planning")
        finally:
            sys.stdin = old_stdin

        # Verify second workflow files exist
        manifest2 = load_manifest(tmpdir)
        assert manifest2 is not None
        assert manifest2['workflow_name'] == 'feature-planning'

        files_from_workflow2 = {f['path'] for f in manifest2['files_copied']}
        print(f"✓ Workflow 2 applied with {len(files_from_workflow2)} files")
        print(f"  Files: {files_from_workflow2}")

        # Step 4: Verify workflow 1 files are removed
        print("\n=== Step 4: Verify workflow 1 files are removed ===")

        # Files that are unique to workflow 1 should be removed
        workflow1_unique = files_from_workflow1 - files_from_workflow2

        for file_path in workflow1_unique:
            full_path = tmpdir / file_path
            if not full_path.exists():
                print(f"  ✓ Correctly removed: {file_path}")
            else:
                print(f"  ✗ ERROR: File still exists: {file_path}")
                raise AssertionError(f"Workflow 1 file should be removed: {file_path}")

        # Step 5: Verify workflow 2 files exist
        print("\n=== Step 5: Verify workflow 2 files exist ===")

        for file_path in files_from_workflow2:
            full_path = tmpdir / file_path
            if full_path.exists():
                print(f"  ✓ Correctly present: {file_path}")
            else:
                print(f"  ✗ ERROR: File missing: {file_path}")
                raise AssertionError(f"Workflow 2 file should exist: {file_path}")

        # Step 6: Verify settings.json hooks are updated
        print("\n=== Step 6: Verify settings.json is updated ===")

        settings_path = tmpdir / ".claude" / "settings.json"
        if settings_path.exists():
            with open(settings_path) as f:
                settings = json.load(f)

            # Count hooks
            hook_count = 0
            if 'hooks' in settings:
                for hook_type, matchers in settings['hooks'].items():
                    for matcher in matchers:
                        hook_count += len(matcher.get('hooks', []))

            print(f"  ✓ Settings has {hook_count} hook(s)")

            # Verify no duplicate hooks from old workflow
            hook_commands = []
            if 'hooks' in settings:
                for hook_type, matchers in settings['hooks'].items():
                    for matcher in matchers:
                        for hook in matcher.get('hooks', []):
                            cmd = hook.get('command', '')
                            if cmd in hook_commands:
                                raise AssertionError(f"Duplicate hook found: {cmd}")
                            hook_commands.append(cmd)

            print(f"  ✓ No duplicate hooks found")

        # Step 7: Verify config tracks the new workflow
        print("\n=== Step 7: Verify config tracks new workflow ===")

        config = load_config(tmpdir)
        assert config['workflows']['active_workflow'] == 'feature-planning'
        print(f"  ✓ Active workflow: {config['workflows']['active_workflow']}")

        print("\n" + "=" * 60)
        print("✅ ALL TESTS PASSED!")
        print("=" * 60)


if __name__ == "__main__":
    test_workflow_switching()
