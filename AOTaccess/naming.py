"""BIDS-style identifier formatting, shared across the access modules.

Subjects and runs are integers and get zero-padded. Sessions may be integers
(the main AOT task — ``ses-01`` … ``ses-10``) or strings (localizer sessions
such as ``pRF``, ``fLOC``, ``time``); :func:`fmt_ses` handles both. Each helper
also accepts an already-formatted value or a full ``sub-``/``ses-``/``run-``
token and returns the bare identifier, so callers can pass either form.
"""


def fmt_sub(sub):
    """Format a subject identifier: ``1`` -> ``'001'``, ``'sub-001'`` -> ``'001'``."""
    if isinstance(sub, int):
        return f"{sub:03d}"
    s = str(sub)
    return s[len("sub-"):] if s.startswith("sub-") else s


def fmt_ses(ses):
    """Format a session identifier: ``1`` -> ``'01'``, ``'pRF'`` -> ``'pRF'``.

    Integer sessions are zero-padded to two digits; string sessions (localizers
    such as ``'pRF'``, ``'fLOC'``, ``'time'``) pass through unchanged. A leading
    ``ses-`` is stripped.
    """
    if isinstance(ses, int):
        return f"{ses:02d}"
    s = str(ses)
    return s[len("ses-"):] if s.startswith("ses-") else s


def fmt_run(run):
    """Format a run identifier: ``1`` -> ``'01'``, ``'all'`` -> ``'all'``."""
    if isinstance(run, int):
        return f"{run:02d}"
    s = str(run)
    return s[len("run-"):] if s.startswith("run-") else s


def fmt_video(video):
    """Format a video identifier: ``1`` -> ``'0001'``."""
    if isinstance(video, int):
        return f"{video:04d}"
    return str(video)
