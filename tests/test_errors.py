"""Unit tests for the exception hierarchy."""

import pytest

from AOTaccess.errors import AOTAccessError, ConfigError, DataNotFoundError


def test_subclasses_share_a_base():
    assert issubclass(ConfigError, AOTAccessError)
    assert issubclass(DataNotFoundError, AOTAccessError)


def test_data_not_found_is_also_filenotfound():
    # legacy `except FileNotFoundError` handlers must keep catching it
    assert issubclass(DataNotFoundError, FileNotFoundError)
    with pytest.raises(FileNotFoundError):
        raise DataNotFoundError("missing")
    with pytest.raises(AOTAccessError):
        raise DataNotFoundError("missing")
