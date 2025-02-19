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
    def __init__(self, root_path):
        self.basedir = Path(__file__).resolve().parent
        self.settings = yaml.safe_load(open(self.basedir / "settings.yml"))
        self.glmsingle_access = GLMSingleAccess()
        self.expdesign_access = ExpDesignAccess()
        self.stimuli_info_access = StimuliInfoAccess()

        self.root_path = root_path
        """
        Root
            Fw rv video betas folder
            Glmginle output raw folder
            Preproced folder
            Bids folder
            Raw data folder
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
