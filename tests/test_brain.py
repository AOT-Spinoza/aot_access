"""Tests for brain-mask conventions and the volume <-> flat-voxel round-trip."""

import numpy as np
import nibabel as nib
import pytest

from AOTaccess.brain import compute_brain_mask, get_voxel_coordinates, to_nifti


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
