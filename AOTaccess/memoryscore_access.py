import AOTaccess
from pathlib import Path
import sys
import os
import yaml
import bids
import csv


basedir = Path(__file__).resolve().parent
settings = yaml.safe_load(open(basedir / "settings.yml"))


class MemoryScoreAccess:
    def __init__(self):
        # self.bids_dir = Path(settings["paths"]["bids"])
        pass
