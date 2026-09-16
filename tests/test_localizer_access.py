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
    assert la.read_map("prf", 6, "noiseceiling").ndim == 3
    # Fit maps exist only once the pipeline repopulates a fits/ dir (during
    # the Aug-2026 migration all fits live in fits_old* renames).
    for sub in (3, 4, 5, 6, 7, 8):
        if la.map_path("prf", sub, "ecc").exists():
            assert la.read_map("prf", sub, "ecc").ndim == 3
            break
    else:
        pytest.skip("no populated fits/ in the pRF store yet (mid-migration)")


@pytest.mark.cluster
def test_prf_median_timeseries(aot_config):
    """The pRF median/medianpsc summary timeseries read."""
    la = LocalizerAccess(config=aot_config)
    median = la.read_map("prf", 6, "median")              # 4-D timeseries
    medianpsc = la.read_map("prf", 6, "medianpsc")        # 4-D timeseries
    assert median.ndim == 4 and median.shape[:3] == (65, 75, 86)
    assert medianpsc.ndim == 4 and medianpsc.shape[:3] == (65, 75, 86)


@pytest.mark.cluster
def test_prf_noisepool_mask(aot_config):
    """The GLMsingle noise-pool mask reads where the pipeline wrote one.

    Unlike the summary timeseries, noisepool is not produced for every
    (subject, resolution) — the pRF pipeline emits it sparsely and has
    moved it between runs, so find one rather than pinning a subject.
    """
    la = LocalizerAccess(config=aot_config)
    for sub, res in [(3, "1p25mm"), (3, "2p0mm"), (7, "2p0mm"), (6, "2p0mm")]:
        if la.map_path("prf", sub, "noisepool", resolution=res).exists():
            noisepool = la.read_map("prf", sub, "noisepool", resolution=res)
            assert noisepool.ndim == 3
            assert noisepool.shape == la.read_map(
                "prf", sub, "median", resolution=res
            ).shape[:3]
            return
    pytest.skip("no noisepool mask in the pRF store at a canonical resolution")
