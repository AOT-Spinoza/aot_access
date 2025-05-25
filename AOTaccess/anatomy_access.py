import AOTaccess
from pathlib import Path
import sys
import os
import yaml
import nibabel as nib

class AnatomyAccess:
    def __init__(self, root_dir: Path = None):
        """
        Initialize an AnatomyAccess instance.

        Parameters:
            root_dir (Path): Root directory for anatomy data.
        """
        pass

    def _temp_read_crop_resampled_T1(
        self, sub: int
    ):  # for new data each sunject shouold have a single affine matrix for all sessions
        anat_source_path = Path("/tank/shared/2024/visual/AOT/derivatives/anat-3T")

        anat_path = anat_source_path / f"sub-{sub:03d}" / "fiducial" / "epi_1.7mm" / f"sub-{sub:03d}_ses-3Tanat_T1w_FS_T2BM_crop_resampled.nii.gz"
        anat_img = nib.load(anat_path)
        return anat_img






