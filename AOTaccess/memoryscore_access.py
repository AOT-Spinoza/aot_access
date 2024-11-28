import AOTaccess
from pathlib import Path
import sys
import os
import yaml
import bids
import csv
from AOTaccess.expdesign_access import ExpDesignAccess


basedir = Path(__file__).resolve().parent
settings = yaml.safe_load(open(basedir / "settings.yml"))


class MemoryScoreAccess:
    def __init__(self):
        self.bids_dir = Path(settings["paths"]["bids"])
        pass

    def get_memory_dir(self, sub: int, ses: int):
        pass

    def read_memory_csv(self, sub: int, ses: int):
        memory_dir = self.get_memory_dir(sub, ses)
        sub = str(sub).zfill(3)
        ses = str(ses).zfill(2)
        run = str(1).zfill(2)
        filename = f"sub-{sub}_ses-{ses}_task-memory_run-{run}_output.csv"
        filepath = memory_dir / filename
        with open(filepath, "r") as f:
            return list(csv.DictReader(f))

    def read_memory_events_tsv(self, sub: int, ses: int):
        memory_dir = self.get_memory_dir(sub, ses)
        sub = str(sub).zfill(3)
        ses = str(ses).zfill(2)
        run = str(1).zfill(2)
        filename = f"sub-{sub}_ses-{ses}_task-memory_run-{run}_events.tsv"
        filepath = memory_dir / filename
        with open(filepath, "r") as f:
            return list(csv.DictReader(f, delimiter="\t"))

    def read_memory_edf(
        self, sub: int, ses: int
    ):  ###############################################################################
        memory_dir = self.get_memory_dir(sub, ses)
        sub = str(sub).zfill(3)
        ses = str(ses).zfill(2)
        run = str(1).zfill(2)
        filename = f"sub-{sub}_ses-{ses}_task-memory_run-{run}_eyetrack.edf"
        filepath = memory_dir / filename
        pass
