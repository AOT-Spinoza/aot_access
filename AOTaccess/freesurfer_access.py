"""Access to per-subject FreeSurfer reconstructions.

The reproductions live in ``derivatives/freesurfer_AOT/<sub>`` (``mri/``,
``surf/``, ``label/`` ...). Reconstruction variants keep the same prefix with a
suffix — e.g. ``sub-004_old_problematic`` — so every accessor takes an optional
``variant`` argument.

Paths are built without touching disk (like the other access classes); readers
raise :class:`DataNotFoundError` when the requested file is missing.
"""

import re

import nibabel as nib

from AOTaccess.config import Config
from AOTaccess.errors import DataNotFoundError
from AOTaccess.naming import fmt_sub

_NUMERIC = re.compile(r"^\d+$")
_HEMIS = ("lh", "rh")
_SURF_KINDS = ("pial", "pial.T2", "white", "smoothwm", "inflated", "sphere", "area")


class FreeSurferAccess:
    def __init__(self, root_dir=None, config=None):
        """Initialize the FreeSurferAccess instance.

        Parameters:
            root_dir: If given, resolve paths relative to this dataset root.
            config (Config): An explicit Config; takes precedence over root_dir.
        """
        self.config = config if config is not None else Config(root_dir=root_dir)
        self.root_freesurfer_dir = self.config.path("freesurfer")

    # ------------------------------------------------------------------
    # directory / subject resolution
    # ------------------------------------------------------------------
    def _subject_name(self, sub, variant=None):
        if isinstance(sub, int):
            base = f"sub-{fmt_sub(sub)}"
        else:
            text = str(sub)
            if _NUMERIC.match(text):
                base = f"sub-{fmt_sub(int(text))}"
            elif re.match(r"^sub-\d+$", text):
                base = text
            elif text.startswith("sub-"):
                # full directory name, e.g. sub-004_old_problematic
                base = text
            else:
                raise ValueError(
                    f"Unrecognised subject identifier {sub!r}; expected an int "
                    f"like 4, '4', 'sub-004' or a full directory name 'sub-004_x'"
                )
        if variant:
            base = f"{base}_{str(variant).strip('_')}"
        return base

    def subject_path(self, sub, variant=None):
        """Path to one reconstruction directory (no existence check)."""
        return self.root_freesurfer_dir / self._subject_name(sub, variant=variant)

    def subjects(self):
        """Directory names of every reconstruction that has ``mri/T1.mgz``."""
        if not self.root_freesurfer_dir.is_dir():
            return []
        return sorted(
            entry.name
            for entry in self.root_freesurfer_dir.iterdir()
            if (entry / "mri" / "T1.mgz").is_file()
        )

    def exists(self, sub, variant=None):
        """True when the reconstruction directory exists."""
        return self.subject_path(sub, variant=variant).is_dir()

    # ------------------------------------------------------------------
    # canonical volume paths
    # ------------------------------------------------------------------
    def _mri_path(self, sub, filename, variant=None):
        return self.subject_path(sub, variant=variant) / "mri" / filename

    def t1_mgz_path(self, sub, variant=None):
        """Path to ``mri/T1.mgz``."""
        return self._mri_path(sub, "T1.mgz", variant=variant)

    def t2_mgz_path(self, sub, variant=None):
        """Path to ``mri/T2.mgz`` (may be absent in some reconstructions)."""
        return self._mri_path(sub, "T2.mgz", variant=variant)

    def ribbon_path(self, sub, variant=None):
        """Path to ``mri/ribbon.mgz`` (cortex labels 3 / 42)."""
        return self._mri_path(sub, "ribbon.mgz", variant=variant)

    def brainmask_path(self, sub, variant=None):
        """Path to ``mri/brainmask.mgz``."""
        return self._mri_path(sub, "brainmask.mgz", variant=variant)

    def tentorium_path(self, sub, variant=None):
        """Path to the optional ``mri/tentorium-dura.nii.gz`` overlay."""
        return self._mri_path(sub, "tentorium-dura.nii.gz", variant=variant)

    def sinus_path(self, sub, variant=None):
        """Path to the optional ``mri/T2_brain_sinus.nii.gz`` overlay."""
        return self._mri_path(sub, "T2_brain_sinus.nii.gz", variant=variant)

    # ------------------------------------------------------------------
    # surface paths
    # ------------------------------------------------------------------
    def surf_path(self, sub, hemi, kind, variant=None):
        """Path to ``surf/<hemi>.<kind>`` (e.g. ``surf/lh.pial``)."""
        if hemi not in _HEMIS:
            raise ValueError(f"hemi must be one of {_HEMIS}, got {hemi!r}")
        if kind not in _SURF_KINDS:
            raise ValueError(f"kind must be one of {_SURF_KINDS}, got {kind!r}")
        return self.subject_path(sub, variant=variant) / "surf" / f"{hemi}.{kind}"

    def has_surfaces(self, sub, variant=None):
        """True when both pial and white surfaces exist for both hemispheres."""
        wanted = (
            ("lh", "pial"), ("lh", "white"), ("rh", "pial"), ("rh", "white"),
        )
        return all(
            self.surf_path(sub, h, k, variant=variant).is_file() for h, k in wanted
        )

    # ------------------------------------------------------------------
    # readers
    # ------------------------------------------------------------------
    def read_t1(self, sub, variant=None):
        """Read ``mri/T1.mgz``."""
        return self._read_mgz(self.t1_mgz_path(sub, variant=variant), "T1.mgz", sub)

    def read_ribbon(self, sub, variant=None):
        """Read ``mri/ribbon.mgz``."""
        return self._read_mgz(self.ribbon_path(sub, variant=variant), "ribbon.mgz", sub)

    def read_brainmask(self, sub, variant=None):
        """Read ``mri/brainmask.mgz``."""
        return self._read_mgz(
            self.brainmask_path(sub, variant=variant), "brainmask.mgz", sub
        )

    @staticmethod
    def _read_mgz(path, label, sub):
        if not path.is_file():
            raise DataNotFoundError(f"FreeSurfer {label} not found: {path} (sub={sub})")
        return nib.load(str(path))
