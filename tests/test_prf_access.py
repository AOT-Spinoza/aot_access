"""Tests for PrfAccess — the pRF-specific convenience wrapper."""

from pathlib import Path

import nibabel as nib
import numpy as np
import pandas as pd
import pytest

from AOTaccess.prf_access import PrfAccess


def _save_nifti(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    image = nib.Nifti1Image(np.asarray(data, dtype=np.float32), np.eye(4))
    nib.save(image, path)


@pytest.fixture
def synthetic_prf_access(tmp_path):
    localizer_dir = tmp_path / "derivatives/localizers/prf"
    localizer_dir.mkdir(parents=True)
    schema = Path(__file__).resolve().parents[1] / "schemas/localizer-manifest.example.yaml"
    (localizer_dir / "manifest.yaml").write_text(schema.read_text())

    access = PrfAccess(root_dir=tmp_path)
    values = np.arange(8, dtype=np.float32).reshape(2, 2, 2)
    r2 = np.array([0.0, 0.2, 0.05, 0.3, 0.4, 0.0, 0.5, 0.6]).reshape(2, 2, 2)

    _save_nifti(
        access.param_path(
            3, "ecc", model="dog", resolution="1p25mm", runpart="firsthalf"
        ),
        values,
    )
    _save_nifti(
        access.param_path(
            3, "r2", model="dog", resolution="1p25mm", runpart="firsthalf"
        ),
        r2,
    )
    _save_nifti(
        access.param_path(
            3, "ecc", model="norm", resolution="1p25mm", runpart="firsthalf"
        ),
        values + 100,
    )
    _save_nifti(
        access.param_path(
            3, "r2", model="norm", resolution="1p25mm", runpart="firsthalf"
        ),
        r2,
    )

    table_path = access.parameter_table_path(
        3, model="dog", resolution="1p25mm", runpart="firsthalf"
    )
    table_path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame({"x": [1.0], "r2": [0.5]}).to_csv(
        table_path, sep="\t", index=False
    )

    prediction = np.ones((2, 2, 2, 3), dtype=np.float32)
    residual = np.full((2, 2, 2, 3), 2.0, dtype=np.float32)
    _save_nifti(
        access.prediction_path(3, model="gauss", resolution="1p25mm"),
        prediction,
    )
    _save_nifti(
        access.residual_path(3, model="gauss", resolution="1p25mm"),
        residual,
    )
    _save_nifti(
        access.noiseceiling_path(3, resolution="1p25mm"),
        np.full((2, 2, 2), 0.75, dtype=np.float32),
    )
    return access


def test_new_hierarchy_and_dog_discovery(synthetic_prf_access):
    access = synthetic_prf_access
    assert access.models() == ["gauss", "dog", "norm"]
    assert "srf_amplitude" in access.params("dog")
    assert "neur_bsl" not in access.params("dog")

    path = access.param_path(
        "sub-003",
        "ecc",
        model="dog",
        resolution="1p25mm",
        runpart="firsthalf",
    )
    assert path.parent.name == "parameter_volumes"
    assert "space-T1w/res-1p25mm/fits" in path.as_posix()
    assert "run-firsthalf_model-dog" in path.name


def test_get_method_list_reports_volume_readers(synthetic_prf_access):
    methods = synthetic_prf_access.get_method_list()

    assert "models" not in methods
    assert "param_path" not in methods
    assert "read_param" not in methods
    assert "read_hrf_delay" in methods
    assert "read_hrf_disp" in methods
    assert "read_hrf_deriv" not in methods
    assert "read_hrf_dsip" not in methods
    assert "read_BDratio" in methods
    assert "read_neuro_baseline" in methods
    assert all(callable(getattr(synthetic_prf_access, name)) for name in methods)

    gauss_methods = synthetic_prf_access.get_method_list(model="gauss")
    assert "read_R2" in gauss_methods
    assert "read_BDratio" not in gauss_methods
    assert "read_neuro_baseline" not in gauss_methods

    dog_methods = synthetic_prf_access.get_method_list(model="dog")
    assert "read_surround_amplitude" in dog_methods
    assert "read_surround_size" in dog_methods
    assert "read_surround_baseline" not in dog_methods

    with pytest.raises(ValueError, match="Unknown pRF model"):
        synthetic_prf_access.get_method_list(model="invalid")

    default_eccentricity = synthetic_prf_access.read_eccentricity(
        3, resolution="1p25mm", runpart="firsthalf"
    )
    assert np.all(default_eccentricity == np.arange(8).reshape(2, 2, 2) + 100)

    eccentricity = synthetic_prf_access.read_eccentricity(
        3,
        model="dog",
        resolution="1p25mm",
        runpart="firsthalf",
        mask=True,
        mask_r2_threshold=0.1,
    )
    assert eccentricity.shape == (2, 2, 2)


def test_read_dog_param_and_mask(synthetic_prf_access):
    access = synthetic_prf_access
    full = access.read_param(
        3, "ecc", model="dog", resolution="1p25mm", runpart="firsthalf"
    )
    masked = access.read_param(
        3,
        "ecc",
        model="dog",
        resolution="1p25mm",
        runpart="firsthalf",
        mask=True,
        mask_r2_threshold=0.1,
    )
    assert full.shape == (2, 2, 2)
    assert np.all(masked[np.array([[[True, False], [True, False]], [[False, True], [False, False]]])] == 0)


def test_read_table_prediction_residual_and_noiseceiling(synthetic_prf_access):
    access = synthetic_prf_access
    table = access.read_parameter_table(
        3, model="dog", resolution="1p25mm", runpart="firsthalf"
    )
    assert list(table.columns) == ["x", "r2"]
    assert access.read_prediction(3, model="gauss", resolution="1p25mm").shape == (
        2,
        2,
        2,
        3,
    )
    assert np.all(
        access.read_residual(3, model="gauss", resolution="1p25mm") == 2.0
    )
    assert np.all(access.read_noiseceiling(3, resolution="1p25mm") == 0.75)


@pytest.mark.cluster
def test_params_are_model_specific(aot_config):
    p = PrfAccess(config=aot_config)
    assert "ecc" in p.params()
    assert "surr_size" in p.params("norm")
    assert "surr_size" not in p.params("gauss")


@pytest.mark.cluster
def test_read_param(aot_config):
    p = PrfAccess(config=aot_config)
    assert p.read_param(1, "ecc").shape == (69, 81, 86)


@pytest.mark.cluster
def test_read_param_masked_zeros_low_r2(aot_config):
    p = PrfAccess(config=aot_config)
    full = p.read_param(1, "ecc")
    masked = p.read_param(1, "ecc", mask=True)
    assert (masked != 0).sum() <= (full != 0).sum()


@pytest.mark.cluster
def test_read_noiseceiling(aot_config):
    p = PrfAccess(config=aot_config)
    assert p.read_noiseceiling(1).ndim == 3
