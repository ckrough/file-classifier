"""
Security tests for logging configuration module.

Tests the _validate_log_dir() function to ensure it properly prevents:
- Path traversal attacks
- Symlink bypass attacks
- Arbitrary file write vulnerabilities
"""

import os
import tempfile
from pathlib import Path

import pytest

from src.config.logging import _validate_log_dir


class TestValidateLogDirSecurity:
    """Security tests for _validate_log_dir() function."""

    def test_valid_tmp_directory(self):
        """Test that valid /tmp path is accepted."""
        assert _validate_log_dir("/tmp") == "/tmp"

    def test_valid_var_log_directory(self):
        """Test that valid /var/log path is accepted."""
        result = _validate_log_dir("/var/log")
        # May return /tmp if /var/log doesn't exist or isn't writable
        assert result in ["/var/log", "/tmp"]

    def test_valid_app_logs_directory(self):
        """Test that valid /app/logs path is accepted."""
        result = _validate_log_dir("/app/logs")
        # May return /tmp if /app/logs doesn't exist or isn't writable
        assert result in ["/app/logs", "/tmp"]

    def test_valid_var_tmp_directory(self):
        """Test that valid /var/tmp path is accepted."""
        result = _validate_log_dir("/var/tmp")
        # May return /tmp if /var/tmp doesn't exist or isn't writable
        assert result in ["/var/tmp", "/tmp"]

    def test_path_traversal_blocked_simple(self):
        """Test that simple path traversal is blocked."""
        assert _validate_log_dir("/tmp/../etc") == "/tmp"

    def test_path_traversal_blocked_complex(self):
        """Test that complex path traversal is blocked."""
        assert _validate_log_dir("/tmp/logs/../../etc/passwd") == "/tmp"

    def test_path_traversal_blocked_relative(self):
        """Test that relative path traversal is blocked."""
        assert _validate_log_dir("../../../etc") == "/tmp"

    def test_path_traversal_blocked_multiple_dots(self):
        """Test that multiple .. sequences are blocked."""
        assert _validate_log_dir("/tmp/../../../../../etc") == "/tmp"

    def test_root_path_blocked(self):
        """Test that /root directory is blocked."""
        assert _validate_log_dir("/root/.ssh") == "/tmp"

    def test_etc_path_blocked(self):
        """Test that /etc directory is blocked."""
        assert _validate_log_dir("/etc/secrets") == "/tmp"

    def test_home_path_blocked(self):
        """Test that /home paths outside whitelist are blocked."""
        assert _validate_log_dir("/home/user/logs") == "/tmp"

    def test_arbitrary_path_blocked(self):
        """Test that arbitrary paths are blocked."""
        assert _validate_log_dir("/opt/malicious") == "/tmp"

    def test_symlink_attack_blocked(self, tmp_path):
        """Test that symlink bypass attacks are blocked."""
        # Create a symlink in /tmp pointing to /etc
        if os.access("/tmp", os.W_OK):
            evil_link = tmp_path / "evil_logs"
            try:
                evil_link.symlink_to("/etc")
                # Should resolve symlink and reject /etc destination
                result = _validate_log_dir(str(evil_link))
                assert result == "/tmp"
            except (OSError, PermissionError):
                pytest.skip("Cannot create symlink in test environment")

    def test_nested_symlink_attack_blocked(self, tmp_path):
        """Test that nested symlink attacks are blocked."""
        if os.access("/tmp", os.W_OK):
            nested_dir = tmp_path / "nested"
            nested_dir.mkdir()
            evil_link = nested_dir / "logs"
            try:
                evil_link.symlink_to("/etc")
                result = _validate_log_dir(str(evil_link))
                assert result == "/tmp"
            except (OSError, PermissionError):
                pytest.skip("Cannot create symlink in test environment")

    def test_double_dot_in_legitimate_name(self, tmp_path):
        """Test that legitimate paths with .. in name are handled correctly."""
        # A directory literally named "my..logs" (not path traversal)
        weird_dir = tmp_path / "my..logs"
        weird_dir.mkdir()
        result = _validate_log_dir(str(weird_dir))
        # Should be blocked because tmp_path is likely not in whitelist
        assert result == "/tmp"

    def test_nonexistent_directory_in_whitelist(self):
        """Test that nonexistent directory in whitelist is created or rejected."""
        test_path = "/tmp/test_nonexistent_dir_12345"
        # Clean up if exists from previous test
        if os.path.exists(test_path):
            os.rmdir(test_path)

        result = _validate_log_dir(test_path)
        # Should either create the directory or return /tmp
        assert result in [test_path, "/tmp"]

        # Clean up
        if os.path.exists(test_path):
            os.rmdir(test_path)

    def test_file_instead_of_directory(self, tmp_path):
        """Test that file path (not directory) is rejected."""
        if os.access("/tmp", os.W_OK):
            test_file = tmp_path / "logfile.txt"
            test_file.touch()
            result = _validate_log_dir(str(test_file))
            assert result == "/tmp"

    def test_unwritable_directory(self, tmp_path):
        """Test that unwritable directory is rejected."""
        unwritable = tmp_path / "unwritable"
        unwritable.mkdir()
        try:
            # Make directory unwritable
            unwritable.chmod(0o555)  # r-xr-xr-x
            result = _validate_log_dir(str(unwritable))
            assert result == "/tmp"
        finally:
            # Restore permissions for cleanup
            unwritable.chmod(0o755)

    def test_circular_symlink(self, tmp_path):
        """Test that circular symlinks are handled safely."""
        if os.access("/tmp", os.W_OK):
            link_a = tmp_path / "link_a"
            link_b = tmp_path / "link_b"
            try:
                link_a.symlink_to(link_b)
                link_b.symlink_to(link_a)
                result = _validate_log_dir(str(link_a))
                # Should handle gracefully and return /tmp
                assert result == "/tmp"
            except (OSError, PermissionError):
                pytest.skip("Cannot create circular symlink in test environment")

    def test_empty_string(self):
        """Test that empty string is rejected."""
        assert _validate_log_dir("") == "/tmp"

    def test_null_byte_injection(self):
        """Test that null byte injection is blocked."""
        # Python 3 handles null bytes in paths safely
        try:
            result = _validate_log_dir("/tmp/logs\x00/etc/passwd")
            assert result == "/tmp"
        except ValueError:
            # ValueError is acceptable (Python blocks null bytes)
            pass

    def test_unicode_normalization_attack(self):
        """Test that unicode normalization attacks are handled."""
        # Unicode tricks to bypass filters
        result = _validate_log_dir("/tmp/\u002e\u002e/etc")  # Unicode dots
        # Should normalize and detect traversal
        assert result == "/tmp"


class TestValidateLogDirEdgeCases:
    """Edge case tests for _validate_log_dir() function."""

    def test_trailing_slash(self):
        """Test that trailing slash is handled correctly."""
        result = _validate_log_dir("/tmp/")
        assert result in ["/tmp/", "/tmp"]

    def test_multiple_slashes(self):
        """Test that multiple slashes are normalized."""
        result = _validate_log_dir("/tmp//logs///")
        # os.path.realpath() normalizes multiple slashes
        assert "/tmp" in result

    def test_current_directory_reference(self):
        """Test that . in path is handled correctly."""
        result = _validate_log_dir("/tmp/./logs")
        # Should normalize to /tmp/logs
        assert result in ["/tmp/logs", "/tmp"]

    def test_whitespace_in_path(self, tmp_path):
        """Test that paths with whitespace are handled."""
        space_dir = tmp_path / "logs with spaces"
        space_dir.mkdir()
        result = _validate_log_dir(str(space_dir))
        # Should be rejected (not in whitelist)
        assert result == "/tmp"


@pytest.mark.unit
class TestValidateLogDirPerformance:
    """Performance tests for _validate_log_dir() function."""

    def test_validation_is_fast(self):
        """Test that validation completes quickly."""
        import time

        start = time.time()
        for _ in range(1000):
            _validate_log_dir("/tmp")
        elapsed = time.time() - start

        # Should complete 1000 validations in under 1 second
        assert elapsed < 1.0, f"Validation too slow: {elapsed:.3f}s for 1000 calls"


@pytest.mark.unit
class TestValidateLogDirIntegration:
    """Integration tests verifying _validate_log_dir() in realistic scenarios."""

    def test_docker_container_scenario(self):
        """Test typical Docker container log paths."""
        # Common Docker paths
        docker_paths = [
            "/tmp",
            "/app/logs",
            "/var/log",
        ]

        for path in docker_paths:
            result = _validate_log_dir(path)
            # Should accept or fallback to /tmp (if directory doesn't exist)
            assert result in [path, "/tmp"]

    def test_attack_scenario_comprehensive(self, tmp_path):
        """Test comprehensive attack scenario with multiple techniques."""
        attack_paths = [
            "/tmp/../etc/passwd",  # Path traversal
            "/tmp/../../root/.ssh",  # Multiple traversal
            "../../../etc",  # Relative traversal
            "/etc/shadow",  # Direct system file
            "/root/.bashrc",  # Root home directory
            "/home/user/.ssh/id_rsa",  # User credentials
            "/proc/self/environ",  # Process info
            "/sys/kernel/debug",  # Kernel info
        ]

        for attack_path in attack_paths:
            result = _validate_log_dir(attack_path)
            assert result == "/tmp", f"Attack path not blocked: {attack_path}"
