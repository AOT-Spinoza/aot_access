"""Tests for GLMSingleAccess — filename building (incl. string sessions) and reads."""

import pytest

from AOTaccess.glmsingle_access import (
    GLMSingleAccess,
    build_per_session_bids_nii,
    build_per_video_bids_nii,
)
from AOTaccess.errors import DataNotFoundError


def test_per_session_filename_int_session():
    fn = build_per_session_bids_nii(1, 2, "2p0mm", "TYPED_FITHRF_GLMDENOISE_RR", "R2")
    assert fn == "sub-001_ses-02_space-T1w_res-2p0mm_model-TYPED_desc-R2.nii.gz"


def test_per_session_filename_string_session():
    # localizer sessions are strings — must not crash on `{ses:02d}`
    fn = build_per_session_bids_nii(
        1, "fLOC", "2p0mm", "TYPED_FITHRF_GLMDENOISE_RR", "R2"
    )
    assert fn == "sub-001_ses-fLOC_space-T1w_res-2p0mm_model-TYPED_desc-R2.nii.gz"


def test_per_video_filename():
    fn = build_per_video_bids_nii(
        3, "2p0mm", "TYPED_FITHRF_GLMDENOISE_RR", 7, zscore=True
    )
    assert fn == "sub-003_space-T1w_res-2p0mm_model-TYPED_desc-0007betaszscore.nii.gz"


def test_nii_dir_path_accepts_string_session():
    g = GLMSingleAccess(root_dir="/ds")
    path = g.get_nii_dir_path(1, "fLOC", resolution="2p0mm")
    assert "sub-001" in str(path)
    assert "ses-fLOC" in str(path)
    assert path.name == "space-T1w_res-2p0mm"


@pytest.mark.cluster
def test_read_betas_real(aot_config):
    g = GLMSingleAccess(config=aot_config)
    betas = g.read_betas(1, 1, resolution="2p0mm")
    assert betas.ndim == 4


@pytest.mark.cluster
def test_read_betas_missing_raises_data_not_found(aot_config):
    g = GLMSingleAccess(config=aot_config)
    with pytest.raises(DataNotFoundError):
        g.read_betas(99, 1, resolution="2p0mm")


@pytest.mark.cluster
def test_list_and_read_session_map(aot_config):
    """Generic per-session desc reader covers the unmapped GLMsingle outputs."""
    g = GLMSingleAccess(config=aot_config)
    descs = g.list_session_descs(1, 1, resolution="2p0mm")
    # The TYPED model writes ~12 maps per session.
    assert {"R2", "meanvol", "betasmd", "HRFindex", "FRACvalue"}.issubset(set(descs))
    # And one of them can be loaded via the generic method.
    arr = g.read_session_map(1, 1, "HRFindex", resolution="2p0mm")
    assert arr.shape == (69, 81, 86)


@pytest.mark.cluster
def test_read_session_map_missing_raises(aot_config):
    g = GLMSingleAccess(config=aot_config)
    with pytest.raises(DataNotFoundError):
        g.read_session_map(1, 1, "no_such_desc_tag", resolution="2p0mm")
