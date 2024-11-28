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

    def read_memory_csv_cleaned(self, sub: int, ses: int):
        def clean_file_name(file_name):
            # from '/experiments/knapen_aot/AOT/AOT_stimuli/pictures/1973_fw.png to 1973
            return os.path.basename(file_name).split("_")[0]

        def clean_response(response):
            # j to True, k to False
            if response == "j":
                return True
            elif response == "k":
                return False
            else:
                return None

        memory_csv = self.read_memory_csv(sub, ses)
        memory_csv_cleaned = []
        for row in memory_csv:
            original_picture_file = row[""]
            original_response = row["0"]
            video_index = clean_file_name(original_picture_file)
            response = clean_response(original_response)
            memory_csv_cleaned.append(
                {"video_index": video_index, "response": response}
            )

        return memory_csv_cleaned

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

    def memorability_list_from_session(self, sub: int, ses: int):
        expdesignaccess = ExpDesignAccess()

        memory_csv = self.read_memory_csv_cleaned(sub, ses)
