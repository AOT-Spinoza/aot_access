"""Tests for AOTSubject — the per-subject access object."""

import numpy as np
import pytest

from AOTaccess.subject import AOTSubject


# ----- pure-unit (no cluster data needed) ----------------------------------


class _StubRoi:
    """Stand-in for ROIAccess.rois used by _resolve_roi_query 'all' branch."""
    def rois(self, subject=None):
        return ["A", "B", "C"]


def test_resolve_roi_query_single_name():
    s = AOTSubject.__new__(AOTSubject)
    s.roi = _StubRoi()
    s.sub = 1
    assert s._resolve_roi_query("V1v") == ["V1v"]


def test_resolve_roi_query_all():
    s = AOTSubject.__new__(AOTSubject)
    s.roi = _StubRoi()
    s.sub = 1
    assert s._resolve_roi_query("all") == ["A", "B", "C"]


def test_resolve_roi_query_list_dedupes_and_preserves_order():
    s = AOTSubject.__new__(AOTSubject)
    s.roi = _StubRoi()
    s.sub = 1
    assert s._resolve_roi_query(["X", "all", "X"]) == ["X", "A", "B", "C"]


def test_resolve_roi_query_rejects_bad_type():
    s = AOTSubject.__new__(AOTSubject)
    s.roi = _StubRoi()
    s.sub = 1
    with pytest.raises(TypeError):
        s._resolve_roi_query(123)


# ----- cluster integration tests --------------------------------------------


@pytest.fixture
def sub1(aot_config):
    return AOTSubject(1, config=aot_config)


@pytest.mark.cluster
def test_discovery_methods(sub1):
    assert sub1.sessions() == list(range(1, 11))
    assert sub1.runs(1) == list(range(1, 11))
    assert len(sub1.videos()) > 0


@pytest.mark.cluster
def test_brain_mask_caches_and_counts(sub1):
    m1 = sub1.get_brain_mask()
    assert m1 is sub1.get_brain_mask()           # cached identity
    assert m1.shape == (69, 81, 86)
    assert sub1.get_n_voxels() == int(m1.sum()) > 0


@pytest.mark.cluster
def test_get_betas_trial_voxel_shape(sub1):
    # per-session ses-01 has 720 trials; V1v has ~572 voxels — both intersect brain
    betas = sub1.get_betas(ses=1, roi="V1v")
    assert betas.ndim == 2
    assert betas.shape[0] == 720
    assert betas.shape[1] > 0


@pytest.mark.cluster
def test_get_video_betas_two_repetitions(sub1):
    bv = sub1.get_video_betas(1, direction="fw", roi="V1v")
    assert bv.shape[0] == 2                       # two timepoints
    bv_avg = sub1.get_video_betas(1, direction="fw", roi="V1v", average_repeats=True)
    assert bv_avg.ndim == 1
    np.testing.assert_allclose(bv.mean(axis=0), bv_avg)


@pytest.mark.cluster
def test_trial_table_structure(sub1):
    t = sub1.trial_table()
    assert len(t) == 8_400                        # 10 ses * 10 run * 84 events
    assert int(t.is_blank.sum()) == 1_200         # 12 blanks/run * 100
    # every (video, direction) appears exactly twice across the subject, with rep ∈ {0, 1}
    stim = t[~t.is_blank]
    grouped = stim.groupby(["video", "direction"]).rep.agg(["min", "max", "count"])
    assert grouped["min"].eq(0).all()
    assert grouped["max"].eq(1).all()
    assert grouped["count"].eq(2).all()


@pytest.mark.cluster
def test_get_run_betas_shape(sub1):
    run = sub1.get_run_betas(ses=1, run=1, roi="V1v")
    assert run.shape[0] == 72                     # 72 stim trials per run
    assert run.shape[1] > 0


@pytest.mark.cluster
def test_to_nifti_roundtrip_in_roi(sub1):
    mask = sub1.get_roi_mask("V1v")
    n = int(mask.sum())
    vals = np.arange(n, dtype=float)
    img = sub1.to_nifti(vals, roi="V1v")
    arr = img.get_fdata()
    np.testing.assert_array_equal(arr[mask], vals)


@pytest.mark.cluster
def test_voxel_coords_match_brain_count(sub1):
    coords = sub1.get_voxel_coordinates()
    assert coords.shape == (sub1.get_n_voxels(), 3)
