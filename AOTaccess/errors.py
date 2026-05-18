"""Exception types for AOTaccess.

Every error the API raises derives from :class:`AOTAccessError`, so callers can
catch the whole family with one ``except``. :class:`DataNotFoundError` also
subclasses the builtin ``FileNotFoundError`` — existing ``except
FileNotFoundError`` handlers keep working unchanged.
"""


class AOTAccessError(Exception):
    """Base class for all AOTaccess errors."""


class ConfigError(AOTAccessError):
    """A configuration problem — missing settings.yml, unknown path key, etc."""


class DataNotFoundError(AOTAccessError, FileNotFoundError):
    """A requested data file or directory does not exist on disk.

    The message should name the resolved path and the identifiers that produced
    it, so the caller can see exactly what was looked for.
    """
