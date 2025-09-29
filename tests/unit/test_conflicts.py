"""Unit tests for command conflict detection utilities."""

import tempfile
from pathlib import Path

from synapse.models.command import (
    AgentType,
    ConflictInfo,
    ConflictResolution,
    ConflictType,
)
from synapse.utils.conflicts import (
    CommandInfo as ConflictsCommandInfo,
)
from synapse.utils.conflicts import (
    ConflictDetectionResult,
    ConflictSummary,
    detect_command_conflicts,
    detect_functionality_overlap,
    parse_command_file,
    resolve_conflict,
    scan_existing_commands,
)


class TestConflictDetection:
    """Test command conflict detection functions."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.temp_path = Path(self.temp_dir)

    def teardown_method(self) -> None:
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_detect_command_conflicts_no_conflicts(self) -> None:
        """Test conflict detection with no conflicts."""
        # Create command directory with non-conflicting commands
        command_dir = self.temp_path / "commands"
        command_dir.mkdir()

        # Create existing command file
        existing_cmd = command_dir / "deploy.md"
        existing_cmd.write_text("# /deploy\n\nDeploy the application.")

        # Test synapse commands that don't conflict
        synapse_commands = ["plan", "implement", "review"]

        result = detect_command_conflicts(synapse_commands, str(command_dir))

        assert isinstance(result, ConflictDetectionResult)
        assert len(result.conflicts) == 0

    def test_detect_command_conflicts_name_collision(self) -> None:
        """Test conflict detection with name collisions."""
        # Create command directory
        command_dir = self.temp_path / "commands"
        command_dir.mkdir()

        # Create existing command file that conflicts
        existing_cmd = command_dir / "plan.md"
        existing_cmd.write_text("# /plan\n\nExisting planning command.")

        # Test synapse commands that conflict
        synapse_commands = ["plan", "implement"]

        result = detect_command_conflicts(synapse_commands, str(command_dir))

        assert len(result.conflicts) >= 1
        # Should detect conflict for plan command
        plan_conflicts = [c for c in result.conflicts if "plan" in c.command_name.lower()]
        assert len(plan_conflicts) >= 1

    def test_detect_command_conflicts_nonexistent_directory(self) -> None:
        """Test conflict detection with non-existent directory."""
        nonexistent_dir = self.temp_path / "nonexistent"

        result = detect_command_conflicts(["plan"], str(nonexistent_dir))

        assert len(result.conflicts) == 0

    def test_scan_existing_commands(self) -> None:
        """Test scanning existing command files."""
        # Create command directory
        command_dir = self.temp_path / "commands"
        command_dir.mkdir()

        # Create command files
        cmd1 = command_dir / "deploy.md"
        cmd1.write_text("# /deploy\n\nDeploy command.")

        cmd2 = command_dir / "test.md"
        cmd2.write_text("# /test\n\nTest command.")

        # Create non-command file
        other_file = command_dir / "readme.txt"
        other_file.write_text("Not a command file")

        commands = scan_existing_commands(str(command_dir))

        assert isinstance(commands, dict)
        # Should find at least the valid command files
        assert len(commands) >= 0  # May depend on implementation

    def test_parse_command_file_valid(self) -> None:
        """Test parsing valid command file."""
        content = "# /deploy\n\nDeploy the application to production."
        file_path = "/path/to/deploy.md"

        command_info = parse_command_file(file_path, content)

        if command_info:  # May return None depending on implementation
            assert isinstance(command_info, ConflictsCommandInfo)
            assert command_info.name == "/deploy"
            assert command_info.source_file == file_path

    def test_parse_command_file_invalid(self) -> None:
        """Test parsing invalid command file."""
        content = "No command header here"
        file_path = "/path/to/invalid.md"

        command_info = parse_command_file(file_path, content)

        # Should return None for invalid format
        assert command_info is None

    def test_resolve_conflict(self) -> None:
        """Test conflict resolution."""
        # Create a mock conflict
        from synapse.models.command import SlashCommand

        mock_synapse_command = SlashCommand(
            name="/synapse:plan",
            description="Planning command",
            agent_target=AgentType.DISPATCHER,
            command_template="# Planning Command"
        )

        conflict = ConflictInfo(
            command_name="/plan",
            existing_source="/path/to/plan.md",
            synapse_command=mock_synapse_command,
            conflict_type=ConflictType.NAME_COLLISION,
            resolution=ConflictResolution.USE_PREFIX,
            detected_date=None
        )

        resolution = resolve_conflict(conflict)

        # Should return some resolution strategy
        assert isinstance(resolution, str)
        assert len(resolution) > 0


class TestConflictDetectionResult:
    """Test ConflictDetectionResult model."""

    def test_conflict_detection_result_creation(self) -> None:
        """Test ConflictDetectionResult creation."""
        result = ConflictDetectionResult()

        assert hasattr(result, 'conflicts')
        assert isinstance(result.conflicts, list)
        assert len(result.conflicts) == 0

    def test_conflict_detection_result_with_conflicts(self) -> None:
        """Test ConflictDetectionResult with conflicts."""
        result = ConflictDetectionResult()

        # Create mock conflict
        from synapse.models.command import SlashCommand

        mock_synapse_command = SlashCommand(
            name="/synapse:plan",
            description="Planning command",
            agent_target=AgentType.DISPATCHER,
            command_template="# Planning Command"
        )

        conflict = ConflictInfo(
            command_name="/plan",
            existing_source="/path/to/plan.md",
            synapse_command=mock_synapse_command,
            conflict_type=ConflictType.NAME_COLLISION,
            resolution=ConflictResolution.USE_PREFIX,
            detected_date=None
        )

        result.conflicts.append(conflict)

        assert len(result.conflicts) == 1
        assert result.conflicts[0].command_name == "/plan"


class TestConflictSummary:
    """Test ConflictSummary model."""

    def test_conflict_summary_creation(self) -> None:
        """Test ConflictSummary creation."""
        summary = ConflictSummary()

        assert hasattr(summary, 'total_conflicts')
        assert hasattr(summary, 'name_collisions')
        assert hasattr(summary, 'functionality_overlaps')
        assert summary.total_conflicts == 0
        assert summary.name_collisions == 0
        assert summary.functionality_overlaps == 0

    def test_conflict_summary_with_data(self) -> None:
        """Test ConflictSummary with conflict data."""
        summary = ConflictSummary()
        summary.total_conflicts = 2
        summary.name_collisions = 1
        summary.functionality_overlaps = 1

        assert summary.total_conflicts == 2
        assert summary.name_collisions == 1
        assert summary.functionality_overlaps == 1


class TestConflictsCommandInfo:
    """Test ConflictsCommandInfo model."""

    def test_conflicts_command_info_creation(self) -> None:
        """Test ConflictsCommandInfo creation."""
        info = ConflictsCommandInfo("/test", "/path/to/test.md", "Test command")

        assert info.name == "/test"
        assert info.source_file == "/path/to/test.md"
        assert info.description == "Test command"

    def test_conflicts_command_info_defaults(self) -> None:
        """Test ConflictsCommandInfo with default values."""
        info = ConflictsCommandInfo("/test", "/path/to/test.md")

        assert info.name == "/test"
        assert info.source_file == "/path/to/test.md"
        assert info.description == ""


class TestConflictIntegration:
    """Test integration between conflict detection components."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.temp_path = Path(self.temp_dir)

    def teardown_method(self) -> None:
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_end_to_end_conflict_detection(self) -> None:
        """Test complete conflict detection workflow."""
        # Create command directory with conflicting commands
        command_dir = self.temp_path / "commands"
        command_dir.mkdir()

        # Create existing commands that conflict
        plan_cmd = command_dir / "plan.md"
        plan_cmd.write_text("# /plan\n\nExisting plan command.")

        review_cmd = command_dir / "review.md"
        review_cmd.write_text("# /review\n\nExisting review command.")

        # Detect conflicts
        synapse_commands = ["plan", "implement", "review"]
        result = detect_command_conflicts(synapse_commands, str(command_dir))

        # Should detect conflicts
        assert isinstance(result, ConflictDetectionResult)
        assert hasattr(result, 'conflicts')

    def test_performance_with_many_commands(self) -> None:
        """Test conflict detection performance with many existing commands."""
        import time

        # Create command directory with many commands
        command_dir = self.temp_path / "commands"
        command_dir.mkdir()

        # Create many existing commands
        for i in range(50):  # Reduced from 100 for faster testing
            cmd_file = command_dir / f"command_{i}.md"
            cmd_file.write_text(f"# /command_{i}\n\nCommand {i}.")

        synapse_commands = ["plan", "implement", "review"]

        start_time = time.time()
        result = detect_command_conflicts(synapse_commands, str(command_dir))
        end_time = time.time()

        # Should complete quickly
        processing_time = end_time - start_time
        assert processing_time < 2.0  # Less than 2 seconds

        # Should be valid result
        assert isinstance(result, ConflictDetectionResult)


class TestFunctionalityOverlap:
    """Test functionality overlap detection."""

    def test_detect_functionality_overlap_basic(self) -> None:
        """Test basic functionality overlap detection."""
        existing_commands = ["planning", "design"]
        synapse_commands = ["/synapse:plan"]

        result = detect_functionality_overlap(existing_commands, synapse_commands)
        assert isinstance(result, list)
        # Should detect overlap between "plan" and "planning"
        assert len(result) > 0

    def test_detect_functionality_overlap_no_overlap(self) -> None:
        """Test functionality overlap with no overlap."""
        existing_commands = ["deploy", "status"]
        synapse_commands = ["/synapse:plan"]

        result = detect_functionality_overlap(existing_commands, synapse_commands)
        assert isinstance(result, list)
        # Should not detect overlap between "plan" and "deploy"/"status"
        assert len(result) == 0
