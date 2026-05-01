import AOTaccess
from pathlib import Path
import sys
import os
import yaml
import numpy as np
import h5py
import csv
import json
import torch


class StimuliInfoAccess:
    def __init__(self, root_dir: Path = None):
        """
        Initialize the StimuliInfoAccess instance.

        Loads video and video annotation directories from the settings.

        Parameters:
            None

        Returns:
            None
        """
        if root_dir is not None:
            self.video_dir = root_dir / "videos"
            self.video_annotation_dir = root_dir / "video_annotations"
        else:
            basedir = Path(__file__).resolve().parent
            settings = yaml.safe_load(open(basedir / "settings.yml"))
            self.video_dir = Path(settings["paths"]["videos"])
            self.picture_dir = Path(settings["paths"]["pictures"])
            self.video_annotation_dir = Path(settings["paths"]["video_annotations"])

    def get_video_path(self, video_id: int, direction: str = "fw"):
        """
        Get the video file path.

        Parameters:
            video_id (int): Video identification number.
            direction (str): Video direction, default is "fw".

        Returns:
            pathlib.Path: Path to the video file.
        """
        return self.video_dir / f"{video_id:04d}_{direction}.mp4"
    
    def get_picture_path(self, video_id: int, direction: str = "fw"):
        """
        Get the picture file path.

        Parameters:
            video_id (int): Video identification number.
            direction (str): Video direction, default is "fw".

        Returns:
            pathlib.Path: Path to the picture file.
        """
        return self.picture_dir / f"{video_id:04d}_{direction}.png"


    def get_video_annotation_dir(self, video_id, direction="fw"):
        """
        Get the directory for video annotations.

        Parameters:
            video_id (int): Video identification number.
            direction (str): Video direction, default is "fw".

        Returns:
            pathlib.Path: Path to the video annotation directory.
        """
        return self.video_annotation_dir / f"{video_id:04d}_{direction}.mp4"
    
    def _temp_read_qwen_description(self, video_id: int, direction: str = "fw"):
        """
        Temporarily read the Qwen description text for a video.

        Parameters:
            video_id (int): Video identification number.
            direction (str): Video direction, default is "fw".

        Returns:
            str: Content of the description text file.
        """
        # example : /tank/shared/2024/visual/AOT/derivatives/DLoutputs/videollama_describe/simple_describe_en_clean/0001_fw.txt
        temp_root_dir = Path(
            "/tank/shared/2024/visual/AOT/derivatives/DLoutputs/qwen_describe/videos_fw_describe_qwen_pure"
        )
        temp_file = temp_root_dir / f"{video_id:04d}_{direction}.txt"
        with open(temp_file, "r") as f:
            return f.read()
        
    def _temp_read_qwen_embedding(self, video_id: int, direction: str = "fw"):
        """
        Temporarily read the Qwen embedding for a video.

        Parameters:
            video_id (int): Video identification number.
            direction (str): Video direction, default is "fw".

        Returns:
            dict: Content of the embedding JSON file.
        """
        # example :  "/tank/shared/2024/visual/AOT/derivatives/DLoutputs/qwen_embedding/videos_fw_describe_qwen_pure_embedding_2048/0001_fw_embedding.json"

        temp_root_dir1 = Path(
            "/tank/shared/2024/visual/AOT/derivatives/DLoutputs/qwen_embedding/videos_fw_describe_qwen_pure_embedding_2048"
        )
        temp_root_dir2 = Path(
            "/projects/prjs1914/output/qwen_embedding/videos_fw_describe_qwen_pure_embedding_2048"
        )

        if temp_root_dir1.exists():
            temp_root_dir = temp_root_dir1
        elif temp_root_dir2.exists():
            temp_root_dir = temp_root_dir2
        else:
            raise FileNotFoundError(f"Qwen embedding file not found: {temp_root_dir1} or {temp_root_dir2}")

        temp_file = temp_root_dir / f"{video_id:04d}_{direction}_embedding.json"
        with open(temp_file, "r") as f:
            data = json.load(f)
        embedding = data["data"][0]["embedding"]
        #make is numpy array
        embedding = np.array(embedding)
        return embedding


    def _temp_read_llama_description(self, video_id: int, direction: str = "fw"):
        """
        Temporarily read the llama description text for a video.

        Parameters:
            video_id (int): Video identification number.
            direction (str): Video direction, default is "fw".

        Returns:
            str: Content of the description text file.
        """
        # example : /tank/shared/2024/visual/AOT/derivatives/DLoutputs/videollama_describe/simple_describe_en_clean/0001_fw.txt
        temp_root_dir = Path(
            "/tank/shared/2024/visual/AOT/derivatives/DLoutputs/videollama_describe/simple_describe_en_clean"
        )
        temp_file = temp_root_dir / f"{video_id:04d}_{direction}.txt"
        with open(temp_file, "r") as f:
            return f.read()

    def _temp_read_llama_description_v2(self, video_id: int, direction: str = "fw"):
        """
        Temporarily read the version 2 llama description text for a video.

        Parameters:
            video_id (int): Video identification number.
            direction (str): Video direction, default is "fw".

        Returns:
            str: Content of the description text file.
        """
        # example : /tank/shared/2024/visual/AOT/derivatives/DLoutputs/videollama_describe/simple_describe_en_clean/0001_fw.txt
        temp_root_dir = Path(
            "/tank/shared/2024/visual/AOT/derivatives/DLoutputs/videollama_describe/withsample_t0.2_r1_v2.1"
        )
        temp_file = temp_root_dir / f"{video_id:04d}_{direction}.txt"
        with open(temp_file, "r") as f:
            return f.read()

    def _temp_read_sbert_embeddings(self, video_id: int, direction: str = "fw"):
        """
        Temporarily load SBERT embeddings for a video.

        Parameters:
            video_id (int): Video identification number.
            direction (str): Video direction, default is "fw".

        Returns:
            numpy.ndarray: Loaded SBERT embeddings.
        """
        temp_root_dir = Path(
            # "/tank/shared/2024/visual/AOT/derivatives/DLoutputs/sbert/simple_describe_en_clean_embeddings"
            "/tank/shared/2024/visual/AOT/derivatives/DLoutputs/sbert_all-mpnet-base-v2/simple_describe_en_withsample_cleaned_embeddings_averaged"
        )
        temp_file = temp_root_dir / f"{video_id:04d}_{direction}.npy"
        return np.load(temp_file)

    def _temp_read_sbert_embeddings_PCA(self, video_id: int, direction: str = "fw"):
        """
        Temporarily load PCA-transformed SBERT embeddings for a video.

        Parameters:
            video_id (int): Video identification number.
            direction (str): Video direction, default is "fw".

        Returns:
            numpy.ndarray: Loaded PCA-transformed embeddings.
        """
        temp_root_dir = Path(
            "/tank/shared/2024/visual/AOT/derivatives/DLoutputs/sbert_all-mpnet-base-v2/pca_embeddings"
        )
        temp_file = temp_root_dir / f"{video_id:04d}_{direction}.npy"
        return np.load(temp_file)

    def _temp_read_sbert_embeddings_SAE(self, video_id: int, direction: str = "fw"):
        """
        Temporarily load SAE-transformed SBERT embeddings for a video.

        Parameters:
            video_id (int): Video identification number.
            direction (str): Video direction, default is "fw".

        Returns:
            numpy.ndarray: Loaded SAE-transformed embeddings.
        """
        temp_root_dir = Path(
            "/tank/shared/2024/visual/AOT/derivatives/DLoutputs/sbert_all-mpnet-base-v2/sae_embeddings"
        )
        temp_file = temp_root_dir / f"{video_id:04d}_{direction}.npy"
        return np.load(temp_file)

    def _temp_read_motion_energy_features(
        self, video_id: int, direction: str = "fw", highest_freq=16
    ):
        """
        Temporarily load motion energy features for a video.

        Parameters:
            video_id (int): Video identification number.
            direction (str): Video direction, default is "fw".

        Returns:
            numpy.ndarray: Loaded motion energy features.
        """
        if highest_freq == 16:
            temp_root_dir = Path(
                "/tank/shared/2024/visual/AOT/temp/motion_energy_features/video_features"
            )
            temp_file = temp_root_dir / f"{video_id:04d}_{direction}.npy"
            return np.load(temp_file)
        elif highest_freq == 32:
            temp_root_dir1 = Path(
                "/tank/shared/2024/visual/AOT/temp/motion_freq_test[0,2,4,8,16,32]"
            )
            temp_root_dir2 = Path(
                "/projects/prjs1914/output/motion_freq_test[0,2,4,8,16,32]"  
            )

            if temp_root_dir1.exists():
                temp_root_dir = temp_root_dir1
            elif temp_root_dir2.exists():
                temp_root_dir = temp_root_dir2
            else:
                raise FileNotFoundError(f"Motion energy features file not found: {temp_root_dir1} or {temp_root_dir2}")
            temp_file = temp_root_dir / f"{video_id:04d}_{direction}.mp4.npy"
            return np.load(temp_file)

    def _temp_load_vae_latent(self, latent_file: Path, kind: str = "VAE"):
        if not latent_file.exists():
            raise FileNotFoundError(f"{kind} latent file not found: {latent_file}")

        try:
            payload = torch.load(latent_file, map_location="cpu", weights_only=False)
        except TypeError:
            payload = torch.load(latent_file, map_location="cpu")

        if isinstance(payload, dict):
            latent = payload.get("latent")
            if latent is None:
                raise KeyError(f"Missing 'latent' in {kind} latent file: {latent_file}")
        else:
            # Some pipelines save a raw tensor directly.
            latent = payload

        if isinstance(latent, torch.Tensor):
            return latent.detach().cpu().numpy()
        return np.asarray(latent)

    def _temp_read_VAE_latents(self, video_id: int, direction: str = "fw"):
        """
        Temporarily load the VAE latent for a video.

        Parameters:
            video_id (int): Video identification number.
            direction (str): Video direction, default is "fw".

        Returns:
            numpy.ndarray: VAE latent array.
        """
        temp_root_dir = Path("/projects/prjs1914/output/vae_latent_540p")
        sample_name = f"{video_id:04d}_{direction}_16by9_960x544_crop_540p"
        temp_file = temp_root_dir / sample_name / f"{sample_name}_latent.pt"
        return self._temp_load_vae_latent(temp_file, kind="VAE")

    def _temp_read_VAE_latents_flattened(self, video_id: int, direction: str = "fw"):
        #example file : /projects/prjs1914/output/vae_latent_540p_flattened/0001_fw_16by9_960x544_crop_540p/0001_fw_16by9_960x544_crop_540p_latent_flattened.pt
        temp_root_dir = Path("/projects/prjs1914/output/vae_latent_540p_flattened")
        sample_name = f"{video_id:04d}_{direction}_16by9_960x544_crop_540p"
        temp_file = temp_root_dir / sample_name / f"{sample_name}_latent_flattened.pt"
        return self._temp_load_vae_latent(temp_file, kind="flattened VAE")

    def _temp_read_VAE_latents_time_averaged(self, video_id: int, direction: str = "fw"):
        """
        Temporarily load the time-averaged VAE latent for a video.

        Parameters:
            video_id (int): Video identification number.
            direction (str): Video direction, default is "fw".

        Returns:
            numpy.ndarray: Time-averaged latent array.
        """
        temp_root_dir = Path("/projects/prjs1914/output/vae_latent_540p_time_averaged")
        sample_name = f"{video_id:04d}_{direction}_16by9_960x544_crop_540p"
        temp_file = temp_root_dir / sample_name / f"{sample_name}_latent.pt"
        return self._temp_load_vae_latent(temp_file, kind="time-averaged VAE")

    def _temp_read_VAE_latents_time_averaged_flattened(self, video_id: int, direction: str = "fw"):
        """
        Temporarily load the time-averaged and flattened VAE latent for a video.

        Parameters:
            video_id (int): Video identification number.
            direction (str): Video direction, default is "fw".

        Returns:
            numpy.ndarray: Time-averaged and flattened latent array.
        """
        #example : "/projects/prjs1914/output/vae_latent_540p_time_averaged_flattened/0001_fw_16by9_960x544_crop_540p/0001_fw_16by9_960x544_crop_540p_latent_time_averaged_flattened.pt"
        temp_root_dir = Path("/projects/prjs1914/output/vae_latent_540p_time_averaged_flattened")
        sample_name = f"{video_id:04d}_{direction}_16by9_960x544_crop_540p"
        temp_file = temp_root_dir / sample_name / f"{sample_name}_latent_time_averaged_flattened.pt"
        return self._temp_load_vae_latent(temp_file, kind="time-averaged flattened VAE")

    def _temp_read_SD3p5VAE_latents_time_averaged_flattened(
        self, video_id: int, direction: str = "fw"
    ):
        """
        Temporarily load SD3.5 time-averaged and flattened VAE latent for a video.

        Parameters:
            video_id (int): Video identification number.
            direction (str): Video direction, default is "fw".

        Returns:
            numpy.ndarray: SD3.5 time-averaged flattened latent array.
        """
        temp_root_dir = Path(
            "/projects/prjs1914/output/SD3p5VAE_latent_540p_time_averaged_flattened"
        )
        sample_name = f"{video_id:04d}_{direction}_16by9_960x544_crop_540p"
        temp_file = (
            temp_root_dir
            / sample_name
            / f"{sample_name}_latent_time_averaged_flattened.pt"
        )
        return self._temp_load_vae_latent(
            temp_file, kind="SD3.5 time-averaged flattened VAE"
        )

    def _temp_read_LaVIT_motion_pre_quant_latent_flattened(
        self, video_id: int, direction: str = "fw"
    ):
        """
        Temporarily load flattened Video-LaVIT motion pre-quant latent for a video.

        Parameters:
            video_id (int): Video identification number.
            direction (str): Video direction, default is "fw".

        Returns:
            numpy.ndarray: Flattened motion pre-quant latent array.
        """
        temp_root_dir = Path(
            "/projects/prjs1914/output/LaVIT_540p_motion_pre_quant_latent_flattened"
        )
        sample_name = f"{video_id:04d}_{direction}_16by9_960x544_crop_540p"
        temp_file = (
            temp_root_dir
            / sample_name
            / f"{sample_name}__motion_pre_quant_latent_flattened.pt"
        )
        return self._temp_load_vae_latent(
            temp_file, kind="LaVIT motion pre-quant flattened"
        )

    def _temp_load_hunyuan_text_encoder_artifacts(self, artifact_file: Path):
        if not artifact_file.exists():
            raise FileNotFoundError(
                f"Hunyuan text encoder artifact file not found: {artifact_file}"
            )

        try:
            payload = torch.load(artifact_file, map_location="cpu", weights_only=False)
        except TypeError:
            payload = torch.load(artifact_file, map_location="cpu")

        if not isinstance(payload, dict):
            raise TypeError(
                f"Unexpected Hunyuan artifact payload type {type(payload)!r} in {artifact_file}"
            )

        return payload

    def _temp_extract_hunyuan_prompt_embeds(self, payload: dict, encoder_key: str, artifact_file: Path):
        pipeline_inputs = payload.get("pipeline_inputs")
        if not isinstance(pipeline_inputs, dict):
            raise KeyError(
                f"Missing 'pipeline_inputs' in Hunyuan artifact file: {artifact_file}"
            )

        encoder_payload = pipeline_inputs.get(encoder_key)
        if not isinstance(encoder_payload, dict):
            raise KeyError(
                f"Missing '{encoder_key}' encoder payload in Hunyuan artifact file: {artifact_file}"
            )

        positive_payload = encoder_payload.get("positive")
        if not isinstance(positive_payload, dict):
            raise KeyError(
                f"Missing '{encoder_key}.positive' payload in Hunyuan artifact file: {artifact_file}"
            )

        prompt_embeds = positive_payload.get("prompt_embeds")
        if prompt_embeds is None:
            raise KeyError(
                f"Missing '{encoder_key}.positive.prompt_embeds' in Hunyuan artifact file: {artifact_file}"
            )

        if isinstance(prompt_embeds, torch.Tensor):
            return prompt_embeds.detach().cpu().numpy()
        return np.asarray(prompt_embeds)

    def _temp_read_hunyuan_MLLM_latents(self, video_id: int, direction: str = "fw"):
        # example file: /projects/prjs1914/output/hunyuan_text_embeddings/0001_fw/text_encoder_artifacts.pt
        temp_root_dir = Path("/projects/prjs1914/output/hunyuan_text_embeddings")
        sample_name = f"{video_id:04d}_{direction}"
        artifact_file = temp_root_dir / sample_name / "text_encoder_artifacts.pt"
        payload = self._temp_load_hunyuan_text_encoder_artifacts(artifact_file)
        return self._temp_extract_hunyuan_prompt_embeds(
            payload, encoder_key="llm", artifact_file=artifact_file
        )

    def _temp_read_hunyuan_CLIP_latents(self, video_id: int, direction: str = "fw"):
        temp_root_dir = Path("/projects/prjs1914/output/hunyuan_text_embeddings")
        sample_name = f"{video_id:04d}_{direction}"
        artifact_file = temp_root_dir / sample_name / "text_encoder_artifacts.pt"
        payload = self._temp_load_hunyuan_text_encoder_artifacts(artifact_file)
        return self._temp_extract_hunyuan_prompt_embeds(
            payload, encoder_key="clipL", artifact_file=artifact_file
        )

    def read_semantic_segmentation(self, video_id: int, direction: str = "fw"):
        """
        Read and return semantic segmentation data for a video.

        Parameters:
            video_id (int): Video identification number.
            direction (str): Video direction, default is "fw".

        Returns:
            numpy.ndarray: The segmentation data from the HDF5 file.
        """
        # temp : /tank/shared/2024/visual/AOT/derivatives/stimuli/annotations/0001_fw.mp4/semantic_segmentation/FCN_ResNet101/0001_fw_FCN_ResNet101.hdf5
        video_annotation_dir = self.get_video_annotation_dir(video_id, direction)
        filepath = (
            video_annotation_dir
            / "semantic_segmentation/FCN_ResNet101"
            / f"{video_id:04d}_{direction}_FCN_ResNet101.hdf5"
        )
        # read hdf5 file
        with h5py.File(filepath, "r") as f:
            return f["data"][:]

    def read_action_detection(self, video_id: int, direction: str = "fw"):
        """
        Read and return action detection data for a video.

        Parameters:
            video_id (int): Video identification number.
            direction (str): Video direction, default is "fw".

        Returns:
            numpy.ndarray: The action detection data from the HDF5 file.
        """
        # temp : /tank/shared/2024/visual/AOT/derivatives/stimuli/annotations/0001_fw.mp4/action_detection/slowfast_r50_detection/0001_fw_slowfast_r50_detection.hdf5
        video_annotation_dir = self.get_video_annotation_dir(video_id, direction)
        filepath = (
            video_annotation_dir
            / "action_detection/slowfast_r50_detection"
            / f"{video_id:04d}_{direction}_slowfast_r50_detection.hdf5"
        )
        # read hdf5 file
        with h5py.File(filepath, "r") as f:
            return f["data"][:]

    def read_action_classification(self, video_id: int, direction: str = "fw"):
        """
        Read and return action classification data for a video.

        Parameters:
            video_id (int): Video identification number.
            direction (str): Video direction, default is "fw".

        Returns:
            list of list: Rows read from the CSV file containing action classification.
        """
        # temp : /tank/shared/2024/visual/AOT/derivatives/stimuli/annotations/0003_rv.mp4/action_classification/X3D/0003_rv.mp4_X3D.csv
        video_annotation_dir = self.get_video_annotation_dir(video_id, direction)
        filepath = (
            video_annotation_dir
            / "action_classification/X3D"
            / f"{video_id:04d}_{direction}.mp4_X3D.csv"
        )
        # read csv file
        with open(filepath, "r") as f:
            reader = csv.reader(f)
            return [row for row in reader]

    def read_captioning(self, video_id: int, direction: str = "fw"):
        """
        Read and return captioning data for a video.

        Parameters:
            video_id (int): Video identification number.
            direction (str): Video direction, default is "fw".

        Returns:
            list of list: Rows read from the CSV file containing captions.
        """
        # temp : /tank/shared/2024/visual/AOT/derivatives/stimuli/annotations/0011_fw.mp4/captioning/GIT/0011_fw.mp4_GIT.csv
        video_annotation_dir = self.get_video_annotation_dir(video_id, direction)
        filepath = (
            video_annotation_dir
            / "captioning/GIT"
            / f"{video_id:04d}_{direction}.mp4_GIT.csv"
        )
        # read csv file
        with open(filepath, "r") as f:
            reader = csv.reader(f)
            return [row for row in reader]

    def read_depth_estimation(self, video_id: int, direction: str = "fw"):
        """
        Read and return depth estimation data for a video.

        Parameters:
            video_id (int): Video identification number.
            direction (str): Video direction, default is "fw".

        Returns:
            numpy.ndarray: Depth estimation data from the HDF5 file.
        """
        # temp : /tank/shared/2024/visual/AOT/derivatives/stimuli/annotations/0011_fw.mp4/depth_estimation/MiDaS/0011_fw.mp4_MiDaS.hdf5
        video_annotation_dir = self.get_video_annotation_dir(video_id, direction)
        filepath = (
            video_annotation_dir
            / "depth_estimation/MiDaS"
            / f"{video_id:04d}_{direction}_MiDaS.hdf5"
        )
        # read hdf5 file
        with h5py.File(filepath, "r") as f:
            return f["data"][:]

    def read_keypoint_detection(self, video_id: int, direction: str = "fw"):
        """
        Read and return keypoint detection data for a video.

        Parameters:
            video_id (int): Video identification number.
            direction (str): Video direction, default is "fw".

        Returns:
            numpy.ndarray: The keypoint detection data from the HDF5 file.
        """
        # temp : /tank/shared/2024/visual/AOT/derivatives/stimuli/annotations/0001_fw.mp4/keypoints/KeypointRCNN_ResNet50/0001_fw_KeypointRCNN_ResNet50.hdf5
        video_annotation_dir = self.get_video_annotation_dir(video_id, direction)
        filepath = (
            video_annotation_dir
            / "keypoints/KeypointRCNN_ResNet50"
            / f"{video_id:04d}_{direction}_KeypointRCNN_ResNet50.hdf5"
        )
        # read hdf5 file
        with h5py.File(filepath, "r") as f:
            return f["data"][:]

    def read_instance_segmentation(self, video_id: int, direction: str = "fw"):
        """
        Read and return instance segmentation data for a video.

        Parameters:
            video_id (int): Video identification number.
            direction (str): Video direction, default is "fw".

        Returns:
            numpy.ndarray: The segmentation data from the HDF5 file.
        """
        # temp : /tank/shared/2024/visual/AOT/derivatives/stimuli/annotations/0001_fw.mp4/instance_segmentation/MaskRCNN_ResNet50_FPN/0001_fw_MaskRCNN_ResNet50_FPN.hdf5
        video_annotation_dir = self.get_video_annotation_dir(video_id, direction)
        filepath = (
            video_annotation_dir
            / "instance_segmentation/MaskRCNN_ResNet50_FPN"
            / f"{video_id:04d}_{direction}_MaskRCNN_ResNet50_FPN.hdf5"
        )
        # read hdf5 file
        with h5py.File(filepath, "r") as f:
            return f["data"][:]

    def read_object_detection(self, video_id: int, direction: str = "fw"):
        """
        Read and return object detection data for a video.

        Parameters:
            video_id (int): Video identification number.
            direction (str): Video direction, default is "fw".

        Returns:
            numpy.ndarray: The object detection data from the HDF5 file.
        """
        # temp : /tank/shared/2024/visual/AOT/derivatives/stimuli/annotations/0001_fw.mp4/object_detection/fasterrcnn_resnet50_fpn_v2/0001_fw_fasterrcnn_resnet50_fpn_v2.hdf5
        video_annotation_dir = self.get_video_annotation_dir(video_id, direction)
        filepath = (
            video_annotation_dir
            / "object_detection/fasterrcnn_resnet50_fpn_v2"
            / f"{video_id:04d}_{direction}_fasterrcnn_resnet50_fpn_v2.hdf5"
        )
        # read hdf5 file
        with h5py.File(filepath, "r") as f:
            return f["data"][:]
