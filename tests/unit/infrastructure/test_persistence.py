"""Unit tests for infrastructure/persistence.py."""
import pytest
import json
import tempfile
from pathlib import Path
from synapse_cli.infrastructure.persistence import JsonStore


class TestJsonStore:
    """Test JsonStore generic class."""

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for testing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def json_store(self):
        """Create JsonStore instance for testing."""
        return JsonStore(".synapse", "test.json")

    def test_get_path_default(self, json_store):
        """Test get_path with default target directory."""
        path = json_store.get_path()
        assert path == Path.cwd() / ".synapse" / "test.json"

    def test_get_path_custom_dir(self, json_store, temp_dir):
        """Test get_path with custom target directory."""
        path = json_store.get_path(temp_dir)
        assert path == temp_dir / ".synapse" / "test.json"

    def test_exists_missing_file(self, json_store, temp_dir):
        """Test exists returns False when file doesn't exist."""
        assert json_store.exists(temp_dir) is False

    def test_exists_existing_file(self, json_store, temp_dir):
        """Test exists returns True when file exists."""
        # Create the file
        file_path = temp_dir / ".synapse" / "test.json"
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text('{}')

        assert json_store.exists(temp_dir) is True

    def test_load_missing_file(self, json_store, temp_dir):
        """Test load returns None when file doesn't exist."""
        result = json_store.load(temp_dir)
        assert result is None

    def test_load_valid_json(self, json_store, temp_dir):
        """Test load with valid JSON file."""
        # Create test data
        test_data = {
            'key': 'value',
            'number': 42,
            'nested': {'inner': 'data'}
        }

        # Write file
        file_path = temp_dir / ".synapse" / "test.json"
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(json.dumps(test_data))

        # Load and verify
        result = json_store.load(temp_dir)
        assert result == test_data

    def test_load_invalid_json(self, json_store, temp_dir, capsys):
        """Test load with invalid JSON returns None and prints warning."""
        # Create invalid JSON file
        file_path = temp_dir / ".synapse" / "test.json"
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text('invalid json {')

        # Load should return None
        result = json_store.load(temp_dir)
        assert result is None

        # Check warning was printed to stderr
        captured = capsys.readouterr()
        assert "Warning: Could not read" in captured.err

    def test_save_creates_directory(self, json_store, temp_dir):
        """Test save creates parent directory if it doesn't exist."""
        test_data = {'key': 'value'}

        # Directory doesn't exist yet
        assert not (temp_dir / ".synapse").exists()

        # Save should create directory
        result = json_store.save(test_data, temp_dir)
        assert result is True
        assert (temp_dir / ".synapse").exists()
        assert (temp_dir / ".synapse" / "test.json").exists()

    def test_save_valid_data(self, json_store, temp_dir):
        """Test save with valid data."""
        test_data = {
            'key': 'value',
            'number': 42,
            'nested': {'inner': 'data'}
        }

        # Save
        result = json_store.save(test_data, temp_dir)
        assert result is True

        # Verify file contents
        file_path = temp_dir / ".synapse" / "test.json"
        with open(file_path, 'r') as f:
            saved_data = json.load(f)
        assert saved_data == test_data

    def test_save_load_roundtrip(self, json_store, temp_dir):
        """Test save and load roundtrip."""
        test_data = {
            'string': 'test',
            'number': 123,
            'boolean': True,
            'array': [1, 2, 3],
            'nested': {'key': 'value'}
        }

        # Save
        save_result = json_store.save(test_data, temp_dir)
        assert save_result is True

        # Load
        loaded_data = json_store.load(temp_dir)
        assert loaded_data == test_data

    def test_save_invalid_data(self, json_store, temp_dir, capsys):
        """Test save with non-serializable data returns False."""
        # Create non-serializable data (e.g., set)
        test_data = {'key': {1, 2, 3}}  # set is not JSON serializable

        # Save should return False
        result = json_store.save(test_data, temp_dir)
        assert result is False

        # Check error was printed to stderr
        captured = capsys.readouterr()
        assert "Error: Could not write" in captured.err

    def test_save_overwrites_existing_file(self, json_store, temp_dir):
        """Test save overwrites existing file."""
        # Create initial file
        file_path = temp_dir / ".synapse" / "test.json"
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text('{"old": "data"}')

        # Save new data
        new_data = {'new': 'data'}
        result = json_store.save(new_data, temp_dir)
        assert result is True

        # Verify new data
        loaded_data = json_store.load(temp_dir)
        assert loaded_data == new_data
        assert 'old' not in loaded_data

    def test_save_formats_json_with_indent(self, json_store, temp_dir):
        """Test save formats JSON with indentation."""
        test_data = {'key': 'value', 'nested': {'inner': 'data'}}

        # Save
        json_store.save(test_data, temp_dir)

        # Read raw file contents
        file_path = temp_dir / ".synapse" / "test.json"
        content = file_path.read_text()

        # Check for indentation (should have newlines and spaces)
        assert '\n' in content
        assert '  ' in content  # indent=2

    def test_different_base_dir_and_filename(self, temp_dir):
        """Test JsonStore with different base_dir and filename."""
        store = JsonStore(".config", "settings.json")
        test_data = {'setting': 'value'}

        # Save
        result = store.save(test_data, temp_dir)
        assert result is True

        # Verify path
        expected_path = temp_dir / ".config" / "settings.json"
        assert expected_path.exists()

        # Load
        loaded = store.load(temp_dir)
        assert loaded == test_data
