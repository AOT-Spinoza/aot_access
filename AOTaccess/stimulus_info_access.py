import AOTaccess
from pathlib import Path
import sys
import os
import yaml
import numpy as np
import h5py
import csv


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

    def _temp_read_motion_energy_features(self, video_id: int, direction: str = "fw"):
        """
        Temporarily load motion energy features for a video.

        Parameters:
            video_id (int): Video identification number.
            direction (str): Video direction, default is "fw".

        Returns:
            numpy.ndarray: Loaded motion energy features.
        """
        temp_root_dir = Path(
            "/tank/shared/2024/visual/AOT/temp/motion_energy_features/video_features"
        )
        temp_file = temp_root_dir / f"{video_id:04d}_{direction}.npy"
        return np.load(temp_file)

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
