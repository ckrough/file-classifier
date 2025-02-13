"""Unit tests for cache configuration utilities."""


from unittest import mock
from src.config.cache_config import delete_cache, handle_signal, DB_FILE


@mock.patch('os.path.exists')
@mock.patch('os.remove')
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


@mock.patch('os.path.exists')
@mock.patch('os.remove')
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


@mock.patch('src.config.cache_config.delete_cache')
@mock.patch('sys.exit')
def test_handle_signal(mock_exit, mock_delete_cache):
    """
    Test that handle_signal deletes the cache and exits the program.
    """
    # Act: Call handle_signal
    handle_signal()

    # Assert: delete_cache called once and sys.exit called with 0
    mock_delete_cache.assert_called_once()
    mock_exit.assert_called_once_with(0)
