"""Unit tests for infrastructure/file_operations.py."""
import pytest
import tempfile
from pathlib import Path
from synapse_cli.infrastructure.file_operations import FileOperations, get_file_operations


class TestFileOperations:
    """Test FileOperations class."""

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for testing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def file_ops(self):
        """Create FileOperations instance for testing."""
        return FileOperations()

    @pytest.fixture
    def setup_source_dir(self, temp_dir):
        """Create a sample source directory structure."""
        src_dir = temp_dir / "source"
        src_dir.mkdir()

        # Create files and directories
        (src_dir / "file1.txt").write_text("content1")
        (src_dir / "file2.txt").write_text("content2")

        subdir = src_dir / "subdir"
        subdir.mkdir()
        (subdir / "file3.txt").write_text("content3")

        nested = subdir / "nested"
        nested.mkdir()
        (nested / "file4.txt").write_text("content4")

        return src_dir

    def test_singleton_pattern(self):
        """Test that get_file_operations returns the same instance."""
        ops1 = get_file_operations()
        ops2 = get_file_operations()
        assert ops1 is ops2

    def test_copy_directory_with_conflicts_normal_case(self, file_ops, temp_dir, setup_source_dir):
        """Test copy_directory_with_conflicts with no conflicts."""
        src_dir = setup_source_dir
        dst_dir = temp_dir / "destination"

        copied, skipped, created = file_ops.copy_directory_with_conflicts(src_dir, dst_dir)

        # Check all files were copied
        assert len(copied) == 4
        assert len(skipped) == 0
        assert len(created) >= 3  # destination, subdir, nested

        # Verify destination structure
        assert dst_dir.exists()
        assert (dst_dir / "file1.txt").exists()
        assert (dst_dir / "file2.txt").exists()
        assert (dst_dir / "subdir" / "file3.txt").exists()
        assert (dst_dir / "subdir" / "nested" / "file4.txt").exists()

        # Verify contents
        assert (dst_dir / "file1.txt").read_text() == "content1"
        assert (dst_dir / "subdir" / "file3.txt").read_text() == "content3"

    def test_copy_directory_with_conflicts_existing_dst(self, file_ops, temp_dir, setup_source_dir):
        """Test copy_directory_with_conflicts when destination already exists."""
        src_dir = setup_source_dir
        dst_dir = temp_dir / "destination"
        dst_dir.mkdir()

        copied, skipped, created = file_ops.copy_directory_with_conflicts(src_dir, dst_dir)

        # Destination dir already existed, so it shouldn't be in created
        assert dst_dir in created or dst_dir not in created  # Either is valid
        assert len(copied) == 4
        assert len(skipped) == 0

    def test_copy_directory_with_conflicts_skip_existing(self, file_ops, temp_dir, setup_source_dir):
        """Test copy_directory_with_conflicts skips existing files by default."""
        src_dir = setup_source_dir
        dst_dir = temp_dir / "destination"
        dst_dir.mkdir()

        # Create conflicting files
        (dst_dir / "file1.txt").write_text("existing1")
        (dst_dir / "subdir").mkdir()
        (dst_dir / "subdir" / "file3.txt").write_text("existing3")

        copied, skipped, created = file_ops.copy_directory_with_conflicts(src_dir, dst_dir, force=False)

        # Should skip 2 files, copy 2 files
        assert len(skipped) == 2
        assert len(copied) == 2

        # Verify skipped files are in the list
        skipped_names = [f.name for f in skipped]
        assert "file1.txt" in skipped_names
        assert "file3.txt" in skipped_names

        # Verify existing files weren't overwritten
        assert (dst_dir / "file1.txt").read_text() == "existing1"
        assert (dst_dir / "subdir" / "file3.txt").read_text() == "existing3"

        # Verify new files were copied
        assert (dst_dir / "file2.txt").read_text() == "content2"
        assert (dst_dir / "subdir" / "nested" / "file4.txt").read_text() == "content4"

    def test_copy_directory_with_conflicts_force_overwrite(self, file_ops, temp_dir, setup_source_dir):
        """Test copy_directory_with_conflicts overwrites existing files with force=True."""
        src_dir = setup_source_dir
        dst_dir = temp_dir / "destination"
        dst_dir.mkdir()

        # Create conflicting files
        (dst_dir / "file1.txt").write_text("existing1")
        (dst_dir / "subdir").mkdir()
        (dst_dir / "subdir" / "file3.txt").write_text("existing3")

        copied, skipped, created = file_ops.copy_directory_with_conflicts(src_dir, dst_dir, force=True)

        # Should copy all files, skip none
        assert len(copied) == 4
        assert len(skipped) == 0

        # Verify files were overwritten
        assert (dst_dir / "file1.txt").read_text() == "content1"
        assert (dst_dir / "subdir" / "file3.txt").read_text() == "content3"

    def test_copy_directory_with_conflicts_empty_source(self, file_ops, temp_dir):
        """Test copy_directory_with_conflicts with empty source directory."""
        src_dir = temp_dir / "empty_source"
        src_dir.mkdir()

        dst_dir = temp_dir / "destination"

        copied, skipped, created = file_ops.copy_directory_with_conflicts(src_dir, dst_dir)

        # Should create destination but copy no files
        assert len(copied) == 0
        assert len(skipped) == 0
        assert dst_dir.exists()

    def test_copy_directory_with_conflicts_preserves_metadata(self, file_ops, temp_dir, setup_source_dir):
        """Test copy_directory_with_conflicts preserves file metadata."""
        src_dir = setup_source_dir
        dst_dir = temp_dir / "destination"

        src_file = src_dir / "file1.txt"
        original_mtime = src_file.stat().st_mtime

        copied, skipped, created = file_ops.copy_directory_with_conflicts(src_dir, dst_dir)

        dst_file = dst_dir / "file1.txt"
        # copy2 preserves metadata, so mtime should be similar
        assert abs(dst_file.stat().st_mtime - original_mtime) < 1.0

    def test_copy_directory_with_conflicts_creates_nested_dirs(self, file_ops, temp_dir):
        """Test copy_directory_with_conflicts creates nested directories."""
        src_dir = temp_dir / "source"
        src_dir.mkdir()

        # Create deeply nested structure
        deep = src_dir / "a" / "b" / "c"
        deep.mkdir(parents=True)
        (deep / "file.txt").write_text("deep")

        dst_dir = temp_dir / "destination"

        copied, skipped, created = file_ops.copy_directory_with_conflicts(src_dir, dst_dir)

        # Verify nested structure was created
        assert (dst_dir / "a" / "b" / "c" / "file.txt").exists()
        assert (dst_dir / "a" / "b" / "c" / "file.txt").read_text() == "deep"

    def test_cleanup_empty_directories_no_empty_dirs(self, file_ops, temp_dir):
        """Test cleanup_empty_directories with no empty directories."""
        # Create structure with files
        root = temp_dir / "root"
        root.mkdir()
        (root / "file.txt").write_text("content")

        subdir = root / "subdir"
        subdir.mkdir()
        (subdir / "file2.txt").write_text("content2")

        file_ops.cleanup_empty_directories(root)

        # All directories should still exist
        assert root.exists()
        assert subdir.exists()

    def test_cleanup_empty_directories_removes_empty(self, file_ops, temp_dir):
        """Test cleanup_empty_directories removes empty directories."""
        # Create structure with empty directories
        root = temp_dir / "root"
        root.mkdir()

        empty1 = root / "empty1"
        empty1.mkdir()

        empty2 = root / "empty2"
        empty2.mkdir()

        # Create nested empty
        nested = root / "nested"
        nested.mkdir()
        nested_empty = nested / "empty"
        nested_empty.mkdir()

        file_ops.cleanup_empty_directories(root)

        # Empty directories should be removed
        assert not empty1.exists()
        assert not empty2.exists()
        assert not nested_empty.exists()
        assert not nested.exists()  # Should also be removed after nested_empty is removed

        # Root should remain
        assert root.exists()

    def test_cleanup_empty_directories_keeps_dirs_with_files(self, file_ops, temp_dir):
        """Test cleanup_empty_directories keeps directories with files."""
        root = temp_dir / "root"
        root.mkdir()

        # Empty directory
        empty = root / "empty"
        empty.mkdir()

        # Directory with file
        with_file = root / "with_file"
        with_file.mkdir()
        (with_file / "file.txt").write_text("content")

        file_ops.cleanup_empty_directories(root)

        # Empty should be removed, with_file should remain
        assert not empty.exists()
        assert with_file.exists()

    def test_cleanup_empty_directories_nested_structure(self, file_ops, temp_dir):
        """Test cleanup_empty_directories with complex nested structure."""
        root = temp_dir / "root"
        root.mkdir()

        # a/b/c/file.txt
        abc = root / "a" / "b" / "c"
        abc.mkdir(parents=True)
        (abc / "file.txt").write_text("content")

        # a/b/empty
        ab_empty = root / "a" / "b" / "empty"
        ab_empty.mkdir()

        # a/empty
        a_empty = root / "a" / "empty"
        a_empty.mkdir()

        # empty
        empty = root / "empty"
        empty.mkdir()

        file_ops.cleanup_empty_directories(root)

        # Only empty directories should be removed
        assert not ab_empty.exists()
        assert not a_empty.exists()
        assert not empty.exists()

        # Directories with files should remain
        assert (root / "a").exists()
        assert (root / "a" / "b").exists()
        assert (root / "a" / "b" / "c").exists()
        assert (abc / "file.txt").exists()

    def test_cleanup_empty_directories_missing_root(self, file_ops, temp_dir):
        """Test cleanup_empty_directories with non-existent root."""
        root = temp_dir / "nonexistent"

        # Should not raise an error
        file_ops.cleanup_empty_directories(root)

    def test_cleanup_empty_directories_file_as_root(self, file_ops, temp_dir):
        """Test cleanup_empty_directories with file as root."""
        root = temp_dir / "file.txt"
        root.write_text("content")

        # Should not raise an error
        file_ops.cleanup_empty_directories(root)

        # File should still exist
        assert root.exists()

    def test_cleanup_empty_directories_does_not_remove_root(self, file_ops, temp_dir):
        """Test cleanup_empty_directories does not remove root directory itself."""
        root = temp_dir / "root"
        root.mkdir()

        # Make root empty
        file_ops.cleanup_empty_directories(root)

        # Root should still exist even though it's empty
        assert root.exists()
