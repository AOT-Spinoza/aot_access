import AOTaccess
from pathlib import Path
import sys
import os
import yaml
import bids
import csv


basedir = Path(__file__).resolve().parent
settings = yaml.safe_load(open(basedir / "settings.yml"))


class ExpLogAccess:
    def __init__(self):
        self.bids_dir = Path(settings["paths"]["bids"])

    def get_func_dir(self, sub: int, ses: int):
        # temp : /tank/shared/2024/visual/AOT/bids/aotfull_final/sub-001/ses-01/func
        return self.bids_dir / f"sub-{sub:03d}" / f"ses-{ses:02d}" / "func"

    def read_events_tsv(self, sub: int, ses: int, run: int):
        # temp : /tank/shared/2024/visual/AOT/bids/aotfull_final/sub-001/ses-01/func/sub-001_ses-01_task-AOT_run-01_events.tsv
        func_dir = self.get_func_dir(sub, ses)
        filepath = (
            func_dir / f"sub-{sub:03d}_ses-{ses:02d}_task-AOT_run-{run:02d}_events.tsv"
        )
        with open(filepath, "r") as f:
            return list(csv.DictReader(f, delimiter="\t"))

    def read_eyetrack_edf(self, sub: int, ses: int, run: int):
        # temp : /tank/shared/2024/visual/AOT/bids/aotfull_final/sub-001/ses-01/func/sub-001_ses-01_task-AOT_run-01_eyetrack.edf
        func_dir = self.get_func_dir(sub, ses)
        filepath = (
            func_dir
            / f"sub-{sub:03d}_ses-{ses:02d}_task-AOT_run-{run:02d}_eyetrack.edf"
        )
        pass  #################

    def get_frames_pdf(self, sub: int, ses: int, run: int):
        # temp : /tank/shared/2024/visual/AOT/bids/aotfull_final/sub-001/ses-01/func/sub-001_ses-01_task-AOT_run-01_frames.pdf
        func_dir = self.get_func_dir(sub, ses)
        filepath = (
            func_dir / f"sub-{sub:03d}_ses-{ses:02d}_task-AOT_run-{run:02d}_frames.pdf"
        )
        return filepath

    def read_lot_txt(self, sub: int, ses: int, run: int):
        # temp : /tank/shared/2024/visual/AOT/bids/aotfull_final/sub-001/ses-01/func/sub-001_ses-01_task-AOT_run-01_log.txt
        func_dir = self.get_func_dir(sub, ses)
        filepath = (
            func_dir / f"sub-{sub:03d}_ses-{ses:02d}_task-AOT_run-{run:02d}_log.txt"
        )
        with open(filepath, "r") as f:
            return f.read()

    def read_scanphyslog_log(self, sub: int, ses: int, run: int):
        # temp : /tank/shared/2024/visual/AOT/bids/aotfull_final/sub-001/ses-01/func/sub-001_ses-01_task-AOT_run-01_scanphyslog.log
        func_dir = self.get_func_dir(sub, ses)
        filepath = (
            func_dir
            / f"sub-{sub:03d}_ses-{ses:02d}_task-AOT_run-{run:02d}_scanphyslog.log"
        )
        with open(filepath, "r") as f:
            return f.read()
