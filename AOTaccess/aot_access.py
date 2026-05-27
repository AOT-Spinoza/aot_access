from AOTaccess.config import Config
from AOTaccess.glmsingle_access import GLMSingleAccess
from AOTaccess.expdesign_access import ExpDesignAccess
from AOTaccess.stimulus_info_access import StimuliInfoAccess
from AOTaccess.bids_access import BidsAccess
from AOTaccess.memoryscore_access import MemoryScoreAccess
from AOTaccess.preproced_access import PreprocedAccess
from AOTaccess.roi_access import ROIAccess


class AOTAccess:
    """Facade over the per-domain access classes.

    All sub-accessors share one Config, so a single ``root_dir`` (or the
    default settings.yml) configures the whole API.
    """

    def __init__(self, root_path=None, config=None):
        """Initialize the facade.

        Parameters:
            root_path: If given, resolve every store relative to this dataset
                root. Otherwise paths come from settings.yml.
            config (Config): An explicit Config; takes precedence over root_path.
        """
        self.config = config if config is not None else Config(root_dir=root_path)
        self.glmsingle_access = GLMSingleAccess(config=self.config)
        self.expdesign_access = ExpDesignAccess(config=self.config)
        self.stimuli_info_access = StimuliInfoAccess(config=self.config)
        self.bids_access = BidsAccess(config=self.config)
        self.memoryscore_access = MemoryScoreAccess(config=self.config)
        self.preproced_access = PreprocedAccess(config=self.config)
        self.roi_access = ROIAccess(config=self.config)
        self.root_path = root_path

    def subject(self, sub):
        """A per-subject access object (AOTSubject)."""
        # imported here to keep top-level imports light (pandas dependency)
        from AOTaccess.subject import AOTSubject
        return AOTSubject(sub, config=self.config, glmtype="TYPED_FITHRF_GLMDENOISE_RR")

    def read_affine_header(self, sub: int):
        """
        Read affine matrix and header for a subject.
        """
        affine = self.glmsingle_access.read_affine(sub)
        header = self.glmsingle_access.read_header(sub)
        return affine, header

    def read_meanvol_from_session(self, sub: int, ses: int, resolution: str = "2p0mm"):
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
        resolution: str = "2p0mm",
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
        resolution: str = "2p0mm",
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
        resolution: str = "2p0mm",
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
        resolution: str = "2p0mm",
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

    def read_session_from_video(self, sub: int, video: int, direction: str = None):
        """Sessions where a video appears in the subject's main-task design.

        Returns a sorted list of session ids. Delegates to
        :meth:`AOTaccess.subject.AOTSubject.sessions_for_video`.
        """
        return self.subject(sub).sessions_for_video(video, direction=direction)

    def read_preproced_bold_from_session(
        self, sub: int, ses: int, run: int, resolution: str = "2p0mm"
    ):
        """
        Read preprocessed BOLD data for a session.
        """
        return self.preproced_access.read_func(
            sub=sub, ses=ses, run=run, resolution=resolution
        )

    def read_roi_mask(
        self,
        sub: int,
        roi: str,
        atlas: str = "wang_2015",
        resolution: str = "2p0mm",
        cons: str = "balanced",
        hemi: str = None,
    ):
        """
        Read a boolean ROI mask on the EPI grid.

        The mask comes from the ROI library's fsnative volume space, which is
        the same voxel grid as the GLMsingle betas and preprocessed BOLD at the
        matching resolution, so it indexes those arrays directly.
        """
        return self.roi_access.read_mask(
            sub=sub,
            roi=roi,
            atlas=atlas,
            space="T1w",
            res=resolution,
            cons=cons,
            hemi=hemi,
        )

    def extract_betas_in_roi(
        self,
        sub: int,
        ses: int,
        roi: str,
        atlas: str = "wang_2015",
        cons: str = "balanced",
        hemi: str = None,
        glmtype: str = "TYPED_FITHRF_GLMDENOISE_RR",
        resolution: str = "2p0mm",
    ):
        """
        Read per-session GLMsingle betas restricted to an ROI.

        Returns an (n_voxels, n_trials) array: the ROI mask applied to the
        session betas volume. The ROI mask (fsnative volume) and the betas
        share the EPI voxel grid at the same resolution.
        """
        betas = self.glmsingle_access.read_betas(
            sub=sub, ses=ses, glmtype=glmtype, resolution=resolution
        )
        mask = self.read_roi_mask(sub, roi, atlas, resolution, cons, hemi)
        if mask.shape != betas.shape[:3]:
            raise ValueError(
                f"ROI mask shape {mask.shape} does not match the betas grid "
                f"{betas.shape[:3]} — check that resolution='{resolution}' "
                f"matches between the ROI and GLMsingle outputs."
            )
        return betas[mask]
