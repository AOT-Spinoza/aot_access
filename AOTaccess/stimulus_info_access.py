import AOTaccess
from pathlib import Path
import sys
import os
import yaml
import numpy as np


class StimuliInfoAccess:
    def __init__(self):
        basedir = Path(__file__).resolve().parent
        settings = yaml.safe_load(open(basedir / "settings.yml"))
        self.video_dir = Path(settings["paths"]["videos"])
        self.video_annotation_dir = Path(settings["paths"]["video_annotations"])

    def get_video_path(self, video_id, direction="fw"):
        return self.video_dir / f"{video_id:04d}_{direction}.mp4"

    def get_video_annotation_dir(
        self, video_id, direction="fw", annotation_type="semantic_segmentation"
    ):
        return (
            self.video_annotation_dir
            / f"{video_id:04d}_{direction}.mp4"
            / annotation_type
        )

    def _temp_read_llama_description(self, video_id, direction="fw"):
        # example : /tank/shared/2024/visual/AOT/derivatives/DLoutputs/videollama_describe/simple_describe_en_clean/0001_fw.txt
        temp_root_dir = Path(
            "/tank/shared/2024/visual/AOT/derivatives/DLoutputs/videollama_describe/simple_describe_en_clean"
        )
        temp_file = temp_root_dir / f"{video_id:04d}_{direction}.txt"
        with open(temp_file, "r") as f:
            return f.read()

    def _temp_read_sbert_embeddings(self, video_id, direction="fw"):
        # example : /tank/shared/2024/visual/AOT/derivatives/DLoutputs/sbert/simple_describe_en_clean_embeddings/0001_fw.npy
        temp_root_dir = Path(
            "/tank/shared/2024/visual/AOT/derivatives/DLoutputs/sbert/simple_describe_en_clean_embeddings"
        )
        temp_file = temp_root_dir / f"{video_id:04d}_{direction}.npy"
        return np.load(temp_file)

    def read_semantic_segmentation(self, video_id, direction="fw"):
        pass

    def read_action_detection(self, video_id, direction="fw"):
        pass

    def read_action_classification(self, video_id, direction="fw"):
        pass

    def read_captioning(self, video_id, direction="fw"):
        pass

    def read_depth_estimation(self, video_id, direction="fw"):
        pass

    def read_keypoint_detection(self, video_id, direction="fw"):
        pass

    def read_instance_segmentation(self, video_id, direction="fw"):
        pass

    def read_object_detection(self, video_id, direction="fw"):
        pass
