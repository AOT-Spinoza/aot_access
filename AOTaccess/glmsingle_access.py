import AOTaccess
from pathlib import Path
import sys
import os
import yaml
import nibabel as nib


class GLMSingleAccess:
    def __init__(self, stctype="nordicstc"):
        """
        Initialize a GLMSingleAccess instance.

        Parameters:
            stctype (str): Structure type, default is "nordicstc".

        Returns:
            None
        """
        basedir = Path(__file__).resolve().parent
        settings = yaml.safe_load(open(basedir / "settings.yml"))
        self.glmsingle_main_dir = Path(settings["paths"]["glmsingle"]) / "mainexp"

        self.video_betas_dir = Path(settings["paths"]["glmsingle"]) / "video_betas"
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
        self, sub: int, ses: int, glmtype: str = "TYPED_FITHRF_GLMDENOISE_RR"
    ):
        """
        Get the nii directory path for a given subject and session.

        Parameters:
            sub (int): Subject number.
            ses (int): Session number.
            glmtype (str): GLM type, default is "TYPED_FITHRF_GLMDENOISE_RR".

        Returns:
            pathlib.Path: Directory path where betas and other files are located.
        """
        glm_type_dir = (
            self.glmsingle_main_dir
            / f"sub-{sub:03d}_ses-{ses:02d}_T1W_{self.stctype}"
            / glmtype
        )
        return glm_type_dir

    def read_shape(
        self, sub: int, ses: int, glmtype: str = "TYPED_FITHRF_GLMDENOISE_RR"
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
        R2 = self.read_R2(sub, ses, glmtype)
        return R2.shape

    def read_betas(  # by session
        self, sub: int, ses: int, glmtype: str = "TYPED_FITHRF_GLMDENOISE_RR"
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
        nii_dir = self.get_nii_dir_path(sub, ses, glmtype)
        betas_file = nii_dir / "betasmd.nii"
        betas = nib.load(betas_file).get_fdata()
        print(f"Loaded betas from {betas_file}")
        print(f"Shape of betas: {betas.shape}")
        return betas

    def read_affine(
        self, sub: int, ses: int, glmtype: str = "TYPED_FITHRF_GLMDENOISE_RR"
    ):
        """
        Load and return the affine matrix for a given subject and session.

        Parameters:
            sub (int): Subject number.
            ses (int): Session number.
            glmtype (str): GLM type.

        Returns:
            numpy.ndarray: The loaded affine matrix.
        """
        nii_dir = self.get_nii_dir_path(sub, ses, glmtype)
        betas_file = nii_dir / "betasmd.nii"
        betas = nib.load(betas_file)
        affine = betas.affine
        print(f"Loaded affine from {betas_file}")
        return affine

    def read_meanvol(
        self, sub: int, ses: int, glmtype: str = "TYPED_FITHRF_GLMDENOISE_RR"
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
        nii_dir = self.get_nii_dir_path(sub, ses, glmtype)
        meanvol_file = nii_dir / "meanvol.nii"
        meanvol = nib.load(meanvol_file).get_fdata()
        print(f"Loaded meanvol from {meanvol_file}")
        print(f"Shape of meanvol: {meanvol.shape}")
        return meanvol

    def read_R2(self, sub: int, ses: int, glmtype: str = "TYPED_FITHRF_GLMDENOISE_RR"):
        """
        Load and return the R2 data for a given subject and session.

        Parameters:
            sub (int): Subject number.
            ses (int): Session number.
            glmtype (str): GLM type.

        Returns:
            numpy.ndarray: Array containing the loaded R2 data.
        """
        nii_dir = self.get_nii_dir_path(sub, ses, glmtype)
        R2_file = nii_dir / "R2.nii"
        R2 = nib.load(R2_file).get_fdata()
        print(f"Loaded R2 from {R2_file}")
        print(f"Shape of R2: {R2.shape}")
        return R2

    def read_R2_mask(
        self,
        sub: int,
        ses: int,
        glmtype: str = "TYPED_FITHRF_GLMDENOISE_RR",
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
        R2 = self.read_R2(sub, ses, glmtype)
        R2_mask = R2 > threshold
        R2_mask = R2_mask.astype(bool)
        print(f"Shape of R2 mask: {R2_mask.shape}")
        return R2_mask

    def read_video_betas(
        self,
        sub: int,
        video_num: int,
        direction: str = "fw",
        glmtype: str = "TYPED_FITHRF_GLMDENOISE_RR",
        # space: str =
    ):
        """
        Load and return the betas data for a specific video.

        Parameters:
            sub (int): Subject number.
            video_num (int): Video number.
            direction (str): Video direction, default is "fw".
            glmtype (str): GLM type.

        Returns:
            numpy.ndarray or None: Array containing the video betas data, or None if the file does not exist.
        """
        beta_file = (
            self.video_betas_dir
            / f"sub-{sub:03d}"
            / f"{video_num:04d}_{direction}_betas.nii"
        )

        if not os.path.exists(beta_file):
            print(f"File {beta_file} does not exist")
            return None
        else:
            beta = nib.load(beta_file).get_fdata()
            print(f"Loaded beta from {beta_file}")
            print(f"Shape of beta: {beta.shape}")
            return beta
