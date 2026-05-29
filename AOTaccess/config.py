"""Central configuration and path resolution for AOTaccess.

A :class:`Config` resolves the on-disk location of every derivative store. Each
access class holds a ``Config`` and asks it for paths, instead of every class
re-implementing the settings.yml lookup and the ``root_dir`` branching.

Two modes:

* **default** — paths come from ``settings.yml`` (absolute cluster paths).
  Override the settings file with the ``AOT_SETTINGS`` environment variable or
  an explicit ``settings_path``.
* **root_dir** — paths are resolved relative to one dataset root using the
  canonical layout in ``_RELATIVE_LAYOUT``. This is how a relocated/copied
  dataset is accessed; ``root_dir`` is the dataset root, not a single store.
"""

from pathlib import Path
import os
import yaml

from AOTaccess.errors import ConfigError

_SETTINGS_ENV = "AOT_SETTINGS"
_DEFAULT_SETTINGS = Path(__file__).resolve().parent / "settings.yml"

# Canonical location of each store relative to a dataset root (root_dir mode).
_RELATIVE_LAYOUT = {
    "glmsingle": "derivatives/glmsingle",
    "preproced": "derivatives/aot_prep",
    "bids": "bids/aot",
    "videos": "derivatives/stimuli/rescaled_final",
    "pictures": "derivatives/stimuli/pictures",
    "video_annotations": "derivatives/stimuli/annotations",
    "roi": "derivatives/roi",
    "localizers": "derivatives/localizers",
    "AOTdesignsettings": "aot/data/experiment/settings/main",
}

# Anatomy roots tried in order — dual-cluster (VU /research, Snellius /projects).
_ANATOMY_ROOTS = (
    "/research/FGB-CognitivePsychology-Knapen/shared/2024/visual/AOT/derivatives/anat-3T",
    "/projects/prjs1914/output/anat-3T",
    "/projects/prjs1914/derivatives/anat-3T",
)


class Config:
    def __init__(self, root_dir=None, settings_path=None):
        """Build a Config.

        Parameters:
            root_dir (Path | str): If given, resolve paths relative to this
                dataset root. Otherwise resolve from settings.yml.
            settings_path (Path | str): Explicit settings.yml location;
                defaults to the ``AOT_SETTINGS`` env var, then the packaged file.
        """
        self.root_dir = Path(root_dir) if root_dir is not None else None
        if settings_path is None:
            settings_path = os.environ.get(_SETTINGS_ENV, _DEFAULT_SETTINGS)
        self.settings_path = Path(settings_path)
        self._settings = None

    @property
    def settings(self):
        """Parsed settings.yml (lazy-loaded, cached)."""
        if self._settings is None:
            if not self.settings_path.exists():
                raise ConfigError(f"settings file not found: {self.settings_path}")
            with open(self.settings_path) as f:
                self._settings = yaml.safe_load(f) or {}
        return self._settings

    def path(self, key):
        """Absolute Path to a named store ('glmsingle', 'bids', 'roi', ...)."""
        if self.root_dir is not None:
            if key not in _RELATIVE_LAYOUT:
                raise ConfigError(
                    f"No relative layout known for store '{key}' (root_dir mode). "
                    f"Known: {sorted(_RELATIVE_LAYOUT)}"
                )
            return self.root_dir / _RELATIVE_LAYOUT[key]
        paths = self.settings.get("paths", {})
        if key not in paths:
            raise ConfigError(
                f"settings.yml defines no path for store '{key}'. "
                f"Known: {sorted(paths)}"
            )
        return Path(paths[key])

    def param(self, key, default=None):
        """A value from the settings 'parameters' section."""
        return self.settings.get("parameters", {}).get(key, default)

    def anatomy_root(self):
        """First existing anatomy root across the known clusters.

        Falls back to the first candidate if none exist (so the caller gets a
        meaningful path in the eventual not-found error).
        """
        for candidate in _ANATOMY_ROOTS:
            if Path(candidate).exists():
                return Path(candidate)
        return Path(_ANATOMY_ROOTS[0])
