import AOTaccess
from pathlib import Path
import sys
import os
import yaml


class StimuliInfoAccess:
    def __init__(self, sub, ses):
        basedir = Path(__file__).resolve().parent
        settings = yaml.safe_load(open(basedir / "settings.yml"))
        self.video_dir = Path(settings["paths"]["videos"])
        self.video_annotation_dir = Path(settings["paths"]["video_annotations"])
        self.sub = sub
        self.ses = ses

    def get_video_path(self, video_id, direction="fw"):
        return self.video_dir / f"{video_id}_{direction}.mp4"

    def get_video_annotation_dir(
        self, video_id, direction="fw", annotation_type="semantic_segmentation"
    ):
        return (
            self.video_annotation_dir / f"{video_id}_{direction}.mp4" / annotation_type
        )

    def read_llama_description(self, video_id, direction="fw"):
        pass

    def read_sbert_embeddings(self, video_id, direction="fw"):
        pass

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
