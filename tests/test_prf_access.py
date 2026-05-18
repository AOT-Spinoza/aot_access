"""Tests for PrfAccess — the pRF-specific convenience wrapper over LocalizerAccess."""

import pytest

from AOTaccess.prf_access import PrfAccess


@pytest.mark.cluster
def test_params_are_model_specific(aot_config):
    p = PrfAccess(config=aot_config)
    assert "ecc" in p.params()
    assert "surr_size" in p.params("norm")
    assert "surr_size" not in p.params("gauss")


@pytest.mark.cluster
def test_read_param(aot_config):
    p = PrfAccess(config=aot_config)
    assert p.read_param(1, "ecc").shape == (69, 81, 86)


@pytest.mark.cluster
def test_read_param_masked_zeros_low_r2(aot_config):
    p = PrfAccess(config=aot_config)
    full = p.read_param(1, "ecc")
    masked = p.read_param(1, "ecc", mask=True)
    assert (masked != 0).sum() <= (full != 0).sum()


@pytest.mark.cluster
def test_read_noiseceiling(aot_config):
    p = PrfAccess(config=aot_config)
    assert p.read_noiseceiling(1).ndim == 3
