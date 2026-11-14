"""Tests for PycortexAccess — flatmap caches, reference grid and transforms."""

import json

import numpy as np
import nibabel as nib
import pytest
from scipy import sparse

from AOTaccess.errors import DataNotFoundError
from AOTaccess.pycortex_access import PycortexAccess


@pytest.fixture
def synthetic_pycortex(tmp_path):
    """A minimal pycortex db with flatmap caches, reference grid and surfaces."""
    root = tmp_path / "derivatives" / "pycortex"
    subject = root / "db" / "sub-001"
    (subject / "cache").mkdir(parents=True)
    (subject / "transforms" / "res-2p0mm").mkdir(parents=True)
    (subject / "surfaces").mkdir(parents=True)

    mask = np.array([[True, False], [True, True]])
    np.savez(
        subject / "cache" / "flatmask_1024.npz",
        mask=mask, extents=np.array([-1.0, 1.0, -1.0, 1.0]),
    )
    mapper = sparse.csr_matrix(
        ([1.0, 1.0, 1.0], ([0, 1, 2], [0, 1, 2])), shape=(3, 8)
    )
    np.savez(
        subject / "cache" / "flatpixel_res-2p0mm_1024_nearest_l32.npz",
        data=mapper.data, indices=mapper.indices, indptr=mapper.indptr,
        shape=mapper.shape,
    )
    np.savez(
        subject / "cache" / "flatpixel_res-2p0mm_1024_nearest_d0.8.npz",
        data=mapper.data, indices=mapper.indices, indptr=mapper.indptr,
        shape=mapper.shape,
    )
    nib.save(
        nib.Nifti1Image(np.zeros((2, 2, 2)), np.eye(4)),
        str(subject / "transforms" / "res-2p0mm" / "reference.nii.gz"),
    )
    (subject / "transforms" / "res-2p0mm" / "matrices.xfm").write_text(
        json.dumps({"coord": np.eye(4).tolist()})
    )
    for kind in ("flat", "pia", "wm"):
        for hemi in ("lh", "rh"):
            (subject / "surfaces" / f"{kind}_{hemi}.gii").write_bytes(b"gifti")
    return tmp_path


def test_store_root_and_paths(synthetic_pycortex):
    pc = PycortexAccess(root_dir=synthetic_pycortex)
    root = synthetic_pycortex / "derivatives" / "pycortex" / "db"
    assert pc.db_root() == root
    assert pc.subject_dir(1) == root / "sub-001"
    assert pc.flatmask_path(1).name == "flatmask_1024.npz"
    assert pc.flatpixel_path(1, sampler="l32").name == (
        "flatpixel_res-2p0mm_1024_nearest_l32.npz"
    )
    assert pc.reference_path(1).as_posix().endswith(
        "transforms/res-2p0mm/reference.nii.gz"
    )
    assert pc.matrices_path(1).name == "matrices.xfm"
    assert pc.surface_path(1, "pia", "rh").name == "pia_rh.gii"
    with pytest.raises(ValueError):
        pc.surface_path(1, "nope", "lh")
    with pytest.raises(ValueError):
        pc.surface_path(1, "pia", "mh")


def test_flatmap_cache_paths_and_availability(synthetic_pycortex):
    pc = PycortexAccess(root_dir=synthetic_pycortex)
    paths = pc.flatmap_cache_paths(1)
    assert set(paths) == {"mask", "mapper", "reference", "matrices"}
    assert all(path.is_file() for path in paths.values())
    assert pc.has_flatmap_cache(1)
    assert pc.has_flatmap_cache(1, sampler="d0.8")
    assert not pc.has_flatmap_cache(2)


def test_reads_and_validate(synthetic_pycortex):
    pc = PycortexAccess(root_dir=synthetic_pycortex)
    mask = pc.read_flatmask(1)
    assert mask["mask"].sum() == 3
    assert list(mask["extents"]) == [-1.0, 1.0, -1.0, 1.0]
    mapper = pc.read_flatpixel_mapper(1)
    assert mapper.shape == (3, 8)
    reference = pc.read_reference(1)
    assert reference.shape == (2, 2, 2)
    assert "coord" in pc.read_matrices(1)
    audit = pc.validate_flatmap_cache(1)
    assert audit["shape_ok"] and audit["mapper_rows"] == 3
    assert audit["reference_voxels"] == 8


def test_missing_files_raise(synthetic_pycortex):
    pc = PycortexAccess(root_dir=synthetic_pycortex)
    with pytest.raises(DataNotFoundError):
        pc.read_flatmask(2)
    with pytest.raises(DataNotFoundError):
        pc.read_flatpixel_mapper(1, sampler="nope")
    with pytest.raises(DataNotFoundError):
        pc.read_reference(2)
    with pytest.raises(DataNotFoundError):
        pc.read_matrices(2)


def test_dimension_mismatch_raises(synthetic_pycortex):
    pc = PycortexAccess(root_dir=synthetic_pycortex)
    subject = synthetic_pycortex / "derivatives" / "pycortex" / "db" / "sub-001"
    # overwrite the mapper with a wrong number of rows
    mapper = sparse.csr_matrix(([1.0], ([0], [0])), shape=(2, 8))
    np.savez(
        subject / "cache" / "flatpixel_res-2p0mm_1024_nearest_l32.npz",
        data=mapper.data, indices=mapper.indices, indptr=mapper.indptr,
        shape=mapper.shape,
    )
    with pytest.raises(ValueError):
        pc.validate_flatmap_cache(1)
