import AOTaccess
from pathlib import Path
import sys
import os
import yaml
import nibabel as nib


def _resolve_anatomy_root():
    candidates = [
        Path("/projects/prjs1914/derivatives/anat-3T"),
        Path("/research/FGB-CognitivePsychology-Knapen/shared/2024/visual/AOT/derivatives/anat-3T"),
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return candidates[0]


MODEL_ENTITY_MAP = {
    "TYPEA_ONOFF": "TYPEA",
    "TYPEB_FITHRF": "TYPEB",
    "TYPEC_FITHRF_GLMDENOISE": "TYPEC",
    "TYPED_FITHRF_GLMDENOISE_RR": "TYPED",
}

def build_per_session_bids_nii(sub, ses, resolution, model, desc):
    model_entity = MODEL_ENTITY_MAP.get(model, model)
    return f"sub-{sub:03d}_ses-{ses:02d}_space-T1w_res-{resolution}_model-{model_entity}_desc-{desc}.nii.gz"


def build_per_video_bids_nii(sub, resolution, model, video_num, zscore=True):
    model_entity = MODEL_ENTITY_MAP.get(model, model)
    suffix = "betaszscore" if zscore else "betas"
    return f"sub-{sub:03d}_space-T1w_res-{resolution}_model-{model_entity}_desc-{video_num:04d}{suffix}.nii.gz"


def build_figure_bids_png(sub, ses, resolution, desc):
    return f"sub-{sub:03d}_ses-{ses:02d}_res-{resolution}_desc-{desc}.png"


class GLMSingleAccess:
    def __init__(self, stctype="nordicstc", root_dir: Path = None):
        """
        Initialize a GLMSingleAccess instance.

        Parameters:
            stctype (str): Structure type, default is "nordicstc".

        Returns:
            None
        """
        if root_dir is not None:
            self.glmsingle_main_dir = root_dir / "per_session"
            self.video_betas_dir = root_dir / "per_video"
        else:
            basedir = Path(__file__).resolve().parent
            settings = yaml.safe_load(open(basedir / "settings.yml"))
            self.glmsingle_main_dir = (
                Path(settings["paths"]["glmsingle"]) / "per_session"
            )

            self.video_betas_dir = Path(settings["paths"]["glmsingle"]) / "per_video"
        self.stctype = stctype

    def get_glm_dir_path(self):
        """
        Get the path to the main glmsingle directory.

        Parameters:
            None

        Returns:
            pathlib.Path: The path to glmsingle_main_dir.
        """
        return self.glmsingle_main_dir

    def get_nii_dir_path(
        self,
        sub: int,
        ses: int,
        glmtype: str = None,
        resolution: str = "2p0mm",
    ):
        """
        Get the nii directory path for a given subject, session and resolution.

        Parameters:
            sub (int): Subject number.
            ses (int): Session number.
            glmtype (str): GLM type (kept for backward compat, unused in path).
            resolution (str): Resolution, default is "2p0mm".

        Returns:
            pathlib.Path: Directory path where BIDS-named nifti files are located.
        """
        glm_type_dir = (
            self.glmsingle_main_dir
            / f"sub-{sub:03d}"
            / f"ses-{ses:02d}"
            / f"space-T1w_res-{resolution}"
        )
        return glm_type_dir

    def read_shape(
        self,
        sub: int,
        ses: int,
        glmtype: str = "TYPED_FITHRF_GLMDENOISE_RR",
        resolution: str = "2p0mm",
    ):
        """
        Get the shape of the betas data.

        Parameters:
            sub (int): Subject number.
            ses (int): Session number.
            glmtype (str): GLM type.

        Returns:
            tuple: The shape of the betas data.
        """
        R2_file = self.get_R2_path(sub, ses, glmtype, resolution)
        R2 = self.read_R2(sub, ses, glmtype, resolution)
        if R2 is None:
            nii_dir = self.get_nii_dir_path(sub, ses, resolution=resolution)
            raise FileNotFoundError(
                "Missing GLMsingle R2 file; cannot infer session volume shape. "
                f"Expected: {R2_file}. "
                f"Directory: {nii_dir}. "
                "Check that this subject/session was processed, and that 'glmtype' and 'resolution' match the output."
            )
        return R2.shape
    
    def get_session_betas_path(
        self,
        sub: int,
        ses: int,
        glmtype: str = "TYPED_FITHRF_GLMDENOISE_RR",
        resolution: str = "2p0mm",
        zscore: bool = False,
    ):
        """
        Get the path to the betas file for a given subject and session.

        Parameters:
            sub (int): Subject number.
            ses (int): Session number.
            glmtype (str): GLM type.
            resolution (str): Resolution, default is "2p0mm".

        Returns:
            pathlib.Path: Path to the betas file.
        """
        nii_dir = self.get_nii_dir_path(sub, ses, resolution=resolution)
        desc = "betasmdzscore" if zscore else "betasmd"
        betas_file = nii_dir / build_per_session_bids_nii(sub, ses, resolution, glmtype, desc)
        return betas_file

    def read_betas(  # by session
        self,
        sub: int,
        ses: int,
        glmtype: str = "TYPED_FITHRF_GLMDENOISE_RR",
        resolution: str = "2p0mm",
        zscore: bool = False,
    ):
        """
        Load and return the betas data for a given subject and session.

        Parameters:
            sub (int): Subject number.
            ses (int): Session number.
            glmtype (str): GLM type.

        Returns:
            numpy.ndarray: Array containing the loaded betas data.
        """
        betas_file = self.get_session_betas_path(sub, ses, glmtype, resolution, zscore)
        if not os.path.exists(betas_file):
            # print(f"File {betas_file} does not exist")
            return None
        else:
            betas = nib.load(betas_file).get_fdata()
            # print(f"Loaded betas from {betas_file}")
            # print(f"Shape of betas: {betas.shape}")
            return betas

    def read_affine(
        self, sub: int
    ):  # for new data each sunject shouold have a single affine matrix for all sessions
        affine_source_path = _resolve_anatomy_root()
        affine_matrix_path = (
            affine_source_path
            / f"sub-{sub:03d}"
            / "fiducial"
            / "res-2p0mm"
            / f"sub-{sub:03d}_ses-3Tanat_T1w_FS_T2BM_crop_resampled.nii.gz"
        )

        # print("affine matrix source path:", affine_matrix_path)
        affine_matrix = nib.load(affine_matrix_path).affine
        return affine_matrix

    def read_header(
        self, sub: int
    ):  # for new data each sunject shouold have a single affine matrix for all sessions
        affine_source_path = _resolve_anatomy_root()
        affine_matrix_path = (
            affine_source_path
            / f"sub-{sub:03d}"
            / "fiducial"
            / "res-2p0mm"
            / f"sub-{sub:03d}_ses-3Tanat_T1w_FS_T2BM_crop_resampled.nii.gz"
        )

        # print("affine matrix source path:", affine_matrix_path)
        header = nib.load(affine_matrix_path).header
        return header

    def get_meanvol_path(
        self,
        sub: int,
        ses: int,
        glmtype: str = "TYPED_FITHRF_GLMDENOISE_RR",
        resolution: str = "2p0mm",
    ):
        """
        Get the path to the mean volume file for a given subject and session.

        Parameters:
            sub (int): Subject number.
            ses (int): Session number.
            glmtype (str): GLM type.

        Returns:
            pathlib.Path: Path to the mean volume file.
        """
        nii_dir = self.get_nii_dir_path(sub, ses, resolution=resolution)
        meanvol_file = nii_dir / build_per_session_bids_nii(sub, ses, resolution, glmtype, "meanvol")
        return meanvol_file

    def read_meanvol(
        self,
        sub: int,
        ses: int,
        glmtype: str = "TYPED_FITHRF_GLMDENOISE_RR",
        resolution: str = "2p0mm",
    ):
        """
        Load and return the mean volume data for a given subject and session.

        Parameters:
            sub (int): Subject number.
            ses (int): Session number.
            glmtype (str): GLM type.

        Returns:
            numpy.ndarray: Array containing the loaded mean volume data.
        """

        meanvol_file = self.get_meanvol_path(sub, ses, glmtype, resolution)
        if not os.path.exists(meanvol_file):
            # print(f"File {meanvol_file} does not exist")
            return None
        else:
            meanvol = nib.load(meanvol_file).get_fdata()
            # print(f"Loaded meanvol from {meanvol_file}")
            # print(f"Shape of meanvol: {meanvol.shape}")
            return meanvol
        
    def get_R2_path(
        self,
        sub: int,
        ses: int,
        glmtype: str = "TYPED_FITHRF_GLMDENOISE_RR",
        resolution: str = "2p0mm",
    ):
        """
        Get the path to the R2 file for a given subject and session.

        Parameters:
            sub (int): Subject number.
            ses (int): Session number.
            glmtype (str): GLM type, default is "TYPED_FITHRF_GLMDENOISE_RR".

        Returns:
            pathlib.Path: Path to the R2 file.
        """
        nii_dir = self.get_nii_dir_path(sub, ses, resolution=resolution)
        R2_file = nii_dir / build_per_session_bids_nii(sub, ses, resolution, glmtype, "R2")
        return R2_file

    def read_R2(
        self,
        sub: int,
        ses: int,
        glmtype: str = "TYPED_FITHRF_GLMDENOISE_RR",
        resolution: str = "2p0mm",
    ):
        """
        Load and return the R2 data for a given subject and session.

        Parameters:
            sub (int): Subject number.
            ses (int): Session number.
            glmtype (str): GLM type.

        Returns:
            numpy.ndarray: Array containing the loaded R2 data.
        """
        R2_file = self.get_R2_path(sub, ses, glmtype, resolution)
        if not os.path.exists(R2_file):
            # print(f"File {R2_file} does not exist")
            return None
        else:
            R2 = nib.load(R2_file).get_fdata()
            # print(f"Loaded R2 from {R2_file}")
            # print(f"Shape of R2: {R2.shape}")
            return R2
        
    def get_noiseceiling_path(
        self,
        sub: int,
        ses: int,
        glmtype: str = "TYPED_FITHRF_GLMDENOISE_RR",
        resolution: str = "2p0mm",
        direction: str = "fw",
    ):
        """
        Get the path to the noise ceiling file for a given subject and session.

        Parameters:
            sub (int): Subject number.
            ses (int): Session number.
            glmtype (str): GLM type, default is "TYPED_FITHRF_GLMDENOISE_RR".
            direction (str): Video direction, default is "fw".

        Returns:
            pathlib.Path: Path to the noise ceiling file.
        """
        nii_dir = self.get_nii_dir_path(sub, ses, resolution=resolution)
        nc_file = nii_dir / build_per_session_bids_nii(sub, ses, resolution, glmtype, f"noiseceiling_dir-{direction}")
        return nc_file
    
    def read_noiseceiling(
        self,
        sub: int,
        ses: int,
        glmtype: str = "TYPED_FITHRF_GLMDENOISE_RR",
        resolution: str = "2p0mm",
        direction: str = "fw",
    ):
        """
        Load and return the noise ceiling data for a given subject and session.

        Parameters:
            sub (int): Subject number.
            ses (int): Session number.
            glmtype (str): GLM type.
            direction (str): Video direction, default is "fw".

        Returns:
            numpy.ndarray: Array containing the loaded noise ceiling data.
        """
        nc_file = self.get_noiseceiling_path(sub, ses, glmtype, resolution, direction)
        if not os.path.exists(nc_file):
            # print(f"File {nc_file} does not exist")
            return None
        else:
            nc = nib.load(nc_file).get_fdata()
            # print(f"Loaded noise ceiling from {nc_file}")
            # print(f"Shape of noise ceiling: {nc.shape}")
            return nc

    def read_R2_mask(
        self,
        sub: int,
        ses: int,
        glmtype: str = "TYPED_FITHRF_GLMDENOISE_RR",
        resolution: str = "2p0mm",
        threshold: float = 0.2,
    ):
        """
        Get a boolean mask of R2 data values that exceed the specified threshold.

        Parameters:
            sub (int): Subject number.
            ses (int): Session number.
            glmtype (str): GLM type.
            threshold (float): Threshold value, default is 0.2.

        Returns:
            numpy.ndarray (bool): Boolean array mask for the R2 data.
        """
        R2_file = self.get_R2_path(sub, ses, glmtype, resolution)
        R2 = self.read_R2(sub, ses, glmtype, resolution)
        if R2 is None:
            nii_dir = self.get_nii_dir_path(sub, ses, resolution=resolution)
            raise FileNotFoundError(
                "Missing GLMsingle R2 file; cannot compute R2 mask. "
                f"Expected: {R2_file}. "
                f"Directory: {nii_dir}."
            )
        R2_mask = R2 > threshold
        R2_mask = R2_mask.astype(bool)
        return R2_mask
    
    def get_video_betas_path(
        self,
        sub: int,
        video_num: int,
        direction: str = "fw",
        glmtype: str = "TYPED_FITHRF_GLMDENOISE_RR",
        resolution: str = "2p0mm",
        zscore: bool = False,
    ):
        """
        Get the path to the betas file for a specific video.

        Parameters:
            sub (int): Subject number.
            video_num (int): Video number.
            direction (str): Video direction, default is "fw".
            glmtype (str): GLM type.
            resolution (str): Resolution, default is "2p0mm".

        Returns:
            pathlib.Path: Path to the betas file for the specified video.
        """
        beta_dir = (
            self.video_betas_dir
            / f"sub-{sub:03d}"
            / f"space-T1w_res-{resolution}"
            / direction
        )
        beta_file = beta_dir / build_per_video_bids_nii(sub, resolution, glmtype, video_num, zscore)
        return beta_file

    def read_video_betas(
        self,
        sub: int,
        video_num: int,
        direction: str = "fw",
        glmtype: str = "TYPED_FITHRF_GLMDENOISE_RR",
        resolution: str = "2p0mm",
        zscore: bool = False,
        average_repeat: bool = False,
    ):
        """
        Load and return the betas data for a specific video.

        Parameters:
            sub (int): Subject number.
            video_num (int): Video number.
            direction (str): Video direction, default is "fw".
            glmtype (str): GLM type.
            resolution (str): Resolution, default is "2p0mm".

        Returns:
            numpy.ndarray or None: Array containing the video betas data, or None if the file does not exist.
        """
        if zscore:
            beta_file = self.get_video_betas_path(
                sub, video_num, direction, glmtype, resolution, zscore=True
            )
        else:
            beta_file = self.get_video_betas_path(
                sub, video_num, direction, glmtype, resolution, zscore=False
            )

        if not os.path.exists(beta_file):
            # print(f"File {beta_file} does not exist")
            return None
        else:
            beta = nib.load(beta_file).get_fdata()
            # print(f"Loaded beta from {beta_file}")
            # print(f"Shape of beta: {beta.shape}")
            if average_repeat:
                beta = beta.mean(axis=0)
            return beta
