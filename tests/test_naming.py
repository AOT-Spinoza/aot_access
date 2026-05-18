"""Unit tests for the BIDS identifier formatting helpers."""

from AOTaccess.naming import fmt_sub, fmt_ses, fmt_run, fmt_video


def test_fmt_sub_zero_pads_int():
    assert fmt_sub(1) == "001"
    assert fmt_sub(42) == "042"


def test_fmt_sub_strips_prefix_and_passes_strings():
    assert fmt_sub("sub-007") == "007"
    assert fmt_sub("007") == "007"


def test_fmt_ses_int_is_two_digits():
    assert fmt_ses(1) == "01"
    assert fmt_ses(10) == "10"


def test_fmt_ses_string_session_passthrough():
    # localizer sessions are strings and must survive unchanged
    assert fmt_ses("pRF") == "pRF"
    assert fmt_ses("fLOC") == "fLOC"
    assert fmt_ses("ses-fLOC") == "fLOC"


def test_fmt_run():
    assert fmt_run(1) == "01"
    assert fmt_run("all") == "all"
    assert fmt_run("run-02") == "02"


def test_fmt_video():
    assert fmt_video(1) == "0001"
    assert fmt_video(1234) == "1234"
