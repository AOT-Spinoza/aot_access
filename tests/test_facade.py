"""Tests for the AOTAccess facade."""

import pytest

from AOTaccess.aot_access import AOTAccess


def test_facade_instantiates_without_arguments():
    a = AOTAccess()
    for name in (
        "glmsingle_access",
        "roi_access",
        "bids_access",
        "preproced_access",
        "expdesign_access",
    ):
        assert hasattr(a, name)


def test_facade_shares_one_config_across_accessors():
    a = AOTAccess()
    assert a.glmsingle_access.config is a.config
    assert a.roi_access.config is a.config


@pytest.mark.cluster
def test_extract_betas_in_roi(aot_config):
    a = AOTAccess(config=aot_config)
    betas = a.extract_betas_in_roi(1, 1, "V1v")
    assert betas.ndim == 2
    assert betas.shape[0] > 0


@pytest.mark.cluster
def test_read_roi_mask_on_epi_grid(aot_config):
    a = AOTAccess(config=aot_config)
    mask = a.read_roi_mask(1, "V1v")
    assert mask.shape == (69, 81, 86)
