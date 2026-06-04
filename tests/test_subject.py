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


@pytest.mark.cluster
def test_sessions_for_video(sub1):
    """Each AOT video appears exactly twice per subject across all sessions."""
    # Pick a video that is definitely present.
    v = sub1.videos(direction="fw")[0]
    sessions = sub1.sessions_for_video(v, direction="fw")
    assert all(isinstance(s, int) for s in sessions)
    # Two chronological appearances — same or two distinct sessions.
    appearances = sub1.trial_table().query(
        "video == @v and direction == 'fw'"
    )
    assert len(appearances) == 2
    assert set(sessions) == set(appearances.ses.tolist())


@pytest.mark.cluster
def test_read_glmsingle_output_and_listing(sub1):
    """Generic GLMsingle output reader on the subject."""
    descs = sub1.available_glmsingle_outputs(ses=1)
    assert "HRFindex" in descs
    hrf_idx = sub1.read_glmsingle_output(ses=1, desc="HRFindex", roi="V1v")
    # Flat over (brain ∩ V1v) — 1-D.
    assert hrf_idx.ndim == 1
    assert hrf_idx.shape[0] > 0


@pytest.mark.cluster
def test_get_gray_matter_mask_binary_variant(sub1):
    """Binary variants return bool and slot into mask= cleanly."""
    gm = sub1.get_gray_matter_mask()                # cortex, bool
    assert gm.dtype == bool
    assert gm.shape == sub1.get_brain_mask().shape
    # Cortex GM is in the 30k-200k range across subjects/resolutions.
    assert 30_000 < int(gm.sum()) < 200_000
    # Passes as a custom mask on the betas pipeline:
    betas = sub1.get_betas(ses=1, mask=gm)
    expected_vox = int((gm & sub1.get_brain_mask()).sum())
    assert betas.shape == (720, expected_vox)


@pytest.mark.cluster
def test_get_gray_matter_mask_sm_returns_float(sub1):
    """Soft variant returns float — user thresholds before passing as mask."""
    sm = sub1.get_gray_matter_mask(variant="cortex_sm")
    assert sm.dtype != bool
    assert 0.0 <= sm.min() and sm.max() <= 1.0
    # Thresholding yourself is one line and goes through `mask=`.
    betas = sub1.get_betas(ses=1, mask=(sm > 0.5))
    assert betas.shape[0] == 720 and betas.shape[1] > 0


@pytest.mark.cluster
def test_get_gray_matter_mask_variants_cached(sub1):
    """Each variant is cached; identity holds across repeat calls."""
    a = sub1.get_gray_matter_mask(variant="cortex")
    b = sub1.get_gray_matter_mask(variant="cortex")
    assert a is b                                    # cached
    c = sub1.get_gray_matter_mask(variant="cortex_dil")
    assert c is not a
    assert int(c.sum()) > int(a.sum())               # dilated is larger


@pytest.mark.cluster
def test_to_torch_dataset(sub1):
    torch = pytest.importorskip("torch")
    ds = sub1.to_torch_dataset(direction="fw", roi="V1v", videos=[1, 2, 3])
    assert len(ds) == 3                                    # one per video (averaged)
    sample = ds[0]
    assert sample["video"] == 1
    assert sample["direction"] == "fw"
    assert sample["rep"] is None                           # averaged
    assert isinstance(sample["betas"], torch.Tensor)
    assert sample["betas"].dtype == torch.float32
    # Without averaging: two items per video.
    ds_split = sub1.to_torch_dataset(
        direction="fw", roi="V1v", videos=[1, 2], average_repeats=False,
    )
    assert len(ds_split) == 4
    assert ds_split[0]["rep"] == 0 and ds_split[1]["rep"] == 1
