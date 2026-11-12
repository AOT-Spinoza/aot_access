"""Unit tests for the motion-energy bank registry (no cluster data needed)."""
import warnings

import pytest

from AOTaccess.errors import DataNotFoundError
from AOTaccess.stimulus_info_access import StimuliInfoAccess


@pytest.fixture(scope="module")
def stim():
    return StimuliInfoAccess()


def test_bank_registry_contents(stim):
    assert set(stim._ME_BANKS) == {"source_32hz", "source_16hz", "display"}
    assert stim._ME_BANK_ALIASES == {"32hz": "source_32hz", "16hz": "source_16hz"}


@pytest.mark.parametrize("bank,expected", [
    ("display", "display"),
    ("source_32hz", "source_32hz"),
    ("source_16hz", "source_16hz"),
])
def test_explicit_bank_resolves_without_warning(stim, bank, expected):
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        assert stim.resolve_motion_energy_bank(bank=bank) == expected


@pytest.mark.parametrize("alias,expected", [
    ("32hz", "source_32hz"),
    ("16hz", "source_16hz"),
])
def test_deprecated_alias_resolves_with_warning(stim, alias, expected):
    with pytest.warns(DeprecationWarning):
        assert stim.resolve_motion_energy_bank(bank=alias) == expected


@pytest.mark.parametrize("freq,expected", [(32, "source_32hz"), (16, "source_16hz")])
def test_legacy_highest_freq_still_works_and_warns(stim, freq, expected):
    with pytest.warns(DeprecationWarning):
        assert stim.resolve_motion_energy_bank(highest_freq=freq) == expected


def test_default_bank_is_display_for_fw(stim):
    """Since 2026-11-11 fw reads default to the physically-correct display bank."""
    with warnings.catch_warnings():
        warnings.simplefilter("error")          # a default read must not warn
        assert stim.resolve_motion_energy_bank() == "display"
        assert stim.resolve_motion_energy_bank(direction="fw") == "display"


def test_default_bank_falls_back_for_rv(stim):
    """rv is not migrated: the default read keeps returning legacy rv data."""
    with pytest.warns(DeprecationWarning):
        assert stim.resolve_motion_energy_bank(direction="rv") == "source_16hz"


def test_default_manifest_is_display(stim):
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        assert stim.resolve_motion_energy_bank(highest_freq=None) == "display"


def test_unknown_bank_rejected(stim):
    with pytest.raises(ValueError):
        stim.resolve_motion_energy_bank(bank="nope")


def test_unknown_freq_rejected(stim):
    with pytest.raises(ValueError):
        stim.resolve_motion_energy_bank(highest_freq=99)


def test_display_bank_has_no_rv_yet(stim):
    """rv is not migrated in this version: must fail loudly, never fall back."""
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        with pytest.raises(DataNotFoundError) as ei:
            stim.read_motion_energy_features(1, direction="rv", bank="display")
    msg = str(ei.value)
    assert "display" in msg and "rv" in msg
    assert "source_16hz" in msg          # tells the caller what to use instead


def test_bank_paths_are_distinct(stim):
    """display and source_32hz must never resolve to the same directory."""
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        display = stim._motion_energy_bank_dir(7, "fw", "display")
        source = stim._motion_energy_bank_dir(7, "fw", "source_32hz")
    assert display.name == "display"
    assert source.name in {"source_32hz", "32hz"}
    assert display != source
