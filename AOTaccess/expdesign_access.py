import AOTaccess
from pathlib import Path
import sys
import os
import yaml


class ExpDesignAccess:
    def __init__(self, root_dir: Path = None):
        """
        Initialize the ExpDesignAccess instance.

        Loads the experiment design directory and run number from the settings.

        Parameters:
            None

        Returns:
            None
        """
        if root_dir is not None:
            self.root_expdesign_dir = root_dir / "expdesign"
        else:
            basedir = Path(__file__).resolve().parent
            settings = yaml.safe_load(open(basedir / "settings.yml"))
            self.root_expdesign_dir = Path(settings["paths"]["AOTdesignsettings"])
            self.run_number = settings["parameters"]["run_number"]

    def read_expdesign_file(self, sub: int, ses: int, run: int):
        """
        Read the experiment design file for a specific subject, session, and run.

        Parameters:
            sub (int): Subject number.
            ses (int): Session number.
            run (int): Run number.

        Returns:
            dict: The parsed experiment design settings.
        """
        expdesign_file = (
            self.root_expdesign_dir
            / f"experiment_settings_sub_{sub:02d}_ses_{ses:02d}_run_{run:02d}.yml"
        )

        expdesign = yaml.safe_load(open(expdesign_file))
        print(f"Loaded expdesign from {expdesign_file}")
        return expdesign

    def read_session_expdesign(self, sub: int, ses: int):
        """
        Read the experiment design for all runs in a specific session for a subject.

        Parameters:
            sub (int): Subject number.
            ses (int): Session number.

        Returns:
            list: List of movie file settings for each run in the session.
        """
        run_number = self.run_number
        session_expdesign = [
            self.read_expdesign_file(sub, ses, run) for run in range(1, run_number + 1)
        ]
        sessions_movies = [
            settings["stimuli"]["movie_files"] for settings in session_expdesign
        ]
        print(f"Loaded expdesign for session {ses} of subject {sub}")
        return sessions_movies

    def append_all_trials_without_blanks(self, sub: int, ses: int):
        """
        Append and return all trials without blanks for a specific subject and session.

        Parameters:
            sub (int): Subject number.
            ses (int): Session number.

        Returns:
            list: A list of trials (movie files) where the entry is not "blank".
        """
        session_trails_without_blanks = []
        for run in range(1, self.run_number + 1):
            expdesign = self.read_expdesign_file(sub, ses, run)
            trials = expdesign["stimuli"]["movie_files"]
            trails_without_blanks = [trial for trial in trials if trial != "blank"]
            session_trails_without_blanks.extend(trails_without_blanks)
        print(
            f"Appended all trails without blanks, length: {len(session_trails_without_blanks)}"
        )

        return session_trails_without_blanks

    def get_session_video_indexes(self, sub: int, ses: int):
        """
        Get the list of video indexes for all trials in a session.

        Parameters:
            sub (int): Subject number.
            ses (int): Session number.

        Returns:
            list of str: Video indexes extracted from the movie file names.
        """
        sessions_movies = self.append_all_trials_without_blanks(sub, ses)
        video_indexes = [movie_name.split("_")[0] for movie_name in sessions_movies]
        print(
            f"Got video indexes for session {ses} of subject {sub}, length: {len(video_indexes)}"
        )
        return video_indexes

    def get_session_uniqe_video_indexes(self, sub: int, ses: int):
        """
        Get the unique video indexes for a session. (none repeat video indexes without direction)

        Parameters:
            sub (int): Subject number.
            ses (int): Session number.

        Returns:
            list of str: A list of unique video indexes.
        """
        sessions_movies = self.append_all_trials_without_blanks(sub, ses)
        video_indexes = [movie_name.split("_")[0] for movie_name in sessions_movies]
        unique_video_indexes = list(set(video_indexes))
        print(
            f"Got unique video indexes for session {ses} of subject {sub}, length: {len(unique_video_indexes)}"
        )
        return unique_video_indexes

    def get_session_id_from_video_id(sub: int, video_id: int):
        """
        (Pending Implementation) Get the session id from a given video id.

        Parameters:
            sub (int): Subject number.
            video_id (int): Video id.

        Returns:
            None: Function pending implementation.
        """
        # Implementation pending...
        pass
