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

    def read_affine_header(self, sub: int):
        """
        Read affine matrix and header for a subject.
        """
        affine = self.glmsingle_access.read_affine(sub)
        header = self.glmsingle_access.read_header(sub)
        return affine, header

    def read_meanvol_from_session(self, sub: int, ses: int, resolution: str = "1.7mm"):
        """
        Read mean volume data for a session.
        """
        return self.glmsingle_access.read_meanvol(
            sub=sub, ses=ses, resolution=resolution
        )

    def read_betas_from_session(
        self,
        sub: int,
        ses: int,
        glmtype: str = "TYPED_FITHRF_GLMDENOISE_RR",
        resolution: str = "1.7mm",
    ):
        """
        Read beta values for a session.
        """
        return self.glmsingle_access.read_betas(
            sub=sub, ses=ses, glmtype=glmtype, resolution=resolution
        )

    def read_betas_from_video(
        self,
        sub: int,
        video: int,
        direction: str = "fw",
        glmtype: str = "TYPED_FITHRF_GLMDENOISE_RR",
        resolution: str = "1.7mm",
    ):
        """
        Read beta values for a specific video.
        """
        return self.glmsingle_access.read_video_betas(
            sub=sub,
            video_num=video,
            direction=direction,
            glmtype=glmtype,
            resolution=resolution,
        )

    def read_R2_from_session(
        self,
        sub: int,
        ses: int,
        glmtype: str = "TYPED_FITHRF_GLMDENOISE_RR",
        resolution: str = "1.7mm",
    ):
        """
        Read R2 values for a session.
        """
        return self.glmsingle_access.read_R2(
            sub=sub, ses=ses, glmtype=glmtype, resolution=resolution
        )

    def read_R2_mask_from_session(
        self,
        sub: int,
        ses: int,
        threshold: float = 0.2,
        glmtype: str = "TYPED_FITHRF_GLMDENOISE_RR",
        resolution: str = "1.7mm",
    ):
        """
        Read R2 mask for a session with given threshold.
        """
        return self.glmsingle_access.read_R2_mask(
            sub=sub,
            ses=ses,
            glmtype=glmtype,
            resolution=resolution,
            threshold=threshold,
        )

    def read_video_list_from_session(self, sub: int, ses: int):
        """
        Get list of videos for a session.
        """
        return self.expdesign_access.get_session_uniqe_video_indexes(sub, ses)

    def read_session_from_video(self, sub: int, video: int):
        """
        Get session number for a given video.
        """
        return self.expdesign_access.get_session_id_from_video_id(sub, video)

    def read_preproced_bold_from_session(
        self, sub: int, ses: int, run: int, resolution: str = "1.7mm"
    ):
        """
        Read preprocessed BOLD data for a session.
        """
        return self.preproced_access.read_func(
            sub=sub, ses=ses, run=run, resolution=resolution
        )
