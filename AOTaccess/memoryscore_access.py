import AOTaccess
from pathlib import Path
import sys
import os
import yaml
import csv
from AOTaccess.expdesign_access import ExpDesignAccess


basedir = Path(__file__).resolve().parent
settings = yaml.safe_load(open(basedir / "settings.yml"))


class MemoryScoreAccess:
    def __init__(self):
        """
        Initialize the MemoryScoreAccess instance.

        Sets up the bids directory from the settings.

        Parameters:
            None

        Returns:
            None
        """
        self.bids_dir = Path(settings["paths"]["bids"])
        pass

    def get_memory_dir(self, sub: int, ses: int):
        """
        Get the memory directory for a specific subject and session.

        Parameters:
            sub (int): Subject number.
            ses (int): Session number.

        Returns:
            pathlib.Path: Path to the memory directory.
        """
        sub = str(sub).zfill(3)
        ses = str(ses).zfill(2)
        memory_dir = self.bids_dir / f"sub-{sub}/ses-{ses}/beh"
        return memory_dir

    def read_memory_csv(self, sub: int, ses: int):
        """
        Read the memory CSV file for a specific subject and session.

        Parameters:
            sub (int): Subject number.
            ses (int): Session number.

        Returns:
            list of dict: List of rows read from the CSV file.
        """
        memory_dir = self.get_memory_dir(sub, ses)
        sub = str(sub).zfill(3)
        ses = str(ses).zfill(2)
        run = str(1).zfill(2)
        filename = f"sub-{sub}_ses-{ses}_task-memory_run-{run}_output.csv"
        filepath = memory_dir / filename
        with open(filepath, "r") as f:
            return list(csv.DictReader(f))

    def read_memory_events_tsv(self, sub: int, ses: int):
        """
        Read the memory events TSV file for a specific subject and session.

        Parameters:
            sub (int): Subject number.
            ses (int): Session number.

        Returns:
            list of dict: List of rows read from the TSV file.
        """
        memory_dir = self.get_memory_dir(sub, ses)
        sub = str(sub).zfill(3)
        ses = str(ses).zfill(2)
        run = str(1).zfill(2)
        filename = f"sub-{sub}_ses-{ses}_task-memory_run-{run}_events.tsv"
        filepath = memory_dir / filename
        with open(filepath, "r") as f:
            return list(csv.DictReader(f, delimiter="\t"))

    def read_memory_csv_cleaned(self, sub: int, ses: int):
        """
        Read and clean the memory CSV file.

        Cleans file names and responses:
          - Extracts video index from a picture file path.
          - Transforms response ('j' to True, 'k' to False, otherwise None).

        Parameters:
            sub (int): Subject number.
            ses (int): Session number.

        Returns:
            list of dict: List of dictionaries with "video_index" and "response".
        """

        def clean_file_name(file_name):
            # Extracts basename and splits to get video index.
            return os.path.basename(file_name).split("_")[0]

        def clean_response(response):
            # Converts specific key responses to boolean.
            if response == "j":
                return True
            elif response == "k":
                return False
            else:
                return None

        memory_csv = self.read_memory_csv(sub, ses)
        memory_csv_cleaned = []
        for row in memory_csv:
            original_picture_file = row[""]
            original_response = row["0"]
            video_index = clean_file_name(original_picture_file)
            response = clean_response(original_response)
            memory_csv_cleaned.append(
                {"video_index": video_index, "response": response}
            )

        return memory_csv_cleaned

    def read_memory_edf(self, sub: int, ses: int):
        """
        Read the eyetracking EDF file for a specific subject and session.

        Parameters:
            sub (int): Subject number.
            ses (int): Session number.

        Returns:
            None (Functionality pending implementation).
        """
        memory_dir = self.get_memory_dir(sub, ses)
        sub = str(sub).zfill(3)
        ses = str(ses).zfill(2)
        run = str(1).zfill(2)
        filename = f"sub-{sub}_ses-{ses}_task-memory_run-{run}_eyetrack.edf"
        filepath = memory_dir / filename
        pass

    def memorability_list_from_session(self, sub: int, ses: int):
        """
        Create a list of memorability responses for a given subject and session.

        Filters memory responses based on the session's unique video indexes.

        Parameters:
            sub (int): Subject number.
            ses (int): Session number.

        Returns:
            list of dict: Each item contains "video_index" and "response"
                           for videos with valid responses.
        """
        expdesignaccess = ExpDesignAccess()

        session_uniqe_video_indexes = expdesignaccess.get_session_uniqe_video_indexes(
            sub, ses
        )
        memory_csv = self.read_memory_csv_cleaned(sub, ses)
        memorability_list = []
        for row in memory_csv:
            video_index = row["video_index"]
            response = row["response"]
            if response is not None:
                if video_index in session_uniqe_video_indexes:
                    memorability_list.append(
                        {"video_index": video_index, "response": response}
                    )

        print(
            f"memorability_list length for sub {sub} ses {ses}: {len(memorability_list)}"
        )
        return memorability_list

    def memorability_list_from_all_sessions(self, sub: int):
        """
        Create a memorability list combining all sessions for a specific subject.

        Parameters:
            sub (int): Subject number.

        Returns:
            list: Combined memorability entries from all sessions (pending implementation).
        """
        pass

    def memorability_result_per_video(self, sub: int, video_index: int):
        """
        Retrieve the memorability result for a specific video from all sessions.

        Parameters:
            sub (int): Subject number.
            video_index (int): Video index to retrieve its response.

        Returns:
            bool or None: The memorability response for the video,
                          or None if not found.
        """
        memorability_list = self.memorability_list_from_all_sessions(sub)
        for row in memorability_list:
            if row["video_index"] == video_index:
                return row["response"]
