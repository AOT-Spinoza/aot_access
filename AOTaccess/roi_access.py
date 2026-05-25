"""Manifest-driven access to the AOT ROI derivatives.

Every path is resolved from the ROI library's ``MANIFEST.yaml`` (its
``path_templates`` section) rather than hard-coded here, so this module follows
the ROI toolchain's layout automatically whenever the manifest is regenerated.

The ROI library propagates hand-drawn and published-atlas ROIs into several
spaces. The ``fsnative`` volumetric space is the same voxel grid as the EPI
space used by GLMsingle and aot_prep, so an ``fsnative`` mask at a matching
resolution indexes a betas/BOLD array directly (see ``extract_betas_in_roi``
on ``AOTAccess``).
"""

import yaml
import numpy as np
import nibabel as nib

from AOTaccess.config import Config
from AOTaccess.errors import DataNotFoundError


# User-facing volume-space label -> ROI manifest template-key prefix.
# Following the project convention adopted 2026-05-22: `T1w` is the canonical
# label for the subject-native volume, `MNI` for the standard volume; bare
# `fsnative` and `fsaverage` are reserved for cortical surfaces.
#
# The current ROI manifest still uses the legacy template-key prefixes
# `fsnative_volume_*` and `mni_volume_*`; this map routes the canonical
# user-facing labels to them transitionally. When the aot_rois toolchain
# regenerates the store with BIDS-canonical entity ordering and the new
# template keys (`T1w_volume_*`, `MNI_volume_*`, surfaces under
# `space-fsnative`/`space-fsaverage`), flip this map to identity:
#
#     _VOLUME_SPACE_ALIASES = {"T1w": "T1w", "MNI": "MNI"}
#
# Everything else (defaults, surface methods, _resolve_volume_space) is
# already canonical and needs no further change.
_VOLUME_SPACE_ALIASES = {
    "T1w": "fsnative",
    "MNI": "mni",
    "MNI152NLin2009cAsym": "mni",   # BIDS-canonical alias
    "epi": "fsnative",              # legacy alias, kept transitionally
}

# Spaces accepted by surface methods.
_SURFACE_SPACES = {"fsnative", "fsaverage"}


def _resolve_volume_space(space):
    """Validate a volume-method `space` arg and return its manifest prefix.

    Rejects surface labels (`fsnative`, `fsaverage`) with a clear hint.
    """
    if space in _SURFACE_SPACES:
        raise ValueError(
            f"{space!r} is a surface space; for volumetric ROI masks use "
            f"space='T1w' (subject-native) or space='MNI'. Surface methods "
            f"(read_surface_label) take {space!r}."
        )
    if space not in _VOLUME_SPACE_ALIASES:
        raise ValueError(
            f"Unknown volume space {space!r}. "
            f"Valid: {sorted(_VOLUME_SPACE_ALIASES)}."
        )
    return _VOLUME_SPACE_ALIASES[space]


class ROIAccess:
    def __init__(self, root_dir=None, config=None):
        """Initialize a ROIAccess instance.

        Parameters:
            root_dir: If given, resolve paths relative to this dataset root.
            config (Config): An explicit Config; takes precedence over root_dir.
        """
        self.config = config if config is not None else Config(root_dir=root_dir)
        self.roi_dir = self.config.path("roi")
        self.manifest_path = self.roi_dir / "MANIFEST.yaml"
        self._manifest = None

    # ------------------------------------------------------------------
    # manifest
    # ------------------------------------------------------------------
    @property
    def manifest(self):
        """The parsed MANIFEST.yaml (lazy-loaded and cached)."""
        if self._manifest is None:
            if not self.manifest_path.exists():
                raise DataNotFoundError(
                    f"ROI manifest not found: {self.manifest_path}"
                )
            with open(self.manifest_path) as f:
                self._manifest = yaml.safe_load(f)
        return self._manifest

    # ------------------------------------------------------------------
    # discovery
    # ------------------------------------------------------------------
    def atlases(self):
        """List atlas names, e.g. 'manual', 'wang_2015', 'glasser_2016'."""
        return list(self.manifest["atlases"])

    def atlas_info(self, atlas: str):
        """Return manifest metadata for an atlas (citation, source files, ...)."""
        return self.manifest["atlases"][atlas]

    def spaces(self):
        """List the spaces ROIs are propagated to."""
        return list(self.manifest["spaces"])

    def conservativeness_levels(self):
        """List conservativeness levels, e.g. 'strict', 'balanced', 'liberal'."""
        return list(self.manifest["conservativeness_levels"])

    def resolutions(self, space: str = "T1w"):
        """List available resolutions for a volumetric space ('T1w' / 'MNI')."""
        key = _resolve_volume_space(space)
        return list(self.manifest["resolutions"][key])

    def subjects(self):
        """List subjects present in the ROI library, e.g. 'sub-001'."""
        return list(self.manifest["subjects"])

    def rois(self, subject=None):
        """List ROI names.

        With ``subject`` given, returns the ROIs available for that subject;
        otherwise returns every ROI defined in the library.
        """
        if subject is not None:
            return list(self.manifest["subjects"][self._sub_key(subject)]["rois"])
        return list(self.manifest["rois"])

    def roi_info(self, roi: str):
        """Return manifest metadata for an ROI (full_name, source)."""
        return self.manifest["rois"][roi]

    def missing_rois(self, subject):
        """ROIs the manifest reports as not produced for a subject."""
        entry = self.manifest["subjects"][self._sub_key(subject)]
        return entry.get("missing_rois", {})

    def template_keys(self):
        """List the path-template names defined in the manifest."""
        return list(self.manifest["path_templates"])

    # ------------------------------------------------------------------
    # subject token helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _sub_token(sub):
        """Zero-padded subject token: 1 -> '001', 'sub-001' -> '001'."""
        if isinstance(sub, int):
            return f"{sub:03d}"
        s = str(sub)
        return s[len("sub-"):] if s.startswith("sub-") else s

    def _sub_key(self, sub):
        """Subject key as used in the manifest 'subjects' mapping, 'sub-001'."""
        return f"sub-{self._sub_token(sub)}"

    # ------------------------------------------------------------------
    # generic path resolution
    # ------------------------------------------------------------------
    def resolve(self, template_key: str, **params):
        """Resolve a manifest path template to an absolute Path.

        ``template_key`` is one of :meth:`template_keys`; keyword arguments
        supply the template's ``{...}`` placeholders and are validated against
        the template's declared parameter list. ``sub`` may be an int or a
        'sub-XXX' string and is normalised to the bare token.
        """
        templates = self.manifest["path_templates"]
        if template_key not in templates:
            raise KeyError(
                f"Unknown path template '{template_key}'. "
                f"Available: {sorted(templates)}"
            )
        spec = templates[template_key]
        required = set(spec["parameters"])
        params = dict(params)
        if "sub" in params:
            params["sub"] = self._sub_token(params["sub"])
        missing = required - set(params)
        unexpected = set(params) - required
        if missing or unexpected:
            raise ValueError(
                f"Template '{template_key}' expects parameters {sorted(required)}; "
                f"missing={sorted(missing)}, unexpected={sorted(unexpected)}."
            )
        return self.roi_dir / spec["template"].format(**params)

    # ------------------------------------------------------------------
    # volumetric masks (single ROI)
    # ------------------------------------------------------------------
    def mask_path(self, sub, roi, atlas="wang_2015", space="T1w",
                  res="2p0mm", cons="balanced", hemi=None):
        """Path to a single-ROI binary mask.

        ``hemi`` None resolves the bilateral mask (union of L and R);
        'L'/'R' resolves the per-hemisphere mask. ``space`` is 'fsnative'
        (the EPI grid) or 'mni'.
        """
        sp = _resolve_volume_space(space)
        kind = "per_hemi" if hemi is not None else "bilateral"
        params = dict(sub=sub, atlas=atlas, roi=roi, res=res, cons=cons)
        if hemi is not None:
            params["hemi"] = hemi
        return self.resolve(f"{sp}_volume_mask_{kind}", **params)

    def read_mask(self, sub, roi, atlas="wang_2015", space="T1w",
                  res="2p0mm", cons="balanced", hemi=None):
        """Load a single-ROI mask as a boolean ndarray.

        With ``space='fsnative'`` at a matching resolution the result indexes
        GLMsingle betas / preprocessed BOLD directly (same voxel grid).
        """
        path = self.mask_path(sub, roi, atlas, space, res, cons, hemi)
        if not path.exists():
            raise DataNotFoundError(
                f"ROI mask not found: {path}\n"
                f"(sub={sub}, roi={roi}, atlas={atlas}, space={space}, "
                f"res={res}, cons={cons}, hemi={hemi})"
            )
        return np.asarray(nib.load(path).get_fdata()) > 0

    # ------------------------------------------------------------------
    # volumetric parcellations (all ROIs of an atlas)
    # ------------------------------------------------------------------
    def dseg_path(self, sub, atlas="wang_2015", space="T1w",
                  res="2p0mm", cons="balanced", hemi=None):
        """Path to an atlas discrete segmentation (integer-labelled volume)."""
        sp = _resolve_volume_space(space)
        kind = "per_hemi" if hemi is not None else "bilateral"
        params = dict(sub=sub, atlas=atlas, res=res, cons=cons)
        if hemi is not None:
            params["hemi"] = hemi
        return self.resolve(f"{sp}_volume_dseg_{kind}", **params)

    def read_dseg(self, sub, atlas="wang_2015", space="T1w",
                  res="2p0mm", cons="balanced", hemi=None):
        """Load an atlas discrete segmentation as an integer ndarray."""
        path = self.dseg_path(sub, atlas, space, res, cons, hemi)
        if not path.exists():
            raise DataNotFoundError(f"ROI dseg not found: {path}")
        return np.asarray(nib.load(path).get_fdata()).astype(int)

    # ------------------------------------------------------------------
    # surface labels
    # ------------------------------------------------------------------
    def surface_label_path(self, sub, roi, hemi, atlas="wang_2015",
                           space="fsnative"):
        """Path to a per-ROI surface label (.label.gii).

        ``space`` is 'fsnative' (atlas-specific) or 'fsaverage' (manual ROIs).
        """
        if space == "fsaverage":
            return self.resolve("fsaverage_surface_label",
                                sub=sub, roi=roi, hemi=hemi)
        return self.resolve("fsnative_surface_label",
                            sub=sub, roi=roi, hemi=hemi, atlas=atlas)

    def read_surface_label(self, sub, roi, hemi, atlas="wang_2015",
                           space="fsnative"):
        """Load a per-ROI surface label as a per-vertex ndarray."""
        path = self.surface_label_path(sub, roi, hemi, atlas, space)
        if not path.exists():
            raise DataNotFoundError(f"ROI surface label not found: {path}")
        return nib.load(path).agg_data()

    # ------------------------------------------------------------------
    # group probabilistic maps
    # ------------------------------------------------------------------
    def group_probseg_path(self, roi, hemi, atlas="wang_2015",
                           res="1p25mm", cons="balanced"):
        """Path to a group probabilistic segmentation (MNI) for one ROI."""
        return self.resolve("group_mni_probseg_per_hemi",
                            atlas=atlas, roi=roi, hemi=hemi, res=res, cons=cons)

    def read_group_probseg(self, roi, hemi, atlas="wang_2015",
                           res="1p25mm", cons="balanced"):
        """Load a group probabilistic segmentation (MNI) as a float ndarray."""
        path = self.group_probseg_path(roi, hemi, atlas, res, cons)
        if not path.exists():
            raise DataNotFoundError(f"Group probseg not found: {path}")
        return np.asarray(nib.load(path).get_fdata())
