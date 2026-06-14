"""Tests for brain-mask conventions and the volume <-> flat-voxel round-trip."""

import numpy as np
import nibabel as nib
import pytest

from AOTaccess.brain import (
    compute_brain_mask,
    compute_ncsnr_brain_mask,
    get_voxel_coordinates,
    to_nifti,
)
from AOTaccess.errors import DataNotFoundError


def test_to_nifti_roundtrip(tmp_path):
    mask = np.zeros((4, 4, 4), dtype=bool)
    mask[0, 0, 0] = True
    mask[1, 2, 3] = True
    mask[3, 3, 3] = True
    values = np.array([10.0, 20.0, 30.0])
    out_path = tmp_path / "out.nii.gz"
    img = to_nifti(values, mask, np.eye(4), output_path=out_path)
    assert img.shape == (4, 4, 4)
    arr = img.get_fdata()
    # values land at the mask True positions, zeros elsewhere
    assert arr[0, 0, 0] == 10
    assert arr[1, 2, 3] == 20
    assert arr[3, 3, 3] == 30
    assert arr.sum() == 60
    # round-trip on disk
    reloaded = nib.load(str(out_path)).get_fdata()
    assert reloaded[mask].tolist() == values.tolist()


def test_to_nifti_rejects_shape_mismatch():
    mask = np.zeros((4, 4, 4), dtype=bool)
    mask[0, 0, 0] = True
    with pytest.raises(ValueError):
        to_nifti(np.zeros(5), mask, np.eye(4))


def test_get_voxel_coordinates_with_identity_affine():
    mask = np.zeros((3, 3, 3), dtype=bool)
    mask[0, 0, 0] = True
    mask[2, 1, 0] = True
    coords = get_voxel_coordinates(mask, np.eye(4))
    # identity affine -> world coords == voxel indices (argwhere order)
    assert coords.shape == (2, 3)
    assert coords[0].tolist() == [0.0, 0.0, 0.0]
    assert coords[1].tolist() == [2.0, 1.0, 0.0]


@pytest.mark.cluster
def test_compute_brain_mask_real(aot_config):
    mask = compute_brain_mask(1, ses=1, resolution="2p0mm", config=aot_config)
    assert mask.dtype == bool
    assert mask.shape == (69, 81, 86)
    # the EPI grid has ~480k voxels; a real brain mask is in the 100k+ range
    n = int(mask.sum())
    assert 80_000 < n < 350_000


@pytest.mark.cluster
def test_compute_ncsnr_brain_mask_default_sessions(aot_config):
    """Session-averaged NCSNR mask uses every main-task session by default."""
    mask = compute_ncsnr_brain_mask(1, resolution="2p0mm", config=aot_config)
    assert mask.dtype == bool
    assert mask.shape == (69, 81, 86)
    n = int(mask.sum())
    # Averaging across 10 sessions × 2 dirs gives a stable signal mask;
    # ~200 k voxels at 2 mm for a full subject.
    assert 100_000 < n < 350_000


@pytest.mark.cluster
def test_compute_ncsnr_brain_mask_threshold_monotone(aot_config):
    """Raising the threshold can only shrink the mask."""
    m0 = compute_ncsnr_brain_mask(1, threshold=0.0, config=aot_config)
    m_hi = compute_ncsnr_brain_mask(1, threshold=0.05, config=aot_config)
    assert m_hi.sum() < m0.sum()
    # m_hi ⊆ m0
    assert (m_hi & ~m0).sum() == 0


@pytest.mark.cluster
def test_compute_ncsnr_brain_mask_subset_of_sessions(aot_config):
    """Averaging over fewer sessions still yields a sane mask."""
    one = compute_ncsnr_brain_mask(1, sessions=[1], config=aot_config)
    two = compute_ncsnr_brain_mask(1, sessions=[1, 2], config=aot_config)
    assert one.dtype == bool and two.dtype == bool
    # Single-session NC mask is noisier — usually slightly larger than
    # the two-session average (more above-zero voxels by chance), but
    # both within the same order of magnitude.
    assert 50_000 < int(one.sum()) < 350_000
    assert 50_000 < int(two.sum()) < 350_000


@pytest.mark.cluster
def test_compute_ncsnr_brain_mask_missing_subject(aot_config):
    """A bogus subject has no NC files → DataNotFoundError."""
    with pytest.raises(DataNotFoundError):
        compute_ncsnr_brain_mask(999, config=aot_config)
