import AOTaccess
from pathlib import Path
import sys
import os
import yaml

basedir = Path(__file__).resolve().parent
settings = yaml.safe_load(open(basedir / 'settings.yml'))
