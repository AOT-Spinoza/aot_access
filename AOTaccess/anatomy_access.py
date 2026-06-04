"""Access to per-subject anatomical reference images."""

import nibabel as nib

from AOTaccess.config import Config
from AOTaccess.errors import DataNotFoundError
from AOTaccess.naming import fmt_sub


# FreeSurfer cortex gray-matter mask variants (suffix after `sub-XXX_`).
# All three live under `anat-3T/<sub>/fiducial/res-XpXmm/` and share the
# affine of the corresponding `space-T1w_res-XpXmm` EPI grid.
_GM_VARIANTS = {
    "cortex":     "FScortexGM_T2BM_crop_resampled",      # binary, ~60 k voxels (sub-001 / 2p0mm)
    "cortex_dil": "FScortexGM_dil_T2BM_crop_resampled",  # dilated binary, ~100 k
    "cortex_sm":  "FScortexGM_sm_T2BM_crop_resampled",   # smoothed float in [0, 1], ~160 k nonzero
}


class AnatomyAccess:
    def __init__(self, root_dir=None, config=None):
        """Initialize an AnatomyAccess instance.

        Parameters:
            root_dir: If given, resolve paths relative to this dataset root.
            config (Config): An explicit Config; takes precedence over root_dir.
        """
        self.config = config if config is not None else Config(root_dir=root_dir)

    # ------------------------------------------------------------------
    # FreeSurfer cortex gray-matter mask (T1w, multi-resolution)
    # ------------------------------------------------------------------
    def gray_matter_mask_path(self, sub, resolution="2p0mm", variant="cortex"):
        """Path to a FreeSurfer cortex gray-matter mask on the EPI grid.

        ``variant`` selects the version produced by the anatomy pipeline:

        - ``"cortex"`` — canonical FreeSurfer cortex GM mask, binary;
        - ``"cortex_dil"`` — dilated (broader), binary;
        - ``"cortex_sm"`` — smoothed soft mask, float in [0, 1].

        The mask shares its affine with ``space-T1w_res-{resolution}``
        derivatives (GLMsingle, preprocessed BOLD), so it drops in as a
        voxel selector with no resampling.
        """
        if variant not in _GM_VARIANTS:
            raise ValueError(
                f"Unknown gray-matter mask variant {variant!r}; "
                f"available: {sorted(_GM_VARIANTS)}"
            )
        sub_t = fmt_sub(sub)
        return (
            self.config.anatomy_root()
            / f"sub-{sub_t}"
            / "fiducial"
            / f"res-{resolution}"
            / f"sub-{sub_t}_{_GM_VARIANTS[variant]}.nii.gz"
        )

    def read_gray_matter_mask(self, sub, resolution="2p0mm", variant="cortex"):
        """Read a FreeSurfer cortex gray-matter mask.

        Return type follows the variant:

        - ``"cortex"`` / ``"cortex_dil"`` → 3-D boolean array (the masks
          are binary on disk).
        - ``"cortex_sm"`` → 3-D float array in ``[0, 1]`` (soft mask;
          threshold yourself if you want a boolean — e.g.
          ``read_gray_matter_mask(..., variant="cortex_sm") > 0.5``).

        Parameters:
            sub (int): Subject number.
            resolution (str): EPI grid, e.g. ``"2p0mm"`` or ``"1p25mm"``.
            variant (str): ``"cortex"`` | ``"cortex_dil"`` | ``"cortex_sm"``.
        """
        path = self.gray_matter_mask_path(sub, resolution=resolution, variant=variant)
        if not path.exists():
            raise DataNotFoundError(
                f"Gray-matter mask not found: {path} "
                f"(sub={sub}, resolution={resolution}, variant={variant})"
            )
        arr = nib.load(path).get_fdata()
        if variant in {"cortex", "cortex_dil"}:
            return arr > 0          # binary on disk → bool
        return arr                   # soft mask → float

    # ------------------------------------------------------------------
    # experimental: full T1w volume
    # ------------------------------------------------------------------
    def _temp_read_crop_resampled_T1(self, sub):
        """Read the cropped/resampled T1w image for a subject.

        Each subject has a single anatomy shared across all sessions.
        """
        sub = fmt_sub(sub)
        anat_path = (
            self.config.anatomy_root()
            / f"sub-{sub}"
            / "fiducial"
            / "res-1p7mm"
            / f"sub-{sub}_ses-3Tanat_T1w_FS_T2BM_crop_resampled.nii.gz"
        )
        if not anat_path.exists():
            raise DataNotFoundError(f"Anatomy T1w not found: {anat_path}")
        return nib.load(anat_path)
