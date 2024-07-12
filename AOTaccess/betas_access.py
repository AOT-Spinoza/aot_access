import AOTaccess
from pathlib import Path
import sys
import os
import yaml
import nibabel as nib

basedir = Path(__file__).resolve().parent
settings = yaml.safe_load(open(basedir / 'settings.yml'))
glmsingle_dir = Path(settings['paths']['glmsingle'])

def get_glmsingle_dir(sub,ses,stctype = "nordicstc"):
    sub = str(sub).zfill(3)
    ses = str(ses).zfill(2)
    return glmsingle_dir / f'sub-{sub}_ses-{ses}_T1W_{stctype}_mainfull'

def get_nii_dir_path(sub,ses,stctype = "nordicstc",glmtype = "TYPED_FITHRF_GLMDENOISE_RR"):
    glmsingle_dir = get_glmsingle_dir(sub,ses,stctype)
    glm_type_dir = glmsingle_dir / glmtype
    return glm_type_dir 

def read_betas(sub,ses,stctype = "nordicstc",glmtype = "TYPED_FITHRF_GLMDENOISE_RR"):
    nii_dir = get_nii_dir_path(sub,ses,stctype,glmtype)
    betas_file = nii_dir / "betasmd.nii"
    betas = nib.load(betas_file).get_fdata()
    print(f"Loaded betas from {betas_file}")
    print(f"Shape of betas: {betas.shape}")
    return betas






    
    