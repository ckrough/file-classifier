"""Unit tests for cache configuration utilities."""

from unittest import mock
from src.storage.cache import delete_cache
from src.config.settings import DB_FILE


@mock.patch("os.path.exists")
@mock.patch("os.remove")
def test_delete_cache_exists(mock_remove, mock_exists):
    """
    Test that delete_cache successfully deletes the cache file when it exists.
    """
    # Arrange: Simulate that DB_FILE exists
    mock_exists.return_value = True

    # Act: Call delete_cache
    delete_cache()

    # Assert: os.path.exists called with DB_FILE and os.remove called with DB_FILE
    mock_exists.assert_called_once_with(DB_FILE)
    mock_remove.assert_called_once_with(DB_FILE)


@mock.patch("os.path.exists")
@mock.patch("os.remove")
def test_delete_cache_not_exists(mock_remove, mock_exists):
    """
    Test that delete_cache does nothing when the cache file does not exist.
    """
    # Arrange: Simulate that DB_FILE does not exist
    mock_exists.return_value = False

    # Act: Call delete_cache
    delete_cache()

    # Assert: os.path.exists called with DB_FILE and os.remove was not called
    mock_exists.assert_called_once_with(DB_FILE)
    mock_remove.assert_not_called()
