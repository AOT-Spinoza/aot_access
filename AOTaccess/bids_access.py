import csv
import nibabel as nib
import json

from AOTaccess.config import Config
from AOTaccess.naming import fmt_sub, fmt_ses, fmt_run


class BidsAccess:
    def __init__(self, root_dir=None, config=None):
        """Initialize a BidsAccess instance.

        Parameters:
            root_dir: If given, resolve paths relative to this dataset root.
            config (Config): An explicit Config; takes precedence over root_dir.
        """
        self.config = config if config is not None else Config(root_dir=root_dir)
        self.bids_dir = self.config.path("bids")

    def _session_dir(self, sub, ses, modality):
        return (
            self.bids_dir
            / f"sub-{fmt_sub(sub)}"
            / f"ses-{fmt_ses(ses)}"
            / modality
        )

    def get_func_dir(self, sub, ses):
        return self._session_dir(sub, ses, "func")

    def read_events_tsv(self, sub, ses, run: int):
        filepath = self.get_func_dir(sub, ses) / (
            f"sub-{fmt_sub(sub)}_ses-{fmt_ses(ses)}"
            f"_task-AOT_run-{fmt_run(run)}_events.tsv"
        )
        with open(filepath, "r") as f:
            return list(csv.DictReader(f, delimiter="\t"))

    def read_bold(
        self, sub, ses, run: int, rec: str = "original", part: str = "mag"
    ):
        """
        Load BOLD data from the BIDS directory.

        Parameters:
            sub (int | str): Subject number.
            ses (int | str): Session number.
            run (int): Run number.
            rec (str): Reconstruction type, default "original".
            part (str): Part type, default "mag".

        Returns:
            nibabel.Nifti1Image: BOLD image data.
        """
        bold_file = self.get_func_dir(sub, ses) / (
            f"sub-{fmt_sub(sub)}_ses-{fmt_ses(ses)}_task-AOT_rec-{rec}"
            f"_run-{fmt_run(run)}_part-{part}_bold.nii.gz"
        )
        return nib.load(bold_file)

    def read_sbref(self, sub, ses, part: str = "mag"):
        """
        Load SBref data from the BIDS directory.

        Parameters:
            sub (int | str): Subject number.
            ses (int | str): Session number.
            part (str): Part type, default "mag".

        Returns:
            nibabel.Nifti1Image: SBref image data.
        """
        sbref_file = self.get_func_dir(sub, ses) / (
            f"sub-{fmt_sub(sub)}_ses-{fmt_ses(ses)}_part-{part}_sbref.nii.gz"
        )
        return nib.load(sbref_file)

    def get_anat_dir(self, sub, ses):
        return self._session_dir(sub, ses, "anat")

    def read_inplane_T2(self, sub, ses):
        t2_file = self.get_anat_dir(sub, ses) / (
            f"sub-{fmt_sub(sub)}_ses-{fmt_ses(ses)}_acq-GRE_inplaneT2.nii.gz"
        )
        return nib.load(t2_file)

    def get_beh_dir(self, sub, ses):
        return self._session_dir(sub, ses, "beh")

    def read_memory_events(self, sub, ses, run: int = 1):
        events_file = self.get_beh_dir(sub, ses) / (
            f"sub-{fmt_sub(sub)}_ses-{fmt_ses(ses)}"
            f"_task-memory_run-{fmt_run(run)}_events.tsv"
        )
        with open(events_file, "r") as f:
            return list(csv.DictReader(f, delimiter="\t"))

    def get_fmap_dir(self, sub, ses):
        return self._session_dir(sub, ses, "fmap")

    def read_fmap_file(self, sub, ses, acq: str, dir: str, run: int):
        fmap_file = self.get_fmap_dir(sub, ses) / (
            f"sub-{fmt_sub(sub)}_ses-{fmt_ses(ses)}_acq-{acq}"
            f"_dir-{dir}_run-{fmt_run(run)}_epi.nii.gz"
        )
        return nib.load(fmap_file)

    def read_global_json(self, filename: str):
        """
        Reads a JSON file from the top-level BIDS directory.
        """
        file_path = self.bids_dir / filename
        with open(file_path, "r") as f:
            return json.load(f)

    def read_acq_json(self, acq: str, echo: int = 1):
        """
        Reads JSON for T2starw or MP2RAGE acquisitions at the root level.
        """
        file_path = self.bids_dir / f"acq-{acq}_echo-{echo}_T2starw.json"
        if not file_path.exists():
            file_path = self.bids_dir / f"acq-{acq}_inv-{echo}_UNIT1.json"
        with open(file_path, "r") as f:
            return json.load(f)

    def read_output_csv(self, sub, ses, run: int):
        """
        Reads any .csv file in the behavioral directory, e.g., output files.
        """
        csv_path = self.get_beh_dir(sub, ses) / (
            f"sub-{fmt_sub(sub)}_ses-{fmt_ses(ses)}"
            f"_task-memory_run-{fmt_run(run)}_output.csv"
        )
        with open(csv_path, "r") as f:
            return list(csv.DictReader(f))

    def read_phasediff(
        self, sub, ses, run: int, acq: str = "nordic", part: str = "mag"
    ):
        """
        Load phasediff data from the BIDS directory.
        """
        phasediff_file = self.get_fmap_dir(sub, ses) / (
            f"sub-{fmt_sub(sub)}_ses-{fmt_ses(ses)}_acq-{acq}"
            f"_run-{fmt_run(run)}_part-{part}_phasediff.nii.gz"
        )
        return nib.load(phasediff_file)
