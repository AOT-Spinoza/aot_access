import AOTaccess
from pathlib import Path
import sys
import os
import yaml


class ExpDesignAccess:
    def __init__(self, sub, ses):
        basedir = Path(__file__).resolve().parent
        settings = yaml.safe_load(open(basedir / "settings.yml"))

        self.sub = sub
        self.ses = ses
