"""Tests for the cross-video annotations manifest + per-video readers."""

import warnings

import h5py
import numpy as np
import pytest

from AOTaccess.stimulus_info_access import StimuliInfoAccess
from AOTaccess.errors import DataNotFoundError


@pytest.fixture
def stim(aot_config):
    return StimuliInfoAccess(config=aot_config)


@pytest.mark.cluster
def test_online_behavior_table_full(stim):
    df = stim.read_online_behavior_table()
    # Schema documented by the dataset authors
    expected_cols = {
        "name", "source_id", "direction", "stimulus_id", "n_views",
        "identifiability_score", "identifiability_score_ci_lo",
        "identifiability_score_ci_hi",
        "direction_accuracy_raw", "direction_accuracy_weighted",
        "mean_confidence", "mean_direction_rt_ms",
        "identifiability_decile", "yaml_path",
    }
    assert set(df.columns) == expected_cols
    # ~2179 unique stimuli × 2 directions = ~4358 rows
    assert len(df) > 4000
    assert df.direction.isin({"forward", "backward"}).all()


@pytest.mark.cluster
def test_online_behavior_table_filtered(stim):
    rows = stim.read_online_behavior_table(video=1)
    # one row per direction for this video
    assert len(rows) == 2
    assert set(rows.direction) == {"forward", "backward"}

    fw = stim.read_online_behavior_table(video=1, direction="fw")
    assert len(fw) == 1
    assert fw.iloc[0]["name"] == "0001_fw"


@pytest.mark.cluster
def test_video_behavior_yaml(stim):
    detail = stim.read_video_behavior(1, "fw")
    assert detail["video"]["name"] == "0001_fw"
    assert "summary" in detail
    assert "responses" in detail and len(detail["responses"]) > 0
    # one row of responses has the expected per-subject fields
    r0 = detail["responses"][0]
    for key in (
        "subject", "response_direction", "correct", "confidence",
        "direction_rt_ms", "subject_quality_weight", "subject_included",
    ):
        assert key in r0


@pytest.mark.cluster
def test_qwen_description_metadata(stim):
    meta = stim.read_qwen_description_meta()
    assert meta["annotation_type"] == "qwen_description"
    assert "model" in meta
    assert meta["generation"]["language"] == "English"


@pytest.mark.cluster
def test_qwen_embedding_metadata(stim):
    meta = stim.read_qwen_embedding_meta()
    assert meta["annotation_type"] == "qwen_embedding"
    assert meta["generation"]["embedding_dimensions"] == 2048


@pytest.mark.cluster
def test_moten_filter_info_16_and_32(stim):
    info16 = stim.read_moten_filter_info(16)
    info32 = stim.read_moten_filter_info(32)
    # The advertised filter count matches the channel axis of the .npy.
    # YAML internal consistency.
    assert info16["meta"]["n_filters"] == len(info16["filters"])
    assert info32["meta"]["n_filters"] == len(info32["filters"])
    assert info32["meta"]["n_filters"] > info16["meta"]["n_filters"]
    # The motion-energy NPY's channel count may be smaller than the
    # filter-bank size (e.g. DC filters dropped) — just confirm the file
    # itself is loadable and 2-D (timepoints, channels).
    feats = stim.read_motion_energy_features(1, direction="fw", highest_freq=16)
    assert feats.ndim == 2 and feats.shape[1] > 0


def test_moten_filter_info_rejects_bad_freq(synthetic_localizers):
    # Pure-unit: validation runs before any disk access.
    stim = StimuliInfoAccess()
    with pytest.raises(ValueError):
        stim.read_moten_filter_info(8)


@pytest.mark.cluster
def test_available_annotations(stim):
    kinds = stim.available_annotations(1, "fw")
    # behavior is the newly added one; all earlier kinds remain
    expected = {
        "action_classification", "action_detection", "behavior", "captioning",
        "depth_estimation", "instance_segmentation", "keypoints", "motion_energy",
        "object_detection", "qwen_description", "qwen_embedding",
        "sbert_embeddings", "semantic_segmentation",
    }
    assert expected.issubset(set(kinds))


@pytest.mark.cluster
def test_missing_video_behavior_raises(stim):
    with pytest.raises(DataNotFoundError):
        stim.read_video_behavior(99999, "fw")


# ---------------------------------------------------------------------------
# motion-energy: HDF5-first, .npy fallback, per-video summary
# ---------------------------------------------------------------------------


@pytest.mark.cluster
def test_motion_energy_features_prefers_h5(stim):
    """If the .h5 exists, it's used and we get exactly its /motion_energy."""
    h5_path = stim._motion_energy_h5_path(1, "fw", 16)
    if not h5_path.exists():
        pytest.skip(f"HDF5 not yet on disk for this video: {h5_path}")
    with h5py.File(h5_path, "r") as f:
        expected = f["motion_energy"][...]
    feats = stim.read_motion_energy_features(1, direction="fw", highest_freq=16)
    assert feats.shape == expected.shape
    assert feats.dtype == expected.dtype
    np.testing.assert_array_equal(feats, expected)
    # And channel-axis matches the filter-bank advert.
    info = stim.read_moten_filter_info(16)
    assert feats.shape[1] == info["meta"]["n_filters"]


@pytest.mark.cluster
def test_motion_energy_features_falls_back_to_npy(stim):
    """When only the legacy .npy exists, we read it and warn loudly."""
    h5_path = stim._motion_energy_h5_path(1, "fw", 32)
    npy_path = stim._motion_energy_npy_path(1, "fw", 32)
    if h5_path.exists() or not npy_path.exists():
        pytest.skip("32-Hz conversion state has moved on; this test is "
                    "specific to the .h5-missing / .npy-present window.")
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        feats = stim.read_motion_energy_features(1, direction="fw", highest_freq=32)
    assert feats.ndim == 2 and feats.shape[1] > 0
    assert any(
        issubclass(w.category, DeprecationWarning) and "legacy .npy" in str(w.message)
        for w in caught
    ), "expected a DeprecationWarning naming the legacy .npy fallback"


@pytest.mark.cluster
def test_motion_energy_features_missing_raises(stim):
    """Neither the HDF5 nor the legacy NPY → DataNotFoundError naming both."""
    with pytest.raises(DataNotFoundError) as ei:
        stim.read_motion_energy_features(99999, direction="fw", highest_freq=16)
    msg = str(ei.value)
    assert "99999" in msg
    assert ".h5" in msg and ".npy" in msg


@pytest.mark.cluster
def test_motion_energy_summary_shape_when_present(stim):
    """If /motion_energy_summary is written, it's (n_filters,) and matches the
    temporal mean of /motion_energy (Nishimoto / Gallant-lab pooling)."""
    h5_path = stim._motion_energy_h5_path(1, "fw", 16)
    if not h5_path.exists():
        pytest.skip("HDF5 not yet on disk for this video")
    with h5py.File(h5_path, "r") as f:
        if "motion_energy_summary" not in f:
            pytest.skip(
                "/motion_energy_summary not yet written — HDF5 conversion is "
                "in progress; the reader is exercised by the missing-dataset "
                "test below."
            )
        per_frame = f["motion_energy"][...]
    summary = stim.read_motion_energy_summary(1, direction="fw", highest_freq=16)
    info = stim.read_moten_filter_info(16)
    assert summary.shape == (info["meta"]["n_filters"],)
    # The summary IS the temporal mean of the per-frame array.
    np.testing.assert_allclose(summary, per_frame.mean(axis=0), atol=1e-5)


@pytest.mark.cluster
def test_motion_energy_summary_raises_when_dataset_missing(stim):
    """During the conversion window, the summary read raises DataNotFoundError
    that names the missing dataset, not just a generic missing file."""
    h5_path = stim._motion_energy_h5_path(1, "fw", 16)
    if not h5_path.exists():
        pytest.skip("HDF5 not yet on disk for this video")
    with h5py.File(h5_path, "r") as f:
        if "motion_energy_summary" in f:
            pytest.skip("summary dataset is already written for this video")
    with pytest.raises(DataNotFoundError) as ei:
        stim.read_motion_energy_summary(1, direction="fw", highest_freq=16)
    assert "motion_energy_summary" in str(ei.value)


@pytest.mark.cluster
def test_motion_energy_summary_missing_file_raises(stim):
    """When the HDF5 file itself is absent (e.g. 32 Hz mid-conversion or a
    bogus video id), the summary reader raises pointing at the missing file."""
    with pytest.raises(DataNotFoundError) as ei:
        stim.read_motion_energy_summary(99999, direction="fw", highest_freq=16)
    assert "99999" in str(ei.value)
    assert ".h5" in str(ei.value)


def test_motion_energy_path_helpers_pure_unit():
    """Path-building is pure: no cluster needed."""
    stim = StimuliInfoAccess()
    h5p = stim._motion_energy_h5_path(7, "rv", 32)
    npyp = stim._motion_energy_npy_path(7, "rv", 32)
    assert h5p.name == "0007_rv.h5"
    assert npyp.name == "0007_rv.npy"
    assert h5p.parent.name == "32hz"
    assert npyp.parent.name == "32hz"
    assert h5p.parent.parent.name == "motion_energy"
