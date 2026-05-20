"""Tests for the filesystem-backed discovery module."""

import pytest

from AOTaccess import discovery


@pytest.mark.cluster
def test_subjects_returns_known_ids(aot_config):
    subs = discovery.subjects(config=aot_config)
    # All seven main-task subjects exist with GLMsingle outputs
    assert subs == [1, 2, 3, 4, 5, 7, 8]


@pytest.mark.cluster
def test_sessions_for_subject(aot_config):
    assert discovery.sessions(1, config=aot_config) == list(range(1, 11))


@pytest.mark.cluster
def test_runs_for_session(aot_config):
    assert discovery.runs(1, 1, config=aot_config) == list(range(1, 11))


@pytest.mark.cluster
def test_videos_for_subject(aot_config):
    vids = discovery.videos(1, direction="fw", config=aot_config)
    assert len(vids) > 0
    # video ids are sorted ints in the 4-digit range
    assert all(isinstance(v, int) and 0 < v < 10_000 for v in vids)
    assert vids == sorted(vids)


@pytest.mark.cluster
def test_atlases_and_localizers(aot_config):
    assert "wang_2015" in discovery.atlases(config=aot_config)
    assert "prf" in discovery.localizers(config=aot_config)


def test_subjects_empty_when_store_absent(tmp_path):
    # No glmsingle/per_session dir under this root -> empty list
    from AOTaccess.config import Config
    assert discovery.subjects(config=Config(root_dir=tmp_path)) == []
