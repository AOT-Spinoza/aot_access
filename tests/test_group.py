"""Tests for AOTGroup — the cross-subject cohort wrapper."""

import pytest

from AOTaccess.group import AOTGroup
from AOTaccess.subject import AOTSubject


@pytest.mark.cluster
def test_group_construction_from_ids(aot_config):
    g = AOTGroup([1, 2], config=aot_config)
    assert len(g) == 2
    assert set(g.keys()) == {1, 2}
    for s in g:
        assert isinstance(s, AOTSubject)


@pytest.mark.cluster
def test_group_shared_videos(aot_config):
    g = AOTGroup([1, 2], config=aot_config)
    shared = g.shared_videos(direction="fw")
    assert len(shared) > 0
    # Subset of each subject's individual video list.
    for s in g:
        assert set(shared).issubset(set(s.videos(direction="fw")))


@pytest.mark.cluster
def test_group_shared_sessions(aot_config):
    g = AOTGroup([1, 2], config=aot_config)
    assert g.shared_sessions() == list(range(1, 11))


@pytest.mark.cluster
def test_group_broadcast_get_video_betas(aot_config):
    g = AOTGroup([1, 2], config=aot_config)
    # Pick a video both subjects saw (different subjects see different
    # subsets — that's exactly what `shared_videos` is for).
    shared = g.shared_videos(direction="fw")
    out = g.get_video_betas(shared[0], direction="fw", roi="V1v",
                            average_repeats=True)
    assert set(out.keys()) == {1, 2}
    for sub, beta in out.items():
        assert beta.ndim == 1
        assert beta.size > 0


@pytest.mark.cluster
def test_group_indexing_returns_subject(aot_config):
    g = AOTGroup([1, 2], config=aot_config)
    s1 = g[1]
    assert isinstance(s1, AOTSubject)
    assert s1.sub == 1
    assert 1 in g and 2 in g and 3 not in g


@pytest.mark.cluster
def test_group_passes_subject_kwargs(aot_config):
    g = AOTGroup([1, 2], config=aot_config, resolution="1p25mm")
    for s in g:
        assert s.resolution == "1p25mm"
