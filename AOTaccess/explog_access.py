import csv

from AOTaccess.config import Config


class ExpLogAccess:
    def __init__(self, root_dir=None, config=None):
        """Initialize the ExpLogAccess instance.

        Parameters:
            root_dir: If given, resolve paths relative to this dataset root.
            config (Config): An explicit Config; takes precedence over root_dir.
        """
        self.config = config if config is not None else Config(root_dir=root_dir)
        self.bids_dir = self.config.path("bids")

    def get_func_dir(self, sub: int, ses: int):
        """
        Get the functional directory for a specific subject and session.

        Parameters:
            sub (int): Subject number.
            ses (int): Session number.

        Returns:
            pathlib.Path: Path to the functional directory.
        """
        # Example: /.../sub-001/ses-01/func
        return self.bids_dir / f"sub-{sub:03d}" / f"ses-{ses:02d}" / "func"

    def read_events_tsv(self, sub: int, ses: int, run: int):
        """
        Read and return the events TSV file for a specific subject, session, and run.

        Parameters:
            sub (int): Subject number.
            ses (int): Session number.
            run (int): Run number.

        Returns:
            list of dict: List of rows read from the TSV file.
        """
        func_dir = self.get_func_dir(sub, ses)
        filepath = (
            func_dir / f"sub-{sub:03d}_ses-{ses:02d}_task-AOT_run-{run:02d}_events.tsv"
        )
        with open(filepath, "r") as f:
            return list(csv.DictReader(f, delimiter="\t"))

    def get_eyetrack_edf(self, sub: int, ses: int, run: int):
        """
        Load and return the eyetracking EDF file for a specific subject, session, and run.

        Parameters:
            sub (int): Subject number.
            ses (int): Session number.
            run (int): Run number.

        Returns:
            None: Function pending implementation.
        """
        func_dir = self.get_func_dir(sub, ses)
        filepath = (
            func_dir
            / f"sub-{sub:03d}_ses-{ses:02d}_task-AOT_run-{run:02d}_eyetrack.edf"
        )

        # ho = HDFEyeOperator()
        # ho.add_edf_file(filepath) #########################################################################################################################################################################
        return filepath

    def get_frames_pdf(self, sub: int, ses: int, run: int):
        """
        Get the path to the frames PDF for a specific subject, session, and run.

        Parameters:
            sub (int): Subject number.
            ses (int): Session number.
            run (int): Run number.

        Returns:
            pathlib.Path: Path to the frames PDF file.
        """
        func_dir = self.get_func_dir(sub, ses)
        filepath = (
            func_dir / f"sub-{sub:03d}_ses-{ses:02d}_task-AOT_run-{run:02d}_frames.pdf"
        )
        return filepath

    def read_lot_txt(self, sub: int, ses: int, run: int):
        """
        Read and return the log text file for a specific subject, session, and run.

        Parameters:
            sub (int): Subject number.
            ses (int): Session number.
            run (int): Run number.

        Returns:
            str: Content of the log file.
        """
        func_dir = self.get_func_dir(sub, ses)
        filepath = (
            func_dir / f"sub-{sub:03d}_ses-{ses:02d}_task-AOT_run-{run:02d}_log.txt"
        )
        with open(filepath, "r") as f:
            return f.read()

    def read_scanphyslog_log(self, sub: int, ses: int, run: int):
        """
        Read and return the scanphyslog file for a specific subject, session, and run.

        Parameters:
            sub (int): Subject number.
            ses (int): Session number.
            run (int): Run number.

        Returns:
            str: Content of the scanphyslog file.
        """
        func_dir = self.get_func_dir(sub, ses)
        filepath = (
            func_dir
            / f"sub-{sub:03d}_ses-{ses:02d}_task-AOT_run-{run:02d}_scanphyslog.log"
        )
        with open(filepath, "r") as f:
            return f.read()
