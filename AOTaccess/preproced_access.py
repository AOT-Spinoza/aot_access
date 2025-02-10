import os
import sys
from pathlib import Path
import yaml
import nibabel as nib


class PreprocedAccess:
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
        self.root_preproced_dir = Path(settings["paths"]["preproced"])

    def read_func(
        self,
        sub: int,
        ses: int,
        run: int,
        task: str = "AOT",
        resolution: str = "1.7mm",
    ):
        """
        Read the preprocessed functional image for a specific subject, session, task, and run.

        Parameters:
            sub (int): Subject number.
            ses (int): Session number.
            task (str): Task name.
            run (int): Run number.

        Returns:
            nibabel.nifti1.Nifti1Image: The preprocessed functional image.
        """

        # temp file : derivatives/aot_prep/sub-001/ses-01/func/sub-001_ses-01_task-AOT_rec-nordicstc_run-01_part-mag_bold_space-epi_1.7mm.nii.gz
        sub = str(sub).zfill(3)
        ses = str(ses).zfill(2)
        run = str(run).zfill(2)

        filename = f"sub-{sub}_ses-{ses}_task-{task}_rec-nordicstc_run-{run}_part-mag_bold_space-epi_{resolution}.nii.gz"

        filepath = self.root_preproced_dir / f"sub-{sub}/ses-{ses}/func" / filename

        return nib.load(filepath)
