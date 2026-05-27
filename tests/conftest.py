"""Shared pytest fixtures and configuration for the AOTaccess test suite.

Tests split into two kinds:

* pure-unit tests run anywhere — they exercise path building, config resolution
  and manifest parsing against synthetic fixtures;
* ``@pytest.mark.cluster`` tests read the real AOT dataset and are skipped
  automatically when it is not reachable.
"""

import sys
from pathlib import Path

import numpy as np
import nibabel as nib
import yaml
import pytest

# make the AOTaccess package importable when running from a source checkout
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from AOTaccess.config import Config


def _cluster_available():
    """True when the real AOT dataset is reachable via settings.yml."""
    try:
        return Config().path("roi").exists()
    except Exception:
        return False


CLUSTER_AVAILABLE = _cluster_available()


def pytest_configure(config):
    config.addinivalue_line(
        "markers", "cluster: test needs the real AOT dataset on the cluster"
    )


def pytest_collection_modifyitems(config, items):
    """Skip cluster-marked tests when the dataset is not reachable."""
    if CLUSTER_AVAILABLE:
        return
    skip = pytest.mark.skip(reason="real AOT dataset not reachable")
    for item in items:
        if "cluster" in item.keywords:
            item.add_marker(skip)


@pytest.fixture
def aot_config():
    """A Config pointed at the real dataset (skips the test if unavailable)."""
    if not CLUSTER_AVAILABLE:
        pytest.skip("real AOT dataset not reachable")
    return Config()


def _save_nii(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    nib.save(nib.Nifti1Image(np.asarray(data, dtype=float), np.eye(4)), str(path))


@pytest.fixture
def synthetic_localizers(tmp_path):
    """A minimal localizers/ store with one 'demo' parametric localizer.

    Laid out under ``derivatives/`` to match Config's root_dir-mode layout.
    """
    loc = tmp_path / "derivatives" / "localizers" / "demo"
    loc.mkdir(parents=True)
    manifest = {
        "manifest_schema_version": "1.0.0",
        "localizer": "demo",
        "kind": "parametric",
        "description": "synthetic localizer",
        "subjects": ["sub-001"],
        "defaults": {"model": "m1", "res": "2p0mm"},
        "models": {"m1": {"full_name": "model one"}},
        "maps": {
            "alpha": {"full_name": "alpha", "models": ["m1"], "template": "map"},
            "beta": {"full_name": "beta", "models": [], "template": "map"},
        },
        "path_templates": {
            "map": {
                "template": "sub-{sub}/sub-{sub}_model-{model}_res-{res}_{map}.nii.gz",
                "parameters": ["sub", "map", "model", "res"],
            },
        },
    }
    (loc / "manifest.yaml").write_text(yaml.safe_dump(manifest))
    _save_nii(loc / "sub-001" / "sub-001_model-m1_res-2p0mm_alpha.nii.gz", np.ones((3, 3, 3)))
    _save_nii(loc / "sub-001" / "sub-001_model-m1_res-2p0mm_beta.nii.gz", np.full((3, 3, 3), 2.0))
    return tmp_path


@pytest.fixture
def synthetic_roi(tmp_path):
    """A minimal roi/ store with one 'demo' atlas and one ROI mask.

    Laid out under ``derivatives/`` to match Config's root_dir-mode layout.
    """
    roi = tmp_path / "derivatives" / "roi"
    manifest = {
        "atlases": {"demo": {"full_name": "demo atlas"}},
        "rois": {"AAA": {"full_name": "AAA", "source": "atlas"}},
        "subjects": {"sub-001": {"rois": ["AAA"], "missing_rois": {}}},
        "spaces": ["MNI152NLin2009cAsym"],
        "resolutions": {"mni": ["1p25mm"], "fsnative": ["2p0mm"]},
        "conservativeness_levels": {"balanced": {"threshold": 0.5}},
        "path_templates": {
            "mni_volume_mask_bilateral": {
                "template": (
                    "sub-{sub}/mni_volume/atlas-{atlas}/res-{res}/cons-{cons}/"
                    "sub-{sub}_atlas-{atlas}_label-{roi}_res-{res}_cons-{cons}_mask.nii.gz"
                ),
                "parameters": ["sub", "atlas", "roi", "res", "cons"],
            },
        },
    }
    roi.mkdir(parents=True)
    (roi / "MANIFEST.yaml").write_text(yaml.safe_dump(manifest))
    mask = (np.arange(27).reshape(3, 3, 3) > 13)
    _save_nii(
        roi / "sub-001/mni_volume/atlas-demo/res-1p25mm/cons-balanced/"
        "sub-001_atlas-demo_label-AAA_res-1p25mm_cons-balanced_mask.nii.gz",
        mask,
    )
    return tmp_path
