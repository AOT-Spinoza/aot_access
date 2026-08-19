"""Convenience access to the pRF localizer.

pRF fits live in the localizer store (``derivatives/localizers/prf/``). This
module is a thin, pRF-specific convenience layer over
:class:`~AOTaccess.localizer_access.LocalizerAccess`: it keeps the familiar
``read_param`` / ``read_noiseceiling`` names and adds access to parameter
tables, predictions, and residuals. New code can equally use
``LocalizerAccess`` directly with ``localizer="prf"``.
"""

import pandas as pd
import numpy as np

from AOTaccess.errors import DataNotFoundError
from AOTaccess.localizer_access import LocalizerAccess

_LOCALIZER = "prf"

_VOLUME_METHODS = {
    "read_R2": "r2",
    "read_eccentricity": "ecc",
    "read_prfsize": "prf_size",
    "read_polar_angle": "polar",
    "read_x_position": "x",
    "read_y_position": "y",
    "read_prf_amplitude": "prf_ampl",
    "read_hrf_delay": "hrf_delay",
    "read_hrf_disp": "hrf_disp",
    "read_BDratio": "BDratio",
    "read_bold_baseline": "bold_bsl",
    "read_surround_amplitude": "surr_ampl",
    "read_surround_baseline": "surr_bsl",
    "read_surround_size": "surr_size",
    "read_neuro_baseline": "neur_bsl",
    "read_srf_amplitude": "srf_amplitude",
    "read_srf_size": "srf_size",
}


class PrfAccess:
    def __init__(self, root_dir=None, config=None, localizer_access=None):
        """Initialize a PrfAccess instance.

        Parameters:
            root_dir: If given, resolve paths relative to this dataset root.
            config (Config): An explicit Config; takes precedence over root_dir.
            localizer_access (LocalizerAccess): An existing accessor to reuse.
        """
        self.localizer = (
            localizer_access
            if localizer_access is not None
            else LocalizerAccess(root_dir=root_dir, config=config)
        )
        self.config = self.localizer.config

    def params(self, model=None):
        """List pRF parameter names (optionally filtered to one fit model)."""
        maps = self.localizer.maps(_LOCALIZER, model=model)
        return [
            name
            for name in maps
            if self.localizer.map_info(_LOCALIZER, name).get("template")
            == "param_map"
        ]

    def models(self):
        """List the pRF fit models (currently gauss, DoG, and DN)."""
        return self.localizer.models(_LOCALIZER)

    def get_method_list(self, model="norm"):
        """List parameter-volume readers available for one fit model.

        The default is the divisive-normalization model, matching the default
        of the named readers returned here. Pass the same explicit ``model``
        to those readers when requesting Gaussian or DoG maps.
        """
        if model not in self.models():
            raise ValueError(
                f"Unknown pRF model '{model}'; available: {self.models()}"
            )
        available_params = set(self.params(model))
        return [
            method
            for method, param in _VOLUME_METHODS.items()
            if param in available_params
        ]

    @staticmethod
    def _fit_params(model, space, resolution, runpart, rec):
        return {
            "model": model,
            "space": space,
            "resolution": resolution,
            "runpart": runpart,
            "rec": rec,
        }

    def param_path(self, sub, param, model="gauss", resolution="2p0mm",
                   runpart="all", rec="nordicstc", space="T1w"):
        """Path to a fitted pRF parameter map."""
        return self.localizer.map_path(
            _LOCALIZER,
            sub,
            param,
            **self._fit_params(model, space, resolution, runpart, rec),
        )

    def read_param(self, sub, param, model="gauss", resolution="2p0mm",
                   runpart="all", rec="nordicstc", mask=False,
                   mask_r2_threshold=0.1, space="T1w"):
        """Read a fitted pRF parameter map as an ndarray.

        With ``mask=True``, voxels whose R2 is below ``mask_r2_threshold`` are
        set to NaN (the R2 map itself is never masked).
        """
        fit_params = self._fit_params(
            model, space, resolution, runpart, rec
        )
        data = self.localizer.read_map(_LOCALIZER, sub, param, **fit_params)
        if mask and param != "r2":
            r2 = self.localizer.read_map(
                _LOCALIZER, sub, "r2", **fit_params
            )
            data[r2 < mask_r2_threshold] = np.nan
        return data

    # Named readers retained for plotting notebooks that iterate over
    # get_method_list().  Extra positional and keyword arguments follow the
    # read_param signature.
    def read_R2(self, sub, model="norm", *args, **kwargs):
        return self.read_param(sub, "r2", model, *args, **kwargs)

    def read_eccentricity(self, sub, model="norm", *args, **kwargs):
        return self.read_param(sub, "ecc", model, *args, **kwargs)

    def read_prfsize(self, sub, model="norm", *args, **kwargs):
        return self.read_param(sub, "prf_size", model, *args, **kwargs)

    def read_polar_angle(self, sub, model="norm", *args, **kwargs):
        return self.read_param(sub, "polar", model, *args, **kwargs)

    def read_x_position(self, sub, model="norm", *args, **kwargs):
        return self.read_param(sub, "x", model, *args, **kwargs)

    def read_y_position(self, sub, model="norm", *args, **kwargs):
        return self.read_param(sub, "y", model, *args, **kwargs)

    def read_prf_amplitude(self, sub, model="norm", *args, **kwargs):
        return self.read_param(sub, "prf_ampl", model, *args, **kwargs)

    def read_hrf_delay(self, sub, model="norm", *args, **kwargs):
        return self.read_param(sub, "hrf_delay", model, *args, **kwargs)

    def read_hrf_disp(self, sub, model="norm", *args, **kwargs):
        return self.read_param(sub, "hrf_disp", model, *args, **kwargs)

    def read_BDratio(self, sub, model="norm", *args, **kwargs):
        return self.read_param(sub, "BDratio", model, *args, **kwargs)

    def read_bold_baseline(self, sub, model="norm", *args, **kwargs):
        return self.read_param(sub, "bold_bsl", model, *args, **kwargs)

    def read_surround_amplitude(self, sub, model="norm", *args, **kwargs):
        return self.read_param(sub, "surr_ampl", model, *args, **kwargs)

    def read_surround_baseline(self, sub, model="norm", *args, **kwargs):
        return self.read_param(sub, "surr_bsl", model, *args, **kwargs)

    def read_surround_size(self, sub, model="norm", *args, **kwargs):
        return self.read_param(sub, "surr_size", model, *args, **kwargs)

    def read_neuro_baseline(self, sub, model="norm", *args, **kwargs):
        return self.read_param(sub, "neur_bsl", model, *args, **kwargs)

    def read_srf_amplitude(self, sub, model="dog", *args, **kwargs):
        return self.read_param(sub, "srf_amplitude", model, *args, **kwargs)

    def read_srf_size(self, sub, model="dog", *args, **kwargs):
        return self.read_param(sub, "srf_size", model, *args, **kwargs)

    # Compatibility aliases for notebooks written before the braincoder HRF
    # parameter names were corrected.
    def read_hrf_deriv(self, sub, model="gauss", *args, **kwargs):
        return self.read_hrf_delay(sub, model, *args, **kwargs)

    def read_hrf_dsip(self, sub, model="gauss", *args, **kwargs):
        return self.read_hrf_disp(sub, model, *args, **kwargs)

    def parameter_table_path(self, sub, model="gauss", resolution="2p0mm",
                             runpart="all", rec="nordicstc", space="T1w"):
        """Path to a fitted pRF parameter table (TSV)."""
        return self.localizer.resolve(
            _LOCALIZER,
            "parameter_table",
            sub=sub,
            **self._fit_params(model, space, resolution, runpart, rec),
        )

    def read_parameter_table(self, sub, model="gauss", resolution="2p0mm",
                             runpart="all", rec="nordicstc", space="T1w"):
        """Read a fitted pRF parameter table as a pandas DataFrame."""
        path = self.parameter_table_path(
            sub,
            model=model,
            resolution=resolution,
            runpart=runpart,
            rec=rec,
            space=space,
        )
        if not path.exists():
            raise DataNotFoundError(f"pRF parameter table not found: {path}")
        return pd.read_csv(path, sep="\t")

    def prediction_path(self, sub, model="gauss", resolution="2p0mm",
                        runpart="cv", rec="nordicstc", space="T1w"):
        """Path to a pRF model-prediction time series."""
        return self.localizer.map_path(
            _LOCALIZER,
            sub,
            "predictions",
            **self._fit_params(model, space, resolution, runpart, rec),
        )

    def read_prediction(self, sub, model="gauss", resolution="2p0mm",
                        runpart="cv", rec="nordicstc", space="T1w"):
        """Read a pRF model-prediction time series as an ndarray."""
        return self.localizer.read_map(
            _LOCALIZER,
            sub,
            "predictions",
            **self._fit_params(model, space, resolution, runpart, rec),
        )

    def residual_path(self, sub, model="gauss", resolution="2p0mm",
                      runpart="cv", rec="nordicstc", space="T1w"):
        """Path to a pRF residual time series."""
        return self.localizer.map_path(
            _LOCALIZER,
            sub,
            "residuals",
            **self._fit_params(model, space, resolution, runpart, rec),
        )

    def read_residual(self, sub, model="gauss", resolution="2p0mm",
                      runpart="cv", rec="nordicstc", space="T1w"):
        """Read a pRF residual time series as an ndarray."""
        return self.localizer.read_map(
            _LOCALIZER,
            sub,
            "residuals",
            **self._fit_params(model, space, resolution, runpart, rec),
        )

    def noiseceiling_path(self, sub, resolution="2p0mm", rec="nordicstc",
                          space="T1w"):
        """Path to the pRF-session split-half noise-ceiling map."""
        return self.localizer.map_path(
            _LOCALIZER,
            sub,
            "noiseceiling",
            space=space,
            resolution=resolution,
            rec=rec,
        )

    def read_noiseceiling(self, sub, resolution="2p0mm", rec="nordicstc",
                          mask=False, mask_r2_threshold=0.1, space="T1w",
                          mask_model="gauss", mask_runpart="all"):
        """Read the pRF-session split-half noise-ceiling map as an ndarray.

        With ``mask=True``, voxels whose R2 (from the ``mask_model`` fit) is
        below ``mask_r2_threshold`` are set to NaN, matching
        :meth:`read_param`.
        """
        data = self.localizer.read_map(
            _LOCALIZER,
            sub,
            "noiseceiling",
            space=space,
            resolution=resolution,
            rec=rec,
        )
        if mask:
            r2 = self.localizer.read_map(
                _LOCALIZER,
                sub,
                "r2",
                **self._fit_params(
                    mask_model, space, resolution, mask_runpart, rec
                ),
            )
            data[r2 < mask_r2_threshold] = np.nan
        return data
