import AOTaccess
from pathlib import Path
import sys
import os
import yaml


class ExpDesignAccess:
    def __init__(self):
        basedir = Path(__file__).resolve().parent
        settings = yaml.safe_load(open(basedir / "settings.yml"))
        self.root_expdesign_dir = Path(settings["paths"]["AOTdesignsettings"])
        self.run_number = settings["parameters"]["run_number"]

    def read_expdesign_file(self, sub: int, ses: int, run: int):
        """
        example : /tank/zhangs/AOT_code_repos/arrow_of_time_experiment/aot/data/experiment/settings/main/experiment_settings_sub_01_ses_01_run_01.yml
        """
        expdesign_file = (
            self.root_expdesign_dir
            / f"experiment_settings_sub_{sub:02d}_ses_{ses:02d}_run_{run:02d}.yml"
        )

        expdesign = yaml.safe_load(open(expdesign_file))
        print(f"Loaded expdesign from {expdesign_file}")
        return expdesign

    def append_all_trails_without_blanks(self, sub: int, ses: int):
        """ """
        session_trails_without_blanks = []
        for run in range(1, self.run_number + 1):
            expdesign = self.read_expdesign_file(sub, ses, run)
            trials = expdesign["stimuli"]["movie_files"]
            trails_without_blanks = [trial for trial in trials if trial != "blank"]
            session_trails_without_blanks.extend(trails_without_blanks)
        print(
            f"Appended all trails without blanks, length: {len(session_trails_without_blanks)}"
        )

        return session_trails_without_blanks
