"""Access to per-subject anatomical reference images."""

import nibabel as nib

from AOTaccess.config import Config
from AOTaccess.errors import DataNotFoundError
from AOTaccess.naming import fmt_sub


class AnatomyAccess:
    def __init__(self, root_dir=None, config=None):
        """Initialize an AnatomyAccess instance.

        Parameters:
            root_dir: If given, resolve paths relative to this dataset root.
            config (Config): An explicit Config; takes precedence over root_dir.
        """
        self.config = config if config is not None else Config(root_dir=root_dir)

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
