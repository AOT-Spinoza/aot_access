import AOTaccess
from pathlib import Path
import sys
import os
import yaml
import nibabel as nib


class GLMSingleAccess:
    def __init__(self, sub, ses, stctype="nordicstc"):

        basedir = Path(__file__).resolve().parent
        settings = yaml.safe_load(open(basedir / "settings.yml"))
        glmsingle_dir = Path(settings["paths"]["glmsingle"])

        self.sub = sub
        self.ses = ses
        self.stctype = stctype
        self.glmsingle_dir = self.get_glmsingle_dir(sub, ses, stctype)

    def get_glmsingle_dir(self, sub, ses, stctype):
        glmsingle_dir = self.glmsingle_dir / f"sub-{sub:03d}/ses-{ses:02d}/{stctype}"
        return glmsingle_dir

    def get_nii_dir_path(self, glmtype="TYPED_FITHRF_GLMDENOISE_RR"):
        glm_type_dir = self.glmsingle_dir / glmtype
        return glm_type_dir

    def read_betas(self, glmtype="TYPED_FITHRF_GLMDENOISE_RR"):
        nii_dir = self.get_nii_dir_path(glmtype)
        betas_file = nii_dir / "betasmd.nii"
        betas = nib.load(betas_file).get_fdata()
        print(f"Loaded betas from {betas_file}")
        print(f"Shape of betas: {betas.shape}")
        return betas

    def read_meanvol(self, glmtype="TYPED_FITHRF_GLMDENOISE_RR"):
        nii_dir = self.get_nii_dir_path(glmtype)
        meanvol_file = nii_dir / "meanvol.nii"
        meanvol = nib.load(meanvol_file).get_fdata()
        print(f"Loaded meanvol from {meanvol_file}")
        print(f"Shape of meanvol: {meanvol.shape}")
        return meanvol

    def read_R2(self, glmtype="TYPED_FITHRF_GLMDENOISE_RR"):
        nii_dir = self.get_nii_dir_path(glmtype)
        R2_file = nii_dir / "R2.nii"
        R2 = nib.load(R2_file).get_fdata()
        print(f"Loaded R2 from {R2_file}")
        print(f"Shape of R2: {R2.shape}")
        return R2
