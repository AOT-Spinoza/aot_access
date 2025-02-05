import os
import sys
from pathlib import Path
import yaml
import nibabel as nib


class FmriprepAccess:
    def __init__(self):
        """
        Initialize the FmriprepAccess instance.

        Loads the root fmriprep directory from the settings.

        Parameters:
            None

        Returns:
            None
        """
        basedir = Path(__file__).resolve().parent
        settings = yaml.safe_load(open(basedir / "settings.yml"))
        self.root_fmriprep_dir = Path(settings["paths"]["fmriprep"])

    def read_bold_file_T1w(self, sub, ses, run):
        """
        Load and return the preprocessed BOLD image in T1w space for a specific subject, session, and run.

        Parameters:
            sub (int): Subject number.
            ses (int): Session number.
            run (int): Run number.

        Returns:
            nibabel.Nifti1Image: Loaded BOLD image.
        """
        bold_file = (
            self.root_fmriprep_dir
            / f"sub-{sub:03d}"
            / f"ses-{ses:02d}"
            / "func"
            / f"sub-{sub:03d}_ses-{ses:02d}_task-AOT_rec-nordicstc_run-{run}_space-T1w_desc-preproc_part-mag_bold.nii.gz"
        )

        bold = nib.load(bold_file)
        print(f"Loaded bold from {bold_file}")
        print(f"Shape of bold: {bold.shape}")
        return bold

    def read_boldref_file_T1w(self, sub, ses, run):
        """
        Load and return the BOLD reference image in T1w space for a specific subject, session, and run.

        Parameters:
            sub (int): Subject number.
            ses (int): Session number.
            run (int): Run number.

        Returns:
            nibabel.Nifti1Image: Loaded BOLD reference image.
        """
        boldref_file = (
            self.root_fmriprep_dir
            / f"sub-{sub:03d}"
            / f"ses-{ses:02d}"
            / "func"
            / f"sub-{sub:03d}_ses-{ses:02d}_task-AOT_rec-nordicstc_run-{run}_space-T1w_part-mag_boldref.nii.gz"
        )

        boldref = nib.load(boldref_file)
        print(f"Loaded boldref from {boldref_file}")
        print(f"Shape of boldref: {boldref.shape}")
        return boldref

    def read_brain_mask_file_T1w(self, sub, ses):
        """
        Load and return the brain mask in T1w space for a specific subject and session.

        Parameters:
            sub (int): Subject number.
            ses (int): Session number.

        Returns:
            numpy.ndarray: Boolean array representing the brain mask.
        """
        brain_mask_file = (
            self.root_fmriprep_dir
            / f"sub-{sub:03d}"
            / f"ses-{ses:02d}"
            / "func"
            / f"sub-{sub:03d}_ses-{ses:02d}_task-AOT_rec-nordicstc_run-1_space-T1w_desc-brain_part-mag_mask.nii.gz"
        )

        brain_mask = nib.load(brain_mask_file).get_fdata().astype(bool)
        print(f"Loaded brain mask from {brain_mask_file}")
        print(f"Shape of brain mask: {brain_mask.shape}")
        return brain_mask
