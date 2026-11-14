"""Tests for PreprocedAccess — func_path and read_func against a synthetic store."""

import numpy as np
import nibabel as nib
import pytest

from AOTaccess.errors import DataNotFoundError
from AOTaccess.preproced_access import PreprocedAccess


@pytest.fixture
def synthetic_preproced(tmp_path):
    func = (
        tmp_path / "derivatives" / "aot_prep" / "sub-001" / "ses-01" / "func"
        / "sub-001_ses-01_task-AOT_rec-nordicstc_run-01_part-mag_bold_space-T1w_res-2p0mm.nii.gz"
    )
    func.parent.mkdir(parents=True)
    nib.save(nib.Nifti1Image(np.zeros((3, 3, 3, 2)), np.eye(4)), str(func))
    return tmp_path


def test_func_path_uses_aot_naming(synthetic_preproced):
    prep = PreprocedAccess(root_dir=synthetic_preproced)
    path = prep.func_path(1, 1, 1)
    assert path.name == (
        "sub-001_ses-01_task-AOT_rec-nordicstc_run-01_part-mag_bold_space-T1w_res-2p0mm.nii.gz"
    )
    assert path.exists()


def test_func_path_resolution_and_task(synthetic_preproced):
    prep = PreprocedAccess(root_dir=synthetic_preproced)
    path = prep.func_path(1, "ses-01", 1, task="pRF", resolution="1p25mm")
    assert path.name == (
        "sub-001_ses-01_task-pRF_rec-nordicstc_run-01_part-mag_bold_space-T1w_res-1p25mm.nii.gz"
    )
    assert not path.exists()


def test_read_func_returns_image(synthetic_preproced):
    prep = PreprocedAccess(root_dir=synthetic_preproced)
    img = prep.read_func(1, 1, 1)
    assert img.shape == (3, 3, 3, 2)


def test_read_func_missing_raises_data_not_found(synthetic_preproced):
    prep = PreprocedAccess(root_dir=synthetic_preproced)
    with pytest.raises(DataNotFoundError):
        prep.read_func(1, 2, 1)
