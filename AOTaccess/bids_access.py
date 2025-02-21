import os
import sys
from pathlib import Path
import csv
import yaml
import bids
import nibabel as nib
import json


class BidsAccess:
    def __init__(self, bids_dir: Path):
        self.bids_dir = bids_dir

    def get_func_dir(self, sub: int, ses: int):
        return self.bids_dir / f"sub-{sub:03d}" / f"ses-{ses:02d}" / "func"

    def read_events_tsv(self, sub: int, ses: int, run: int):
        func_dir = self.get_func_dir(sub, ses)
        filepath = (
            func_dir / f"sub-{sub:03d}_ses-{ses:02d}_task-AOT_run-{run:02d}_events.tsv"
        )
        with open(filepath, "r") as f:
            return list(csv.DictReader(f, delimiter="\t"))

    def read_bold(
        self, sub: int, ses: int, run: int, rec: str = "original", part: str = "mag"
    ):
        """
        Load BOLD data from the BIDS directory.

        Parameters:
            sub (int): Subject number.
            ses (int): Session number.
            run (int): Run number.
            rec (str): Reconstruction type, default "original".
            part (str): Part type, default "mag".

        Returns:
            nibabel.Nifti1Image: BOLD image data.
        """
        func_dir = self.get_func_dir(sub, ses)
        bold_file = (
            func_dir
            / f"sub-{sub:03d}_ses-{ses:02d}_task-AOT_rec-{rec}_run-{run:02d}_part-{part}_bold.nii.gz"
        )
        return nib.load(bold_file)

    def read_sbref(self, sub: int, ses: int, part: str = "mag"):
        """
        Load SBref data from the BIDS directory.

        Parameters:
            sub (int): Subject number.
            ses (int): Session number.
            part (str): Part type, default "mag".

        Returns:
            nibabel.Nifti1Image: SBref image data.
        """
        func_dir = self.get_func_dir(sub, ses)
        sbref_file = func_dir / f"sub-{sub:03d}_ses-{ses:02d}_part-{part}_sbref.nii.gz"
        return nib.load(sbref_file)

    def get_anat_dir(self, sub: int, ses: int):
        return self.bids_dir / f"sub-{sub:03d}" / f"ses-{ses:02d}" / "anat"

    def read_inplane_T2(self, sub: int, ses: int):
        anat_dir = self.get_anat_dir(sub, ses)
        t2_file = anat_dir / f"sub-{sub:03d}_ses-{ses:02d}_acq-GRE_inplaneT2.nii.gz"
        return nib.load(t2_file)

    def get_beh_dir(self, sub: int, ses: int):
        return self.bids_dir / f"sub-{sub:03d}" / f"ses-{ses:02d}" / "beh"

    def read_memory_events(self, sub: int, ses: int, run: int = 1):
        beh_dir = self.get_beh_dir(sub, ses)
        events_file = (
            beh_dir
            / f"sub-{sub:03d}_ses-{ses:02d}_task-memory_run-{run:02d}_events.tsv"
        )
        with open(events_file, "r") as f:
            return list(csv.DictReader(f, delimiter="\t"))

    def get_fmap_dir(self, sub: int, ses: int):
        return self.bids_dir / f"sub-{sub:03d}" / f"ses-{ses:02d}" / "fmap"

    def read_fmap_file(self, sub: int, ses: int, acq: str, dir: str, run: int):
        fmap_dir = self.get_fmap_dir(sub, ses)
        fmap_file = (
            fmap_dir
            / f"sub-{sub:03d}_ses-{ses:02d}_acq-{acq}_dir-{dir}_run-{run:02d}_epi.nii.gz"
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

    def read_output_csv(self, sub: int, ses: int, run: int = 1):
        """
        Reads any .csv file in the behavioral directory, e.g., output files.
        """
        beh_dir = self.get_beh_dir(sub, ses)
        csv_path = (
            beh_dir
            / f"sub-{sub:03d}_ses-{ses:02d}_task-memory_run-{run:02d}_output.csv"
        )
        with open(csv_path, "r") as f:
            return list(csv.DictReader(f))

    def read_phasediff(
        self, sub: int, ses: int, run: int, acq: str = "nordic", part: str = "mag"
    ):
        """
        Load phasediff data from the BIDS directory.
        """
        fmap_dir = self.get_fmap_dir(sub, ses)
        phasediff_file = (
            fmap_dir
            / f"sub-{sub:03d}_ses-{ses:02d}_acq-{acq}_run-{run:02d}_part-{part}_phasediff.nii.gz"
        )
        return nib.load(phasediff_file)
