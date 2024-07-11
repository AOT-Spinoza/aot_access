import AOTaccess
from pathlib import Path
import sys
import os
import yaml

basedir = Path(__file__).resolve().parent
settings = yaml.safe_load(open(basedir / 'settings.yml'))
video_dir = Path(settings['paths']['videos'])
video_annotation_dir = Path(settings['paths']['video_annotations'])
print(video_dir)

def get_video_path(video_id,direction='fw'): #fw and rv
    return video_dir / f'{video_id}_{direction}.mp4'

def get_video_annotation_dir(video_id,direction='fw',annotation_type = "semantic_segmentation"): #fw and rv
    return video_annotation_dir / f'{video_id}_{direction}.mp4' / annotation_type





