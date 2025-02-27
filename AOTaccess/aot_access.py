import AOTaccess
from pathlib import Path
import sys
import os
import yaml
import nibabel as nib

from AOTaccess.glmsingle_access import GLMSingleAccess
from AOTaccess.expdesign_access import ExpDesignAccess
from AOTaccess.stimulus_info_access import StimuliInfoAccess
from AOTaccess.bids_access import BidsAccess
from AOTaccess.memoryscore_access import MemoryScoreAccess
from AOTaccess.preproced_access import PreprocedAccess


class AOTAccess:
    def __init__(self, root_path):
        self.basedir = Path(__file__).resolve().parent
        self.settings = yaml.safe_load(open(self.basedir / "settings.yml"))
        self.glmsingle_access = GLMSingleAccess(root_dir=root_path)
        self.expdesign_access = ExpDesignAccess(root_dir=root_path)
        self.stimuli_info_access = StimuliInfoAccess(root_dir=root_path)
        self.bids_access = BidsAccess(root_dir=root_path)
        self.memoryscore_access = MemoryScoreAccess(root_dir=root_path)
        self.preproced_access = PreprocedAccess(root_dir=root_path)

        self.root_path = root_path
        """
        data dir structure:

        Root path
            Fw rv video betas folder
            Glmginle output raw folder
            Preproced folder
            Bids folder
            expdesign folder
            Raw data folder
            video folder
            video annotations folder

        """

    def read_affine_header(sub: int):
        pass

    def read_meanvol_from_session(sub: int, ses: int, resolution: str = "1.7mm"):
        pass

    def read_betas_from_session(
        sub: int,
        ses: int,
        glmtype: str = "TYPED_FITHRF_GLMDENOISE_RR",
        resolution: str = "1.7mm",
    ):
        pass

    def read_betas_from_video(
        sub: int,
        video: int,
        glmtype: str = "TYPED_FITHRF_GLMDENOISE_RR",
        resolution: str = "1.7mm",
    ):
        pass

    def read_R2_from_session(
        sub: int,
        ses: int,
        glmtype: str = "TYPED_FITHRF_GLMDENOISE_RR",
        resolution: str = "1.7mm",
    ):
        pass

    def read_R2_mask_from_session(
        sub: int,
        ses: int,
        threshold: float = 0.2,
        glmtype: str = "TYPED_FITHRF_GLMDENOISE_RR",
        resolution: str = "1.7mm",
    ):
        pass

    def read_video_list_from_session(sub: int, ses: int):
        pass

    def read_session_from_video(sub: int, video: int):
        pass

    def read_preproced_bold_from_session(
        sub: int, ses: int, run: int, resolution: str = "1.7mm"
    ):
        pass
