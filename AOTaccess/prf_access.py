import AOTaccess
from pathlib import Path
import sys
import os
import yaml
import nibabel as nib

class PrfAccess:
    def __init__(self, root_dir: Path = None):
        """
        Initialize a GLMSingleAccess instance.

        Parameters:
            stctype (str): Structure type, default is "nordicstc".

        Returns:
            None
        """
        if root_dir is not None:
            self.prf_main_dir = root_dir / "prf"
        else:
            basedir = Path(__file__).resolve().parent
            settings = yaml.safe_load(open(basedir / "settings.yml"))
            self.prf_main_dir = Path(settings["paths"]["prf"])

    def get_prf_dir_path(self):
        """
        Get the path to the main glmsingle directory.

        Parameters:
            None
        Returns:
            pathlib.Path: The path to prf_main_dir.
        """
        return self.prf_main_dir
    

    def get_prf_noiseceiling_dir_path(
        self,
        sub:int,
    ):
        """
        Get the path to the main glmsingle directory.

        Parameters:
            None
        Returns:
            pathlib.Path: The path to prf_main_dir.
        """
        return self.prf_main_dir / f"sub-{sub:03d}" / "prep" / f"sub-{sub:03d}_ses-pRF_task-pRF_rec-nordicstc_run-noiseceiling_part-mag_bold_space-epi_1.7mm.nii.gz"

    def get_prf_fits_r2_path(
        self,
        sub:int,
        model:str="gauss",
        resolution:str="1.7mm",
        runpart:str="firsthalf",
        rec:str="nordicstc",
    ):
       #/tank/shared/2024/visual/AOT/derivatives/prf/sub-001/prf_fits/params/sub-001_ses-pRF_task-pRF_rec-nordicstc_run-firsthalf_model-gauss_stage-iter_space-epi_1.7mm_desc-prf_params_r2.nii.gz

        """
        Get the path to the main glmsingle directory.
        Parameters:
            None
        Returns:
            pathlib.Path: The path to prf_main_dir.
        """
        return self.prf_main_dir / f"sub-{sub:03d}" / "prf_fits" / "params" / f"sub-{sub:03d}_ses-pRF_task-pRF_rec-{rec}_run-{runpart}_model-{model}_stage-iter_space-epi_{resolution}_desc-prf_params_r2.nii.gz"
    
    def get_prf_fits_eccentricity_path(
        self,
        sub:int,
        model:str="gauss",
        resolution:str="1.7mm",
        runpart:str="firsthalf",
        rec:str="nordicstc",
    ):
        """
        Get the path to the main glmsingle directory.
        Parameters:
            None
        Returns:
            pathlib.Path: The path to prf_main_dir.
        """
        return self.prf_main_dir / f"sub-{sub:03d}" / "prf_fits" / "params" / f"sub-{sub:03d}_ses-pRF_task-pRF_rec-{rec}_run-{runpart}_model-{model}_stage-iter_space-epi_{resolution}_desc-prf_params_ecc.nii.gz"
    
    def get_prf_fits_prfsize_path(
        self,
        sub:int,
        model:str="gauss",
        resolution:str="1.7mm",
        runpart:str="firsthalf",
        rec:str="nordicstc",
    ):
        """
        Get the path to the main glmsingle directory.
        Parameters:
            None
        Returns:
            pathlib.Path: The path to prf_main_dir.
        """
        return self.prf_main_dir / f"sub-{sub:03d}" / "prf_fits" / "params" / f"sub-{sub:03d}_ses-pRF_task-pRF_rec-{rec}_run-{runpart}_model-{model}_stage-iter_space-epi_{resolution}_desc-prf_params_prf_size.nii.gz"
    
    def get_prf_fits_polar_angle_path(
        self,
        sub:int,
        model:str="gauss",
        resolution:str="1.7mm",
        runpart:str="firsthalf",
        rec:str="nordicstc",
    ):
        """
        Get the path to the main glmsingle directory.
        Parameters:
            None
        Returns:
            pathlib.Path: The path to prf_main_dir.
        """
        return self.prf_main_dir / f"sub-{sub:03d}" / "prf_fits" / "params" / f"sub-{sub:03d}_ses-pRF_task-pRF_rec-{rec}_run-{runpart}_model-{model}_stage-iter_space-epi_{resolution}_desc-prf_params_polar.nii.gz"
    
    def get_prf_fits_x_position_path(
        self,
        sub:int,
        model:str="gauss",
        resolution:str="1.7mm",
        runpart:str="firsthalf",
        rec:str="nordicstc",
    ):
        """
        Get the path to the main glmsingle directory.
        Parameters:
            None
        Returns:
            pathlib.Path: The path to prf_main_dir.
        """
        return self.prf_main_dir / f"sub-{sub:03d}" / "prf_fits" / "params" / f"sub-{sub:03d}_ses-pRF_task-pRF_rec-{rec}_run-{runpart}_model-{model}_stage-iter_space-epi_{resolution}_desc-prf_params_x.nii.gz"
    
    def get_prf_fits_y_position_path(
        self,
        sub:int,
        model:str="gauss",
        resolution:str="1.7mm",
        runpart:str="firsthalf",
        rec:str="nordicstc",
    ):
        """
        Get the path to the main glmsingle directory.
        Parameters:
            None
        Returns:
            pathlib.Path: The path to prf_main_dir.
        """
        return self.prf_main_dir / f"sub-{sub:03d}" / "prf_fits" / "params" / f"sub-{sub:03d}_ses-pRF_task-pRF_rec-{rec}_run-{runpart}_model-{model}_stage-iter_space-epi_{resolution}_desc-prf_params_y.nii.gz"
    
    def get_prf_fits_prf_amplitude_path(
        self,
        sub:int,
        model:str="gauss",
        resolution:str="1.7mm",
        runpart:str="firsthalf",
        rec:str="nordicstc",
    ):
        """
        Get the path to the main glmsingle directory.
        Parameters:
            None
        Returns:
            pathlib.Path: The path to prf_main_dir.
        """
        return self.prf_main_dir / f"sub-{sub:03d}" / "prf_fits" / "params" / f"sub-{sub:03d}_ses-pRF_task-pRF_rec-{rec}_run-{runpart}_model-{model}_stage-iter_space-epi_{resolution}_desc-prf_params_prf_ampl.nii.gz"

    def get_prf_fits_hrf_deriv_path(
        self,
        sub:int,
        model:str="gauss",
        resolution:str="1.7mm",
        runpart:str="firsthalf",
        rec:str="nordicstc",
    ):
        """
        Get the path to the main glmsingle directory.
        Parameters:
            None
        Returns:
            pathlib.Path: The path to prf_main_dir.
        """
        return self.prf_main_dir / f"sub-{sub:03d}" / "prf_fits" / "params" / f"sub-{sub:03d}_ses-pRF_task-pRF_rec-{rec}_run-{runpart}_model-{model}_stage-iter_space-epi_{resolution}_desc-prf_params_hrf_deriv.nii.gz"
    
    def get_prf_fits_hrf_dsip_path(
        self,
        sub:int,
        model:str="gauss",
        resolution:str="1.7mm",
        runpart:str="firsthalf",
        rec:str="nordicstc",
    ):
        """
        Get the path to the main glmsingle directory.
        Parameters:
            None
        Returns:
            pathlib.Path: The path to prf_main_dir.
        """
        return self.prf_main_dir / f"sub-{sub:03d}" / "prf_fits" / "params" / f"sub-{sub:03d}_ses-pRF_task-pRF_rec-{rec}_run-{runpart}_model-{model}_stage-iter_space-epi_{resolution}_desc-prf_params_hrf_dsip.nii.gz"
    
    def get_prf_fits_BDratio_path(
        self,
        sub:int,
        model:str="norm",
        resolution:str="1.7mm",
        runpart:str="firsthalf",
        rec:str="nordicstc",
    ):
        """
        Get the path to the main glmsingle directory.
        Parameters:
            None
        Returns:
            pathlib.Path: The path to prf_main_dir.
        """
        return self.prf_main_dir / f"sub-{sub:03d}" / "prf_fits" / "params" / f"sub-{sub:03d}_ses-pRF_task-pRF_rec-{rec}_run-{runpart}_model-{model}_stage-iter_space-epi_{resolution}_desc-prf_params_BDratio.nii.gz"
    
    def get_prf_fits_bold_baseline_path(
        self,
        sub:int,
        model:str="norm",
        resolution:str="1.7mm",
        runpart:str="firsthalf",
        rec:str="nordicstc",
    ):
        """
        Get the path to the main glmsingle directory.
        Parameters:
            None
        Returns:
            pathlib.Path: The path to prf_main_dir.
        """
        return self.prf_main_dir / f"sub-{sub:03d}" / "prf_fits" / "params" / f"sub-{sub:03d}_ses-pRF_task-pRF_rec-{rec}_run-{runpart}_model-{model}_stage-iter_space-epi_{resolution}_desc-prf_params_bold_bsl.nii.gz"
    
    def get_prf_fits_surround_amplitude_path(
        self,
        sub:int,
        model:str="norm",
        resolution:str="1.7mm",
        runpart:str="firsthalf",
        rec:str="nordicstc",
    ):
        """
        Get the path to the main glmsingle directory.
        Parameters:
            None
        Returns:
            pathlib.Path: The path to prf_main_dir.
        """
        return self.prf_main_dir / f"sub-{sub:03d}" / "prf_fits" / "params" / f"sub-{sub:03d}_ses-pRF_task-pRF_rec-{rec}_run-{runpart}_model-{model}_stage-iter_space-epi_{resolution}_desc-prf_params_surr_ampl.nii.gz"
    
    def get_prf_fits_surround_baseline_path(
        self,
        sub:int,
        model:str="norm",
        resolution:str="1.7mm",
        runpart:str="firsthalf",
        rec:str="nordicstc",
    ):
        """
        Get the path to the main glmsingle directory.
        Parameters:
            None
        Returns:
            pathlib.Path: The path to prf_main_dir.
        """
        return self.prf_main_dir / f"sub-{sub:03d}" / "prf_fits" / "params" / f"sub-{sub:03d}_ses-pRF_task-pRF_rec-{rec}_run-{runpart}_model-{model}_stage-iter_space-epi_{resolution}_desc-prf_params_surr_bsl.nii.gz"
    
    def get_prf_fits_surround_size_path(
        self,
        sub:int,
        model:str="norm",
        resolution:str="1.7mm",
        runpart:str="firsthalf",
        rec:str="nordicstc",
    ):
        """
        Get the path to the main glmsingle directory.
        Parameters:
            None
        Returns:
            pathlib.Path: The path to prf_main_dir.
        """
        return self.prf_main_dir / f"sub-{sub:03d}" / "prf_fits" / "params" / f"sub-{sub:03d}_ses-pRF_task-pRF_rec-{rec}_run-{runpart}_model-{model}_stage-iter_space-epi_{resolution}_desc-prf_params_surr_size.nii.gz"
    
    def get_prf_fits_neuro_baseline_path(
        self,
        sub:int,
        model:str="norm",
        resolution:str="1.7mm",
        runpart:str="firsthalf",
        rec:str="nordicstc",
    ):
        """
        Get the path to the main glmsingle directory.
        Parameters:
            None
        Returns:
            pathlib.Path: The path to prf_main_dir.
        """
        return self.prf_main_dir / f"sub-{sub:03d}" / "prf_fits" / "params" / f"sub-{sub:03d}_ses-pRF_task-pRF_rec-{rec}_run-{runpart}_model-{model}_stage-iter_space-epi_{resolution}_desc-prf_params_neur_bsl.nii.gz"
    
    def read_R2(
        self,
        sub:int,
        model:str="gauss",
        resolution:str="1.7mm",
        runpart:str="firsthalf",
        rec:str="nordicstc",
    ):
        """
        Read the R2 data for a given subject and session.

        Parameters:
            sub (int): Subject number.
            ses (int): Session number.
            glmtype (str): GLM type, default is "TYPED_FITHRF_GLMDENOISE_RR".

        Returns:
            np.ndarray: The R2 data.
        """
        r2_path = self.get_prf_fits_r2_path(sub, model, resolution, runpart, rec)
        r2_data = nib.load(r2_path).get_fdata()
        return r2_data
    
    def read_eccentricity(
        self,
        sub:int,
        model:str="gauss",
        resolution:str="1.7mm",
        runpart:str="firsthalf",
        rec:str="nordicstc",
    ):
        """
        Read the eccentricity data for a given subject and session.

        Parameters:
            sub (int): Subject number.
            ses (int): Session number.
            glmtype (str): GLM type, default is "TYPED_FITHRF_GLMDENOISE_RR".

        Returns:
            np.ndarray: The eccentricity data.
        """
        ecc_path = self.get_prf_fits_eccentricity_path(sub, model, resolution, runpart, rec)
        ecc_data = nib.load(ecc_path).get_fdata()
        return ecc_data
    
    def read_prfsize(
        self,
        sub:int,
        model:str="gauss",
        resolution:str="1.7mm",
        runpart:str="firsthalf",
        rec:str="nordicstc",
    ):
        """
        Read the prfsize data for a given subject and session.

        Parameters:
            sub (int): Subject number.
            ses (int): Session number.
            glmtype (str): GLM type, default is "TYPED_FITHRF_GLMDENOISE_RR".

        Returns:
            np.ndarray: The prfsize data.
        """
        prfsize_path = self.get_prf_fits_prfsize_path(sub, model, resolution, runpart, rec)
        prfsize_data = nib.load(prfsize_path).get_fdata()
        return prfsize_data
    
    def read_polar_angle(
        self,
        sub:int,
        model:str="gauss",
        resolution:str="1.7mm",
        runpart:str="firsthalf",
        rec:str="nordicstc",
    ):
        """
        Read the polar angle data for a given subject and session.

        Parameters:
            sub (int): Subject number.
            ses (int): Session number.
            glmtype (str): GLM type, default is "TYPED_FITHRF_GLMDENOISE_RR".

        Returns:
            np.ndarray: The polar angle data.
        """
        polar_angle_path = self.get_prf_fits_polar_angle_path(sub, model, resolution, runpart, rec)
        polar_angle_data = nib.load(polar_angle_path).get_fdata()
        return polar_angle_data
    
    def read_x_position(
        self,
        sub:int,
        model:str="gauss",
        resolution:str="1.7mm",
        runpart:str="firsthalf",
        rec:str="nordicstc",
    ):
        """
        Read the x position data for a given subject and session.

        Parameters:
            sub (int): Subject number.
            ses (int): Session number.
            glmtype (str): GLM type, default is "TYPED_FITHRF_GLMDENOISE_RR".

        Returns:
            np.ndarray: The x position data.
        """
        x_position_path = self.get_prf_fits_x_position_path(sub, model, resolution, runpart, rec)
        x_position_data = nib.load(x_position_path).get_fdata()
        return x_position_data
    
    def read_y_position(
        self,
        sub:int,
        model:str="gauss",
        resolution:str="1.7mm",
        runpart:str="firsthalf",
        rec:str="nordicstc",
    ):
        """
        Read the y position data for a given subject and session.

        Parameters:
            sub (int): Subject number.
            ses (int): Session number.
            glmtype (str): GLM type, default is "TYPED_FITHRF_GLMDENOISE_RR".

        Returns:
            np.ndarray: The y position data.
        """
        y_position_path = self.get_prf_fits_y_position_path(sub, model, resolution, runpart, rec)
        y_position_data = nib.load(y_position_path).get_fdata()
        return y_position_data
    
    def read_prf_amplitude(
        self,
        sub:int,
        model:str="gauss",
        resolution:str="1.7mm",
        runpart:str="firsthalf",
        rec:str="nordicstc",
    ):
        """
        Read the amplitude data for a given subject and session.

        Parameters:
            sub (int): Subject number.
            ses (int): Session number.
            glmtype (str): GLM type, default is "TYPED_FITHRF_GLMDENOISE_RR".

        Returns:
            np.ndarray: The amplitude data.
        """
        amplitude_path = self.get_prf_fits_prf_amplitude_path(sub, model, resolution, runpart, rec)
        amplitude_data = nib.load(amplitude_path).get_fdata()
        return amplitude_data
    
    def read_hrf_deriv(
        self,
        sub:int,
        model:str="gauss",
        resolution:str="1.7mm",
        runpart:str="firsthalf",
        rec:str="nordicstc",
    ):
        """
        Read the hrf deriv data for a given subject and session.

        Parameters:
            sub (int): Subject number.
            ses (int): Session number.
            glmtype (str): GLM type, default is "TYPED_FITHRF_GLMDENOISE_RR".

        Returns:
            np.ndarray: The hrf deriv data.
        """
        hrf_deriv_path = self.get_prf_fits_hrf_deriv_path(sub, model, resolution, runpart, rec)
        hrf_deriv_data = nib.load(hrf_deriv_path).get_fdata()
        return hrf_deriv_data
    
    def read_hrf_dsip(
        self,
        sub:int,
        model:str="gauss",
        resolution:str="1.7mm",
        runpart:str="firsthalf",
        rec:str="nordicstc",
    ):
        """
        Read the hrf dsip data for a given subject and session.

        Parameters:
            sub (int): Subject number.
            ses (int): Session number.
            glmtype (str): GLM type, default is "TYPED_FITHRF_GLMDENOISE_RR".

        Returns:
            np.ndarray: The hrf dsip data.
        """
        hrf_dsip_path = self.get_prf_fits_hrf_dsip_path(sub, model, resolution, runpart, rec)
        hrf_dsip_data = nib.load(hrf_dsip_path).get_fdata()
        return hrf_dsip_data
    
    def read_BDratio(
        self,
        sub:int,
        model:str="norm",
        resolution:str="1.7mm",
        runpart:str="firsthalf",
        rec:str="nordicstc",
    ):
        """
        Read the BDratio data for a given subject and session.

        Parameters:
            sub (int): Subject number.
            ses (int): Session number.
            glmtype (str): GLM type, default is "TYPED_FITHRF_GLMDENOISE_RR".

        Returns:
            np.ndarray: The BDratio data.
        """
        bd_ratio_path = self.get_prf_fits_BDratio_path(sub, model, resolution, runpart, rec)
        bd_ratio_data = nib.load(bd_ratio_path).get_fdata()
        return bd_ratio_data
    
    def read_bold_baseline(
        self,
        sub:int,
        model:str="norm",
        resolution:str="1.7mm",
        runpart:str="firsthalf",
        rec:str="nordicstc",
    ):
        """
        Read the bold baseline data for a given subject and session.

        Parameters:
            sub (int): Subject number.
            ses (int): Session number.
            glmtype (str): GLM type, default is "TYPED_FITHRF_GLMDENOISE_RR".

        Returns:
            np.ndarray: The bold baseline data.
        """
        bold_baseline_path = self.get_prf_fits_bold_baseline_path(sub, model, resolution, runpart, rec)
        bold_baseline_data = nib.load(bold_baseline_path).get_fdata()
        return bold_baseline_data
    
    def read_surround_amplitude(
        self,
        sub:int,
        model:str="norm",
        resolution:str="1.7mm",
        runpart:str="firsthalf",
        rec:str="nordicstc",
    ):
        """
        Read the surround amplitude data for a given subject and session.

        Parameters:
            sub (int): Subject number.
            ses (int): Session number.
            glmtype (str): GLM type, default is "TYPED_FITHRF_GLMDENOISE_RR".

        Returns:
            np.ndarray: The surround amplitude data.
        """
        surround_amplitude_path = self.get_prf_fits_surround_amplitude_path(sub, model, resolution, runpart, rec)
        surround_amplitude_data = nib.load(surround_amplitude_path).get_fdata()
        return surround_amplitude_data
    
    def read_surround_baseline(
        self,
        sub:int,
        model:str="norm",
        resolution:str="1.7mm",
        runpart:str="firsthalf",
        rec:str="nordicstc",
    ):
        """
        Read the surround baseline data for a given subject and session.

        Parameters:
            sub (int): Subject number.
            ses (int): Session number.
            glmtype (str): GLM type, default is "TYPED_FITHRF_GLMDENOISE_RR".

        Returns:
            np.ndarray: The surround baseline data.
        """
        surround_baseline_path = self.get_prf_fits_surround_baseline_path(sub, model, resolution, runpart, rec)
        surround_baseline_data = nib.load(surround_baseline_path).get_fdata()
        return surround_baseline_data
    
    def read_surround_size(
        self,
        sub:int,
        model:str="norm",
        resolution:str="1.7mm",
        runpart:str="firsthalf",
        rec:str="nordicstc",
    ):
        """
        Read the surround size data for a given subject and session.

        Parameters:
            sub (int): Subject number.
            ses (int): Session number.
            glmtype (str): GLM type, default is "TYPED_FITHRF_GLMDENOISE_RR".

        Returns:
            np.ndarray: The surround size data.
        """
        surround_size_path = self.get_prf_fits_surround_size_path(sub, model, resolution, runpart, rec)
        surround_size_data = nib.load(surround_size_path).get_fdata()
        return surround_size_data
    
    def read_neuro_baseline(
        self,
        sub:int,
        model:str="norm",
        resolution:str="1.7mm",
        runpart:str="firsthalf",
        rec:str="nordicstc",
    ):
        """
        Read the neuro baseline data for a given subject and session.

        Parameters:
            sub (int): Subject number.
            ses (int): Session number.
            glmtype (str): GLM type, default is "TYPED_FITHRF_GLMDENOISE_RR".

        Returns:
            np.ndarray: The neuro baseline data.
        """
        neuro_baseline_path = self.get_prf_fits_neuro_baseline_path(sub, model, resolution, runpart, rec)
        neuro_baseline_data = nib.load(neuro_baseline_path).get_fdata()
        return neuro_baseline_data
    
    def read_noiseceiling(
        self,
        sub:int,
        ses:int,
        glmtype:str="TYPED_FITHRF_GLMDENOISE_RR",
        resolution:str="1.7mm",
    ):
        """
        Read the noise ceiling data for a given subject and session.

        Parameters:
            sub (int): Subject number.
            ses (int): Session number.
            glmtype (str): GLM type, default is "TYPED_FITHRF_GLMDENOISE_RR".

        Returns:
            np.ndarray: The noise ceiling data.
        """
        noiseceiling_path = self.get_prf_noiseceiling_dir_path(sub)
        noiseceiling_data = nib.load(noiseceiling_path).get_fdata()
        return noiseceiling_data
    
    
    def get_method_list(self):
        """
        Get a list of available methods for accessing pRF data.

        Returns:
            list: List of method names.
        """
        return [
            "read_R2",
            "read_eccentricity",
            "read_prfsize",
            "read_polar_angle",
            "read_x_position",
            "read_y_position",
            "read_prf_amplitude",
            "read_hrf_deriv",
            "read_hrf_dsip",
            "read_BDratio",
            "read_bold_baseline",
            "read_surround_amplitude",
            "read_surround_baseline",
            "read_surround_size",
            "read_neuro_baseline",
        ]


