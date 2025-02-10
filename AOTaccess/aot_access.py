import AOTaccess
from pathlib import Path
import sys
import os
import yaml
import nibabel as nib

from AOTaccess.glmsingle_access import GLMSingleAccess
from AOTaccess.expdesign_access import ExpDesignAccess
from AOTaccess.stimulus_info_access import StimuliInfoAccess


class AOTAccess:
    def __init__(self):
        self.basedir = Path(__file__).resolve().parent
        self.settings = yaml.safe_load(open(self.basedir / "settings.yml"))
        self.glmsingle_access = GLMSingleAccess()
        self.expdesign_access = ExpDesignAccess()
        self.stimuli_info_access = StimuliInfoAccess()
