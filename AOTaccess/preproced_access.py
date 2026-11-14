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

    def func_path(
        self,
        sub: int,
        ses: int,
        run: int,
        task: str = "AOT",
        resolution: str = "2p0mm",
    ):
        """Path to one preprocessed functional image (no existence check).

        The filename follows the AOT BIDS naming; ``task`` covers the
        ``task-AOT``, ``task-pRF``, ``task-fLoc`` and ``task-Dur`` scopes.
        """
        # example file: derivatives/aot_prep/sub-001/ses-01/func/sub-001_ses-01_task-AOT_rec-nordicstc_run-01_part-mag_bold_space-T1w_res-2p0mm.nii.gz
        sub_t = fmt_sub(sub)
        ses_t = fmt_ses(ses)
        run_t = fmt_run(run)
        filename = (
            f"sub-{sub_t}_ses-{ses_t}_task-{task}_rec-nordicstc_run-{run_t}"
            f"_part-mag_bold_space-T1w_res-{resolution}.nii.gz"
        )
        return self.root_preproced_dir / f"sub-{sub_t}/ses-{ses_t}/func" / filename

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

        filepath = self.func_path(sub, ses, run, task=task, resolution=resolution)
        if not filepath.exists():
            raise DataNotFoundError(
                f"Preprocessed BOLD not found: {filepath} "
                f"(sub={sub}, ses={ses}, run={run}, resolution={resolution})"
            )
        return nib.load(filepath)
