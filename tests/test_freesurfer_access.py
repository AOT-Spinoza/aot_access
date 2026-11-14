"""Tests for FreeSurferAccess — reconstruction directories, volumes and surfaces."""

import numpy as np
import nibabel as nib
import pytest

from AOTaccess.errors import DataNotFoundError
from AOTaccess.freesurfer_access import FreeSurferAccess


def _save_mgz(path, data=None):
    path.parent.mkdir(parents=True, exist_ok=True)
    data = np.zeros((4, 4, 4), dtype=np.int16) if data is None else data
    nib.save(nib.Nifti1Image(data, np.eye(4)), str(path))


@pytest.fixture
def synthetic_freesurfer(tmp_path):
    """A minimal freesurfer_AOT store with a current and an old reconstruction."""
    root = tmp_path / "derivatives" / "freesurfer_AOT"
    for subject, has_surfaces in (("sub-004", True), ("sub-004_old_problematic", True)):
        sub = root / subject
        for name in ("T1.mgz", "T2.mgz", "ribbon.mgz", "brainmask.mgz"):
            _save_mgz(sub / "mri" / name)
        if has_surfaces:
            for hemi in ("lh", "rh"):
                for kind in ("pial", "white"):
                    surf = sub / "surf" / f"{hemi}.{kind}"
                    surf.parent.mkdir(parents=True, exist_ok=True)
                    surf.write_bytes(b"#!ascii synthetic surface\n0 0\n")
    # a directory without mri/T1.mgz must not be listed as a subject
    (root / "fsaverage" / "surf").mkdir(parents=True)
    return tmp_path


def test_subject_path_and_variants(synthetic_freesurfer):
    fs = FreeSurferAccess(root_dir=synthetic_freesurfer)
    root = synthetic_freesurfer / "derivatives" / "freesurfer_AOT"
    assert fs.subject_path(4) == root / "sub-004"
    assert fs.subject_path("4") == root / "sub-004"
    assert fs.subject_path("sub-004") == root / "sub-004"
    assert fs.subject_path(4, variant="old_problematic") == root / "sub-004_old_problematic"
    assert fs.subject_path("sub-004_old_problematic") == root / "sub-004_old_problematic"


def test_subject_path_rejects_garbage(synthetic_freesurfer):
    fs = FreeSurferAccess(root_dir=synthetic_freesurfer)
    with pytest.raises(ValueError):
        fs.subject_path("left-hemisphere")


def test_subjects_lists_only_complete_reconstructions(synthetic_freesurfer):
    fs = FreeSurferAccess(root_dir=synthetic_freesurfer)
    assert fs.subjects() == ["sub-004", "sub-004_old_problematic"]
    assert fs.exists(4) and not fs.exists(99)


def test_canonical_volume_paths(synthetic_freesurfer):
    fs = FreeSurferAccess(root_dir=synthetic_freesurfer)
    sub = synthetic_freesurfer / "derivatives" / "freesurfer_AOT" / "sub-004"
    assert fs.t1_mgz_path(4) == sub / "mri" / "T1.mgz"
    assert fs.t2_mgz_path(4) == sub / "mri" / "T2.mgz"
    assert fs.ribbon_path(4) == sub / "mri" / "ribbon.mgz"
    assert fs.brainmask_path(4) == sub / "mri" / "brainmask.mgz"
    assert fs.tentorium_path(4) == sub / "mri" / "tentorium-dura.nii.gz"
    assert fs.sinus_path(4) == sub / "mri" / "T2_brain_sinus.nii.gz"


def test_surface_paths_and_has_surfaces(synthetic_freesurfer):
    fs = FreeSurferAccess(root_dir=synthetic_freesurfer)
    assert fs.surf_path(4, "lh", "pial").name == "lh.pial"
    assert fs.has_surfaces(4)
    assert fs.has_surfaces("sub-004_old_problematic")
    with pytest.raises(ValueError):
        fs.surf_path(4, "mh", "pial")
    with pytest.raises(ValueError):
        fs.surf_path(4, "lh", "nope")


def test_has_surfaces_false_when_a_file_is_missing(synthetic_freesurfer):
    fs = FreeSurferAccess(root_dir=synthetic_freesurfer)
    missing = synthetic_freesurfer / "derivatives" / "freesurfer_AOT" / "sub-004"
    (missing / "surf" / "rh.white").unlink()
    assert not fs.has_surfaces(4)


def test_readers_roundtrip(synthetic_freesurfer):
    fs = FreeSurferAccess(root_dir=synthetic_freesurfer)
    assert fs.read_t1(4).shape == (4, 4, 4)
    assert fs.read_ribbon(4).shape == (4, 4, 4)
    assert fs.read_brainmask(4).shape == (4, 4, 4)


def test_reader_missing_raises_data_not_found(synthetic_freesurfer):
    fs = FreeSurferAccess(root_dir=synthetic_freesurfer)
    with pytest.raises(DataNotFoundError):
        fs.read_t1(99)
