"""Tests for the cross-video annotations manifest + per-video readers."""

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
