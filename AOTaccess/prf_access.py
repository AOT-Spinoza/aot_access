"""Convenience access to the pRF localizer.

pRF fits live in the localizer store (``derivatives/localizers/prf/``). This
module is a thin, pRF-specific convenience layer over
:class:`~AOTaccess.localizer_access.LocalizerAccess`: it keeps the familiar
``read_param`` / ``read_noiseceiling`` names and adds optional R2 masking.
New code can equally use ``LocalizerAccess`` directly with ``localizer="prf"``.
"""

from AOTaccess.localizer_access import LocalizerAccess

_LOCALIZER = "prf"


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
        return self.localizer.maps(_LOCALIZER, model=model)

    def models(self):
        """List the pRF fit models ('gauss', 'norm')."""
        return self.localizer.models(_LOCALIZER)

    def param_path(self, sub, param, model="gauss", resolution="2.0mm",
                   runpart="all", rec="nordicstc"):
        """Path to a fitted pRF parameter map."""
        return self.localizer.map_path(
            _LOCALIZER, sub, param, model=model, resolution=resolution,
            runpart=runpart, rec=rec,
        )

    def read_param(self, sub, param, model="gauss", resolution="2.0mm",
                   runpart="all", rec="nordicstc", mask=False,
                   mask_r2_threshold=0.1):
        """Read a fitted pRF parameter map as an ndarray.

        With ``mask=True``, voxels whose R2 is below ``mask_r2_threshold`` are
        zeroed (the R2 map itself is never masked).
        """
        data = self.localizer.read_map(
            _LOCALIZER, sub, param, model=model, resolution=resolution,
            runpart=runpart, rec=rec,
        )
        if mask and param != "r2":
            r2 = self.localizer.read_map(
                _LOCALIZER, sub, "r2", model=model, resolution=resolution,
                runpart=runpart, rec=rec,
            )
            data[r2 < mask_r2_threshold] = 0
        return data

    def read_noiseceiling(self, sub, resolution="2.0mm", rec="nordicstc",
                          mask=False, mask_r2_threshold=0.1):
        """Read the pRF-session split-half noise-ceiling map as an ndarray."""
        data = self.localizer.read_map(
            _LOCALIZER, sub, "noiseceiling", resolution=resolution, rec=rec,
        )
        if mask:
            r2 = self.localizer.read_map(
                _LOCALIZER, sub, "r2", resolution=resolution,
            )
            data[r2 < mask_r2_threshold] = 0
        return data
