import AOTaccess
from pathlib import Path
import sys
import os
import yaml
import nibabel as nib


class GLMSingleAccess:
    def __init__(self, stctype="nordicstc"):

        basedir = Path(__file__).resolve().parent
        settings = yaml.safe_load(open(basedir / "settings.yml"))
        self.glmsingle_main_dir = Path(settings["paths"]["glmsingle"]) / "mainexp"

        self.video_betas_dir = Path(settings["paths"]["glmsingle"]) / "video_betas"
        self.stctype = stctype

    def get_glm_dir_path(self):
        return self.glmsingle_main_dir

    def get_nii_dir_path(
        self, sub: int, ses: int, glmtype: str = "TYPED_FITHRF_GLMDENOISE_RR"
    ):
        glm_type_dir = (
            self.glmsingle_main_dir
            / f"sub-{sub:03d}_ses-{ses:02d}_T1W_{self.stctype}"
            / glmtype
        )
        return glm_type_dir

    def read_betas(
        self, sub: int, ses: int, glmtype: str = "TYPED_FITHRF_GLMDENOISE_RR"
    ):
        nii_dir = self.get_nii_dir_path(sub, ses, glmtype)
        betas_file = nii_dir / "betasmd.nii"
        betas = nib.load(betas_file).get_fdata()
        print(f"Loaded betas from {betas_file}")
        print(f"Shape of betas: {betas.shape}")
        return betas

    def read_affine(
        self, sub: int, ses: int, glmtype: str = "TYPED_FITHRF_GLMDENOISE_RR"
    ):
        nii_dir = self.get_nii_dir_path(sub, ses, glmtype)
        betas_file = nii_dir / "betasmd.nii"
        betas = nib.load(betas_file)
        affine = betas.affine
        print(f"Loaded affine from {betas_file}")
        return affine

    def read_meanvol(
        self, sub: int, ses: int, glmtype: str = "TYPED_FITHRF_GLMDENOISE_RR"
    ):
        nii_dir = self.get_nii_dir_path(sub, ses, glmtype)
        meanvol_file = nii_dir / "meanvol.nii"
        meanvol = nib.load(meanvol_file).get_fdata()
        print(f"Loaded meanvol from {meanvol_file}")
        print(f"Shape of meanvol: {meanvol.shape}")
        return meanvol

    def read_R2(self, sub: int, ses: int, glmtype: str = "TYPED_FITHRF_GLMDENOISE_RR"):
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
    ):
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
