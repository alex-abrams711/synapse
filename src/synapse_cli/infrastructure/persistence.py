"""Base persistence layer."""
from pathlib import Path
from typing import Optional, TypeVar, Generic, Dict
import json
import sys

T = TypeVar('T')


class JsonStore(Generic[T]):
    """Generic JSON file storage."""

    def __init__(self, base_dir: str, filename: str):
        """
        Initialize JSON store.

        Args:
            base_dir: Directory name (e.g., ".synapse")
            filename: File name (e.g., "config.json")
        """
        self.base_dir = base_dir
        self.filename = filename

    def get_path(self, target_dir: Optional[Path] = None) -> Path:
        """
        Get full path to the JSON file.

        Args:
            target_dir: Target directory (defaults to current working directory)

        Returns:
            Full path to the JSON file
        """
        if target_dir is None:
            target_dir = Path.cwd()
        return target_dir / self.base_dir / self.filename

    def exists(self, target_dir: Optional[Path] = None) -> bool:
        """
        Check if file exists.

        Args:
            target_dir: Target directory (defaults to current working directory)

        Returns:
            True if file exists, False otherwise
        """
        return self.get_path(target_dir).exists()

    def load(self, target_dir: Optional[Path] = None) -> Optional[Dict]:
        """
        Load JSON file.

        Args:
            target_dir: Target directory (defaults to current working directory)

        Returns:
            Loaded JSON data as dict, or None if file doesn't exist or has errors
        """
        path = self.get_path(target_dir)

        if not path.exists():
            return None

        try:
            with open(path, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            print(f"Warning: Could not read {path}: {e}", file=sys.stderr)
            return None

    def save(self, data: Dict, target_dir: Optional[Path] = None) -> bool:
        """
        Save JSON file.

        Args:
            data: Data to save as JSON
            target_dir: Target directory (defaults to current working directory)

        Returns:
            True if save was successful, False otherwise
        """
        path = self.get_path(target_dir)

        # Ensure directory exists
        path.parent.mkdir(parents=True, exist_ok=True)

        try:
            # Validate can be serialized
            json_str = json.dumps(data, indent=2)

            # Write file
            with open(path, 'w') as f:
                f.write(json_str)
                f.write('\n')
            return True
        except (TypeError, ValueError, IOError) as e:
            print(f"Error: Could not write {path}: {e}", file=sys.stderr)
            return False
