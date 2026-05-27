"""Tests for LocalizerAccess — manifest discovery, resolution and reads."""

import pytest

from AOTaccess.localizer_access import LocalizerAccess
from AOTaccess.errors import DataNotFoundError


def test_discovery_from_synthetic_manifest(synthetic_localizers):
    la = LocalizerAccess(root_dir=synthetic_localizers)
    assert la.localizers() == ["demo"]
    assert la.kind("demo") == "parametric"
    assert la.subjects("demo") == ["sub-001"]
    assert "alpha" in la.maps("demo")
    assert la.maps("demo", model="m1") == ["alpha", "beta"]


def test_read_map_uses_manifest_defaults(synthetic_localizers):
    la = LocalizerAccess(root_dir=synthetic_localizers)
    arr = la.read_map("demo", 1, "alpha")
    assert arr.shape == (3, 3, 3)


def test_map_path_for_model_independent_map(synthetic_localizers):
    la = LocalizerAccess(root_dir=synthetic_localizers)
    path = la.map_path("demo", "sub-001", "beta")
    assert path.name == "sub-001_model-m1_res-2p0mm_beta.nii.gz"


def test_unknown_map_raises(synthetic_localizers):
    la = LocalizerAccess(root_dir=synthetic_localizers)
    with pytest.raises(ValueError):
        la.read_map("demo", 1, "nope")


def test_missing_manifest_raises_data_not_found(synthetic_localizers):
    la = LocalizerAccess(root_dir=synthetic_localizers)
    with pytest.raises(DataNotFoundError):
        la.manifest("ghost")


def test_missing_file_raises_data_not_found(synthetic_localizers):
    la = LocalizerAccess(root_dir=synthetic_localizers)
    with pytest.raises(DataNotFoundError):
        la.read_map("demo", 2, "alpha")  # sub-002 has no file


def test_localizers_empty_when_store_absent(tmp_path):
    la = LocalizerAccess(root_dir=tmp_path)
    assert la.localizers() == []


@pytest.mark.cluster
def test_real_prf_localizer(aot_config):
    la = LocalizerAccess(config=aot_config)
    assert "prf" in la.localizers()
    assert la.kind("prf") == "parametric"
    assert la.read_map("prf", 1, "ecc").shape == (69, 81, 86)
    assert la.read_map("prf", 1, "noiseceiling").ndim == 3


@pytest.mark.cluster
def test_prf_prep_maps(aot_config):
    """The pRF prep maps (median/medianpsc timeseries + noisepool) read."""
    la = LocalizerAccess(config=aot_config)
    median = la.read_map("prf", 1, "median")              # 4-D timeseries
    medianpsc = la.read_map("prf", 1, "medianpsc")        # 4-D timeseries
    noisepool = la.read_map("prf", 1, "noisepool")        # 3-D mask
    assert median.ndim == 4 and median.shape[:3] == (69, 81, 86)
    assert medianpsc.ndim == 4 and medianpsc.shape[:3] == (69, 81, 86)
    assert noisepool.ndim == 3 and noisepool.shape == (69, 81, 86)
