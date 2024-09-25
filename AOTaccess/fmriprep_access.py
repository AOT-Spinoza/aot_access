import os
import sys
from pathlib import Path
import yaml


class FmriprepAccess:
    def __init__(self, sub, ses):
        basedir = Path(__file__).resolve().parent
        settings = yaml.safe_load(open(basedir / "settings.yml"))
        fmriprep_dir = Path(settings["paths"]["fmriprep"])
        self.sub = sub
        self.ses = ses
