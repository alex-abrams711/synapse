"""File operations utilities."""
from pathlib import Path
from typing import List, Tuple
import shutil


class FileOperations:
    """Handles file copying and directory operations."""

    @staticmethod
    def copy_directory_with_conflicts(
        src_dir: Path,
        dst_dir: Path,
        force: bool = False
    ) -> Tuple[List[Path], List[Path], List[Path]]:
        """
        Copy directory contents with conflict detection.

        Args:
            src_dir: Source directory
            dst_dir: Destination directory
            force: Overwrite existing files

        Returns:
            Tuple of (copied_files, skipped_files, created_dirs)
        """
        copied_files: List[Path] = []
        skipped_files: List[Path] = []
        created_dirs: List[Path] = []

        # Create destination
        if not dst_dir.exists():
            dst_dir.mkdir(parents=True)
            created_dirs.append(dst_dir)

        # Walk source directory
        for src_item in src_dir.rglob("*"):
            if src_item == src_dir:
                continue

            rel_path = src_item.relative_to(src_dir)
            dst_item = dst_dir / rel_path

            if src_item.is_dir():
                if not dst_item.exists():
                    dst_item.mkdir(parents=True)
                    created_dirs.append(dst_item)
            else:
                if dst_item.exists():
                    if force:
                        shutil.copy2(src_item, dst_item)
                        copied_files.append(dst_item)
                    else:
                        skipped_files.append(dst_item)
                else:
                    shutil.copy2(src_item, dst_item)
                    copied_files.append(dst_item)

        return copied_files, skipped_files, created_dirs

    @staticmethod
    def cleanup_empty_directories(root_dir: Path) -> None:
        """
        Recursively remove empty directories.

        Args:
            root_dir: Root directory to clean up
        """
        if not root_dir.exists() or not root_dir.is_dir():
            return

        try:
            all_dirs = []
            for dir_path in root_dir.rglob("*"):
                if dir_path.is_dir():
                    all_dirs.append(dir_path)

            # Sort by depth (deepest first)
            all_dirs.sort(key=lambda x: len(x.parts), reverse=True)

            for dir_path in all_dirs:
                if dir_path.exists() and dir_path.is_dir():
                    try:
                        if dir_path != root_dir and not any(dir_path.iterdir()):
                            dir_path.rmdir()
                    except OSError:
                        pass
        except Exception:
            pass


# Singleton instance
_file_ops = FileOperations()


def get_file_operations() -> FileOperations:
    """Get the global file operations instance."""
    return _file_ops
