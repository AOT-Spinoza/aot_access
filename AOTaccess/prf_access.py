"""Access to fitted population-receptive-field (pRF) parameter maps.

pRF fits live under ``<prf>/sub-XXX/prf_fits/params/`` as one NIfTI per fitted
parameter. ``read_param`` loads any of them; a parameter is named by its
on-disk suffix (see ``PRF_PARAMS``), so the name maps 1:1 to the filename.

Two fit models produce volumetric parameter maps: ``gauss`` (a 2D Gaussian
pRF) and ``norm`` (a divisive-normalization pRF, which exposes the extra
surround/normalization parameters). ``params(model)`` lists what each provides.
The ``dog`` model only writes a combined ``.tsv``, so it has no per-parameter
maps and is not in the registry.
"""

from pathlib import Path
import yaml
import nibabel as nib


# on-disk parameter suffix -> set of fit models that produce that map
PRF_PARAMS = {
    "r2": {"gauss", "norm"},          # variance explained by the fit
    "ecc": {"gauss", "norm"},         # eccentricity
    "polar": {"gauss", "norm"},       # polar angle
    "prf_size": {"gauss", "norm"},    # pRF size
    "prf_ampl": {"gauss", "norm"},    # pRF amplitude
    "bold_bsl": {"gauss", "norm"},    # BOLD baseline
    "x": {"gauss", "norm"},           # pRF centre, x
    "y": {"gauss", "norm"},           # pRF centre, y
    "hrf_deriv": {"gauss"},           # HRF derivative param (gauss naming)
    "hrf_dsip": {"gauss"},            # HRF dispersion param (gauss naming)
    "hrf_delay": {"norm"},            # HRF first param (norm naming)
    "hrf_disp": {"norm"},             # HRF dispersion param (norm naming)
    "BDratio": {"norm"},              # normalization B/D ratio
    "surr_ampl": {"norm"},            # surround amplitude
    "surr_bsl": {"norm"},             # surround baseline
    "surr_size": {"norm"},            # surround size
    "neur_bsl": {"norm"},             # neural baseline
}


class PrfAccess:
    def __init__(self, root_dir: Path = None):
        """Initialize a PrfAccess instance.

        Parameters:
            root_dir (Path): If given, the pRF derivatives are ``root_dir / "prf"``.
                Otherwise the path is read from settings.yml.
        """
        if root_dir is not None:
            self.prf_main_dir = Path(root_dir) / "prf"
        else:
            basedir = Path(__file__).resolve().parent
            settings = yaml.safe_load(open(basedir / "settings.yml"))
            self.prf_main_dir = Path(settings["paths"]["prf"])

    def get_prf_dir_path(self):
        """Return the root pRF derivatives directory."""
        return self.prf_main_dir

    # ------------------------------------------------------------------
    # discovery
    # ------------------------------------------------------------------
    @staticmethod
    def params(model: str = None):
        """List pRF parameter names.

        With ``model`` given ('gauss' or 'norm'), returns only the parameters
        that model produces; otherwise returns every known parameter.
        """
        if model is None:
            return sorted(PRF_PARAMS)
        return sorted(p for p, models in PRF_PARAMS.items() if model in models)

    # ------------------------------------------------------------------
    # parameter maps
    # ------------------------------------------------------------------
    def param_path(self, sub: int, param: str, model: str = "gauss",
                   resolution: str = "2.0mm", runpart: str = "all",
                   rec: str = "nordicstc"):
        """Path to a fitted pRF parameter map.

        Parameters:
            sub (int): Subject number.
            param (str): Parameter name — one of :meth:`params` (the on-disk suffix).
            model (str): Fit model, 'gauss' or 'norm'.
            resolution (str): EPI resolution, e.g. '2.0mm'.
            runpart (str): Which runs were fit — 'all', 'firsthalf', 'secondhalf'.
            rec (str): Reconstruction type.

        Returns:
            pathlib.Path: Path to the parameter map NIfTI.
        """
        self._check(param, model)
        fname = (
            f"sub-{sub:03d}_ses-pRF_task-pRF_rec-{rec}_run-{runpart}"
            f"_model-{model}_stage-iter_space-epi_{resolution}"
            f"_desc-prf_params_{param}.nii.gz"
        )
        return self.prf_main_dir / f"sub-{sub:03d}" / "prf_fits" / "params" / fname

    def read_param(self, sub: int, param: str, model: str = "gauss",
                   resolution: str = "2.0mm", runpart: str = "all",
                   rec: str = "nordicstc", mask: bool = False,
                   mask_r2_threshold: float = 0.1):
        """Read a fitted pRF parameter map as an ndarray.

        With ``mask=True``, voxels whose R2 is below ``mask_r2_threshold`` are
        zeroed (the R2 map itself is never masked).

        Returns:
            numpy.ndarray: The parameter map.
        """
        path = self.param_path(sub, param, model, resolution, runpart, rec)
        if not path.exists():
            raise FileNotFoundError(
                f"pRF parameter map not found: {path}\n"
                f"(sub={sub}, param={param}, model={model}, "
                f"resolution={resolution}, runpart={runpart}, rec={rec})"
            )
        data = nib.load(path).get_fdata()
        if mask and param != "r2":
            r2 = self.read_param(sub, "r2", model, resolution, runpart, rec)
            data[r2 < mask_r2_threshold] = 0
        return data

    # ------------------------------------------------------------------
    # noise ceiling
    # ------------------------------------------------------------------
    def noiseceiling_path(self, sub: int, resolution: str = "2.0mm",
                          rec: str = "nordicstc"):
        """Path to the pRF-session noise-ceiling map."""
        fname = (
            f"sub-{sub:03d}_ses-pRF_task-pRF_rec-{rec}_run-noiseceiling"
            f"_part-mag_bold_space-epi_{resolution}.nii.gz"
        )
        return self.prf_main_dir / f"sub-{sub:03d}" / "prep" / fname

    def read_noiseceiling(self, sub: int, resolution: str = "2.0mm",
                          rec: str = "nordicstc", mask: bool = False,
                          mask_r2_threshold: float = 0.1):
        """Read the pRF-session noise-ceiling map as an ndarray.

        With ``mask=True``, voxels below the gauss-model R2 threshold are zeroed.
        """
        path = self.noiseceiling_path(sub, resolution, rec)
        if not path.exists():
            raise FileNotFoundError(f"pRF noise-ceiling map not found: {path}")
        data = nib.load(path).get_fdata()
        if mask:
            r2 = self.read_param(sub, "r2", "gauss", resolution)
            data[r2 < mask_r2_threshold] = 0
        return data

    # ------------------------------------------------------------------
    # helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _check(param: str, model: str):
        """Validate a (param, model) pair against the registry."""
        if param not in PRF_PARAMS:
            raise ValueError(
                f"Unknown pRF parameter '{param}'. Available: {sorted(PRF_PARAMS)}"
            )
        if model not in PRF_PARAMS[param]:
            raise ValueError(
                f"pRF parameter '{param}' is not produced by model '{model}'. "
                f"It is available for: {sorted(PRF_PARAMS[param])}"
            )
