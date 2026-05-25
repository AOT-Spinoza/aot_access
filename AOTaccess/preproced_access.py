import nibabel as nib

from AOTaccess.config import Config
from AOTaccess.errors import DataNotFoundError
from AOTaccess.naming import fmt_sub, fmt_ses, fmt_run


class PreprocedAccess:
    def __init__(self, root_dir=None, config=None):
        """Initialize the PreprocedAccess instance.

        Parameters:
            root_dir: If given, resolve paths relative to this dataset root.
            config (Config): An explicit Config; takes precedence over root_dir.
        """
        self.config = config if config is not None else Config(root_dir=root_dir)
        self.root_preproced_dir = self.config.path("preproced")

    def read_func(
        self,
        sub: int,
        ses: int,
        run: int,
        task: str = "AOT",
        resolution: str = "2p0mm",
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

        # example file: derivatives/aot_prep/sub-001/ses-01/func/sub-001_ses-01_task-AOT_rec-nordicstc_run-01_part-mag_bold_space-epi2p0mm.nii.gz
        sub = fmt_sub(sub)
        ses = fmt_ses(ses)
        run = fmt_run(run)

        filename = f"sub-{sub}_ses-{ses}_task-{task}_rec-nordicstc_run-{run}_part-mag_bold_space-epi{resolution}.nii.gz"

        filepath = self.root_preproced_dir / f"sub-{sub}/ses-{ses}/func" / filename

        if not filepath.exists():
            raise DataNotFoundError(
                f"Preprocessed BOLD not found: {filepath} "
                f"(sub={sub}, ses={ses}, run={run}, resolution={resolution})"
            )
        return nib.load(filepath)
