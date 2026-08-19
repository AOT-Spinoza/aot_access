"""Tests for AnatomyAccess — FreeSurfer cortex gray-matter masks."""

import numpy as np
import nibabel as nib
import pytest

from AOTaccess.anatomy_access import AnatomyAccess
from AOTaccess.errors import DataNotFoundError


def test_gray_matter_mask_rejects_unknown_variant():
    """Pure unit — variant validation runs before disk."""
    a = AnatomyAccess()
    with pytest.raises(ValueError):
        a.gray_matter_mask_path(1, resolution="2p0mm", variant="nope")


@pytest.mark.cluster
def test_t1w_path_resolves(aot_config):
    a = AnatomyAccess(config=aot_config)
    path = a.t1w_path(1, resolution="2p0mm")
    assert path.exists()
    assert path.name == (
        "sub-001_ses-3Tanat_T1w_FS_T2BM_crop_resampled.nii.gz"
    )


@pytest.mark.cluster
def test_t1w_matches_functional_grid(aot_config):
    """The T1 underlay and GLMsingle maps require no resampling."""
    from AOTaccess.glmsingle_access import GLMSingleAccess

    a = AnatomyAccess(config=aot_config)
    glm = GLMSingleAccess(config=aot_config)
    t1w = a.read_t1w(1, resolution="2p0mm")
    nc_path = glm.get_noiseceiling_path(
        1, 1, resolution="2p0mm", direction="fw"
    )
    nc = nib.load(nc_path)

    assert t1w.shape == nc.shape
    np.testing.assert_allclose(t1w.affine, nc.affine, atol=1e-5)


@pytest.mark.cluster
def test_gray_matter_mask_path_resolves(aot_config):
    a = AnatomyAccess(config=aot_config)
    p = a.gray_matter_mask_path(1, resolution="2p0mm", variant="cortex")
    assert p.exists()
    assert p.name == "sub-001_FScortexGM_T2BM_crop_resampled.nii.gz"


@pytest.mark.cluster
def test_read_cortex_returns_bool(aot_config):
    """Binary variants → bool, by variant convention."""
    a = AnatomyAccess(config=aot_config)
    cortex = a.read_gray_matter_mask(1, resolution="2p0mm", variant="cortex")
    dil = a.read_gray_matter_mask(1, resolution="2p0mm", variant="cortex_dil")
    assert cortex.shape == (69, 81, 86)
    assert cortex.dtype == bool and dil.dtype == bool
    # Dilation strictly grows the mask.
    assert int(dil.sum()) > int(cortex.sum())


@pytest.mark.cluster
def test_read_cortex_sm_returns_float(aot_config):
    """Soft variant → float in [0, 1] (no automatic binarisation)."""
    a = AnatomyAccess(config=aot_config)
    sm = a.read_gray_matter_mask(1, resolution="2p0mm", variant="cortex_sm")
    assert sm.shape == (69, 81, 86)
    assert sm.dtype != bool
    assert 0.0 <= sm.min() and sm.max() <= 1.0
    # Intermediate values are present — confirms softness.
    assert int((sm > 0).sum()) > int((sm == 1).sum())


@pytest.mark.cluster
def test_missing_subject_raises_data_not_found(aot_config):
    a = AnatomyAccess(config=aot_config)
    with pytest.raises(DataNotFoundError):
        a.read_gray_matter_mask(99, resolution="2p0mm", variant="cortex")
