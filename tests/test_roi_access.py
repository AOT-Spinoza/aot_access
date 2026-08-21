"""Tests for ROIAccess — manifest discovery, path resolution and reads."""

import pytest

from AOTaccess.roi_access import ROIAccess
from AOTaccess.errors import DataNotFoundError


def test_discovery_from_synthetic_manifest(synthetic_roi):
    r = ROIAccess(root_dir=synthetic_roi)
    assert r.atlases() == ["demo", "seg"]
    assert r.rois() == ["AAA", "SSS"]
    assert r.rois(subject="sub-001") == ["AAA", "SSS"]
    assert "balanced" in r.conservativeness_levels()


def test_atlas_rois_partitions_the_pooled_roi_list(synthetic_roi):
    r = ROIAccess(root_dir=synthetic_roi)
    # rois() pools names across atlases; atlas_rois() is per-atlas
    assert r.atlas_rois("demo") == ["AAA"]
    assert r.atlas_rois("seg") == ["SSS"]


def test_default_resolution_is_space_aware(synthetic_roi):
    """MNI is built at 1p25mm only; subject-native prefers 2p0mm."""
    r = ROIAccess(root_dir=synthetic_roi)
    assert "res-1p25mm" in r.mask_path(1, "AAA", atlas="demo", space="MNI").parts
    assert "res-2p0mm" in r.mask_path(1, "AAA", atlas="demo", space="T1w").parts
    # the MNI default now resolves to a real file rather than a dead path
    assert r.read_mask(1, "AAA", atlas="demo", space="MNI").sum() > 0


def test_default_cons_falls_back_to_an_atlas_sole_level(synthetic_roi):
    """'seg' ships only cons-labels; 'demo' keeps 'balanced'."""
    r = ROIAccess(root_dir=synthetic_roi)
    assert r.available_cons(1, "seg") == ["labels"]
    assert r.available_cons(1, "demo") == ["balanced"]
    assert "cons-labels" in r.mask_path(1, "SSS", atlas="seg").parts
    assert "cons-balanced" in r.mask_path(1, "AAA", atlas="demo").parts
    assert r.read_mask(1, "SSS", atlas="seg").sum() > 0


def test_explicit_res_and_cons_still_win(synthetic_roi):
    r = ROIAccess(root_dir=synthetic_roi)
    p = r.mask_path(1, "AAA", atlas="demo", space="T1w",
                    res="1p25mm", cons="balanced")
    assert "res-1p25mm" in p.parts


def test_partial_listing_does_not_masquerade_as_a_sole_level(synthetic_roi):
    """A half-written res dir must not redirect the read to another level.

    The store is rebuilt in place, so one resolution can list a single
    level while the atlas really ships several. Corroborating across the
    atlas's resolutions keeps 'balanced' as the default.
    """
    demo = synthetic_roi / "derivatives/roi/sub-001/fsnative_volume/atlas-demo"
    # res-1p25mm is mid-write and shows only 'strict'
    (demo / "res-1p25mm" / "cons-strict").mkdir(parents=True)

    r = ROIAccess(root_dir=synthetic_roi)
    assert r.available_cons(1, "demo", res="1p25mm") == ["strict"]
    # ... but the default still resolves to balanced, not strict
    assert "cons-balanced" in r.mask_path(1, "AAA", atlas="demo").parts


def test_ambiguous_cons_raises_instead_of_guessing(synthetic_roi):
    """Several non-preferred levels and no 'balanced' — do not pick one."""
    demo = synthetic_roi / "derivatives/roi/sub-001/fsnative_volume/atlas-demo"
    for level in ("strict", "liberal"):
        (demo / "res-2p0mm" / f"cons-{level}").mkdir(parents=True)
    for stale in (demo / "res-2p0mm").glob("cons-balanced"):
        for f in stale.iterdir():
            f.unlink()
        stale.rmdir()

    r = ROIAccess(root_dir=synthetic_roi)
    with pytest.raises(ValueError, match="pass cons= explicitly"):
        r.mask_path(1, "AAA", atlas="demo")


def test_empty_listing_is_not_cached(synthetic_roi):
    """A momentarily absent atlas dir must not be remembered as empty."""
    r = ROIAccess(root_dir=synthetic_roi)
    assert r.available_cons(1, "later") == []

    built = (synthetic_roi / "derivatives/roi/sub-001/fsnative_volume"
             / "atlas-later/res-2p0mm/cons-balanced")
    built.mkdir(parents=True)
    assert r.available_cons(1, "later") == ["balanced"]


def test_availability_queries(synthetic_roi):
    r = ROIAccess(root_dir=synthetic_roi)
    assert r.available_atlases(1) == ["demo", "seg"]
    assert r.available_atlases(1, space="MNI") == ["demo"]
    assert r.available_resolutions(1, atlas="demo") == ["2p0mm"]
    assert r.available_atlases("sub-999") == []


def test_provenance_and_build_status(synthetic_roi):
    r = ROIAccess(root_dir=synthetic_roi)
    prov = r.provenance()
    assert prov["manifest_schema_version"] == "1.1.0"
    assert prov["generated_by"] == "aot_rois 0.1.0"
    assert r.schema_version() == (1, 1, 0)
    assert r.is_complete() is True
    assert r.failed_outputs() == []
    assert r.build_warnings() == [
        {"code": "validation", "message": "1 check failed"}
    ]
    assert r.cons_info("labels")["description"] == "seg-only"


def test_build_status_absent_from_older_manifests(synthetic_roi):
    """A manifest predating the 1.1.0 keys must not raise."""
    import yaml
    path = synthetic_roi / "derivatives/roi/MANIFEST.yaml"
    manifest = yaml.safe_load(path.read_text())
    del manifest["build_status"]
    del manifest["manifest_schema_version"]
    path.write_text(yaml.safe_dump(manifest))

    r = ROIAccess(root_dir=synthetic_roi)
    assert r.build_status() == {}
    assert r.build_warnings() == []
    assert r.failed_outputs() == []
    assert r.is_complete() is False
    assert r.schema_version() is None


def test_unknown_subject_raises_data_not_found(synthetic_roi):
    r = ROIAccess(root_dir=synthetic_roi)
    with pytest.raises(DataNotFoundError, match="not in the ROI library"):
        r.rois(subject=999)


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
def test_sub006_is_a_first_class_subject(aot_config):
    """sub-006 joined the ROI library on 2026-08-21."""
    r = ROIAccess(config=aot_config)
    assert "sub-006" in r.subjects()
    assert r.missing_rois(6) == {}
    # same ROI set as an established subject
    assert set(r.rois(subject=6)) == set(r.rois(subject=5))
    mask = r.read_mask(6, "V1v", atlas="wang_2015", space="T1w", res="2p0mm")
    # sub-006's GLMsingle grid — the mask indexes its betas directly
    assert mask.shape == (65, 75, 86)
    assert mask.sum() > 0


@pytest.mark.cluster
def test_real_defaults_resolve_for_mni_and_aseg(aot_config):
    """The default res/cons must resolve on the real store, not just T1w+wang."""
    r = ROIAccess(config=aot_config)
    assert r.mask_path(6, "V1v", atlas="wang_2015", space="MNI").exists()
    assert r.available_cons(6, "fs_aseg") == ["labels"]
    assert r.mask_path(6, "Left_Hippocampus", atlas="fs_aseg").exists()


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
