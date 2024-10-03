import os
import sys
from pathlib import Path
import yaml
import nibabel as nib


class FmriprepAccess:
    def __init__(self, sub, ses):
        basedir = Path(__file__).resolve().parent
        settings = yaml.safe_load(open(basedir / "settings.yml"))
        self.root_fmriprep_dir = Path(settings["paths"]["fmriprep"])
        self.sub = sub
        self.ses = ses
        self.fmriprep_dir = self.root_fmriprep_dir / f"sub-{sub:03d}/ses-{ses:02d}/func"

    def read_bold_file_T1w(self, run):
        """
        example : sub-001_ses-01_task-AOT_rec-nordicstc_run-1_space-T1w_desc-preproc_part-mag_bold.nii.gz
        """
        bold_file = (
            self.fmriprep_dir
            / f"sub-{self.sub:03d}_ses-{self.ses:02d}_task-AOT_rec-nordicstc_run-{run}_space-T1w_desc-preproc_part-mag_bold.nii.gz"
        )

        bold = nib.load(bold_file)
        print(f"Loaded bold from {bold_file}")
        print(f"Shape of bold: {bold.shape}")
        return bold

    def read_boldref_file_T1w(self, run):
        """
        example : sub-001_ses-01_task-AOT_rec-nordicstc_run-1_space-T1w_part-mag_boldref.nii.gz
        """
        boldref_file = (
            self.fmriprep_dir
            / f"sub-{self.sub:03d}_ses-{self.ses:02d}_task-AOT_rec-nordicstc_run-{run}_space-T1w_part-mag_boldref.nii.gz"
        )

        boldref = nib.load(boldref_file)
        print(f"Loaded boldref from {boldref_file}")
        print(f"Shape of boldref: {boldref.shape}")
        return boldref

    def read_bold_file_fsnative_L(self, run):
        pass

    def read_bold_file_fsnative_R(self, run):
        pass

    def read_bold_file_fsaverage_L(self, run):
        pass

    def read_bold_file_fsaverage_R(self, run):
        pass
