"""Tests for ROIAccess — manifest discovery, path resolution and reads."""

import pytest

from AOTaccess.roi_access import ROIAccess
from AOTaccess.errors import DataNotFoundError


def test_discovery_from_synthetic_manifest(synthetic_roi):
    r = ROIAccess(root_dir=synthetic_roi)
    assert r.atlases() == ["demo"]
    assert r.rois() == ["AAA"]
    assert r.rois(subject="sub-001") == ["AAA"]
    assert "balanced" in r.conservativeness_levels()


def test_read_mask_synthetic(synthetic_roi):
    r = ROIAccess(root_dir=synthetic_roi)
    mask = r.read_mask(
        1, "AAA", atlas="demo", space="MNI", res="1p25mm", cons="balanced"
    )
    assert mask.dtype == bool
    assert mask.sum() > 0


def test_missing_mask_raises_data_not_found(synthetic_roi):
    r = ROIAccess(root_dir=synthetic_roi)
    with pytest.raises(DataNotFoundError):
        r.read_mask(1, "AAA", atlas="demo", space="MNI", res="9mm", cons="balanced")


def test_resolve_validates_template_parameters(synthetic_roi):
    r = ROIAccess(root_dir=synthetic_roi)
    with pytest.raises(ValueError):
        # missing roi / res / cons
        r.resolve("mni_volume_mask_bilateral", sub=1, atlas="demo")


def test_unknown_template_raises(synthetic_roi):
    r = ROIAccess(root_dir=synthetic_roi)
    with pytest.raises(KeyError):
        r.resolve("not_a_template", sub=1)


@pytest.mark.cluster
def test_real_manifest_lists_known_atlases(aot_config):
    r = ROIAccess(config=aot_config)
    assert "wang_2015" in r.atlases()
    assert "V1v" in r.rois()


@pytest.mark.cluster
def test_real_mask_on_epi_grid(aot_config):
    r = ROIAccess(config=aot_config)
    mask = r.read_mask(
        1, "V1v", atlas="wang_2015", space="T1w", res="2p0mm", cons="balanced"
    )
    assert mask.shape == (69, 81, 86)
    assert mask.sum() > 0


@pytest.mark.cluster
def test_read_group_majority(aot_config):
    r = ROIAccess(config=aot_config)
    m = r.read_group_majority("V1v", hemi="L", atlas="wang_2015")
    assert m.dtype == bool
    assert m.sum() > 0


@pytest.mark.cluster
def test_read_group_fsaverage_probseg(aot_config):
    r = ROIAccess(config=aot_config)
    p = r.read_group_fsaverage_probseg("V1v", hemi="L", atlas="wang_2015")
    # gifti agg_data returns a 1-D ndarray of per-vertex floats
    assert p.ndim == 1 and p.size > 0


@pytest.mark.cluster
def test_group_fsaverage_mpm_path(aot_config):
    r = ROIAccess(config=aot_config)
    p = r.group_fsaverage_mpm_path(hemi="L", atlas="wang_2015")
    assert p.exists()
    assert p.suffix == ".annot"


@pytest.mark.cluster
def test_cifti_dlabel(aot_config):
    r = ROIAccess(config=aot_config)
    p32 = r.cifti_dlabel_path(atlas="wang_2015", den="32k")
    p170 = r.cifti_dlabel_path(atlas="wang_2015", den="170k")
    assert p32.exists() and p170.exists()
    img = r.read_cifti_dlabel(atlas="wang_2015", den="32k")
    assert img.shape[0] >= 1


def test_cifti_dlabel_rejects_bad_density(aot_config):
    pytest.importorskip("nibabel")
    r = ROIAccess(config=aot_config)
    with pytest.raises(ValueError):
        r.cifti_dlabel_path(atlas="wang_2015", den="64k")
