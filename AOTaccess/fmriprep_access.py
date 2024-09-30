import os
import sys
from pathlib import Path
import yaml


class FmriprepAccess:
    def __init__(self, sub, ses):
        basedir = Path(__file__).resolve().parent
        settings = yaml.safe_load(open(basedir / "settings.yml"))
        self.root_fmriprep_dir = Path(settings["paths"]["fmriprep"])
        self.sub = sub
        self.ses = ses
        self.fmriprep_dir = self.root_fmriprep_dir / f"sub-{sub:03d}/ses-{ses:02d}/func"

    def get_bold_file_T1w(self, run):
        """
        example : sub-001_ses-01_task-AOT_rec-nordicstc_run-1_space-T1w_desc-preproc_part-mag_bold.nii.gz
        """
        bold_file = (
            self.fmriprep_dir
            / f"sub-{self.sub:03d}_ses-{self.ses:02d}_task-AOT_rec-nordicstc_run-{run}_space-T1w_desc-preproc_part-mag_bold.nii.gz"
        )
        return bold_file

    def get_boldref_file_T1w(self, run):
        """
        example : sub-001_ses-01_task-AOT_rec-nordicstc_run-1_space-T1w_part-mag_boldref.nii.gz
        """
        boldref_file = (
            self.fmriprep_dir
            / f"sub-{self.sub:03d}_ses-{self.ses:02d}_task-AOT_rec-nordicstc_run-{run}_space-T1w_part-mag_boldref.nii.gz"
        )
        return boldref_file

    def get_bold_file_fsnative_L(self, run):
        pass

    def get_bold_file_fsnative_R(self, run):
        pass

    def get_bold_file_fsaverage_L(self, run):
        pass

    def get_bold_file_fsaverage_R(self, run):
        pass
