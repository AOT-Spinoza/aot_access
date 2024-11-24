import AOTaccess
from pathlib import Path
import sys
import os
import yaml
import bids
from bids import BIDSLayout


basedir = Path(__file__).resolve().parent
settings = yaml.safe_load(open(basedir / "settings.yml"))


class ExpLogAccess:
    def __init__(self):
        self.bids_dir = Path(settings["paths"]["bids"])

    def get_func_dir(self, sub: int, ses: int):
        # temp : /tank/shared/2024/visual/AOT/bids/aotfull_final/sub-001/ses-01/func
        return self.bids_dir / f"sub-{sub:03d}" / f"ses-{ses:02d}" / "func"
