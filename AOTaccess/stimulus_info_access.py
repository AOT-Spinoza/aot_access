from pathlib import Path
import warnings
import numpy as np
import pandas as pd
import yaml
import h5py
import csv
import json

from AOTaccess.config import Config
from AOTaccess.errors import DataNotFoundError

# NOTE: `torch` is imported lazily inside the `_temp_*` methods that need it,
# so the rest of the API stays importable without that heavy dependency.


class StimuliInfoAccess:
    def __init__(self, root_dir=None, config=None):
        """Initialize the StimuliInfoAccess instance.

        Parameters:
            root_dir: If given, resolve paths relative to this dataset root.
            config (Config): An explicit Config; takes precedence over root_dir.
        """
        self.config = config if config is not None else Config(root_dir=root_dir)
        self.video_dir = self.config.path("videos")
        self.picture_dir = self.config.path("pictures")
        self.video_annotation_dir = self.config.path("video_annotations")
        # Lazy caches for the bulky cross-video annotation files.
        self._online_behavior = None
        self._moten_filter_info = {}

    # ------------------------------------------------------------------
    # cross-video annotations manifest
    # ------------------------------------------------------------------
    def annotations_manifest_dir(self):
        """Path to the cross-video annotations manifest folder.

        Holds the condensed online-behavior table, pymoten filter-bank
        metadata, and per-annotation-pipeline descriptions (qwen, …).
        """
        return self.video_annotation_dir / "manifest"

    def read_online_behavior_table(self, video=None, direction=None):
        """The condensed per-video online-behavior table.

        Returns a :class:`pandas.DataFrame` with one row per (video,
        direction) — identifiability score (+ CI), direction accuracy
        (raw and quality-weighted), mean confidence and RT, decile, and a
        ``yaml_path`` pointing at the per-video detail file (see
        :meth:`read_video_behavior`). Cached after the first load.

        Parameters:
            video (int): Filter to one ``source_id``.
            direction (str): Filter to one direction (``"fw"`` / ``"rv"``).
        """
        if self._online_behavior is None:
            path = self.annotations_manifest_dir() / "online_behavior.tsv"
            if not path.exists():
                raise DataNotFoundError(
                    f"Online-behavior table not found: {path}"
                )
            self._online_behavior = pd.read_csv(path, sep="\t")
        df = self._online_behavior
        if video is not None:
            df = df[df.source_id == int(video)]
        if direction is not None:
            mapped = {"fw": "forward", "rv": "backward"}.get(direction, direction)
            df = df[df.direction == mapped]
        return df.reset_index(drop=True)

    def read_video_behavior(self, video_id: int, direction: str = "fw"):
        """The detailed per-video online-behavior YAML.

        Returns a dict with ``video``, ``summary``, ``source_context`` and
        ``responses`` — one entry per online subject (response direction,
        confidence, RTs, subject quality weight, included flag, …).
        """
        path = (
            self.get_video_annotation_dir(video_id, direction)
            / "behavior"
            / "online_behavior.yaml"
        )
        if not path.exists():
            raise DataNotFoundError(
                f"Per-video behavior YAML not found: {path}"
            )
        with open(path) as f:
            return yaml.safe_load(f)

    def read_qwen_description_meta(self):
        """Metadata about the qwen_description annotation pipeline."""
        return self._read_manifest_yaml("qwen_description.yml")

    def read_qwen_embedding_meta(self):
        """Metadata about the qwen_embedding annotation pipeline."""
        return self._read_manifest_yaml("qwen_embedding.yml")

    # Manifest file per bank. The source banks were renamed with the
    # ``source_`` prefix; the pre-rename names are still accepted while the
    # rollout completes.
    _MOTEN_MANIFEST_NAMES = {
        "source_32hz": "moten_filter_info_source_32.yml",
        "source_16hz": "moten_filter_info_source_16.yml",
        "display": "moten_filter_info_display.yml",
    }
    _MOTEN_MANIFEST_PRE_RENAME = {
        "source_32hz": "moten_filter_info_32.yml",
        "source_16hz": "moten_filter_info_16.yml",
    }

    def read_moten_filter_info(self, highest_freq=None, bank=None):
        """Pymoten filter-bank info for one bank.

        Returns a dict with ``meta`` (filter-bank parameters; ``n_filters``
        is the channel count of the per-frame motion-energy array),
        ``dva_alignment`` (image-to-degrees mapping) and ``filters`` — one
        entry per filter. For the legacy ``source_*`` banks the per-filter
        coordinates are the historical source-frame alignment; for the
        ``display`` bank they are already physical (``x_deg``, ``y_deg``,
        ``sf_cpd``, ``direction_phys_deg``, ...). Cached per bank.

        Parameters:
            highest_freq (int): 16 or 32 — legacy bank selector, ignored when
                ``bank`` is given.
            bank (str | None): ``"display"``, ``"source_32hz"``,
                ``"source_16hz"``, or a deprecated alias. ``None`` keeps the
                historical behaviour and warns.
        """
        canonical = self.resolve_motion_energy_bank(bank=bank,
                                                    highest_freq=highest_freq,
                                                    direction="fw")
        key = canonical
        if key not in self._moten_filter_info:
            manifest_dir = self.annotations_manifest_dir()
            path = manifest_dir / self._MOTEN_MANIFEST_NAMES[canonical]
            if not path.exists():
                pre = self._MOTEN_MANIFEST_PRE_RENAME.get(canonical)
                if pre is not None and (manifest_dir / pre).exists():
                    warnings.warn(
                        f"{canonical} manifest still under its pre-rename name "
                        f"{pre!r}; this transitional fallback will be removed.",
                        DeprecationWarning,
                        stacklevel=3,
                    )
                    path = manifest_dir / pre
                else:
                    raise DataNotFoundError(
                        f"Pymoten filter info not found for bank "
                        f"{canonical!r}: {path}"
                    )
            with open(path) as f:
                self._moten_filter_info[key] = yaml.safe_load(f)
        return self._moten_filter_info[key]

    def available_annotations(self, video_id: int, direction: str = "fw"):
        """Annotation kinds available for one (video, direction)."""
        d = self.get_video_annotation_dir(video_id, direction)
        if not d.exists():
            return []
        return sorted(p.name for p in d.iterdir() if p.is_dir())

    def _read_manifest_yaml(self, name):
        """Load one YAML from the annotations manifest folder."""
        path = self.annotations_manifest_dir() / name
        if not path.exists():
            raise DataNotFoundError(
                f"Annotations manifest file not found: {path}"
            )
        with open(path) as f:
            return yaml.safe_load(f)

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
    
    def read_qwen_description(self, video_id: int, direction: str = "fw"):
        """
        Read and return the Qwen description text for a video.

        Parameters:
            video_id (int): Video identification number.
            direction (str): Video direction, default is "fw".

        Returns:
            str: Content of the description text file.
        """
        video_annotation_dir = self.get_video_annotation_dir(video_id, direction)
        filepath = (
            video_annotation_dir
            / "qwen_description"
            / f"{video_id:04d}_{direction}.txt"
        )
        with open(filepath, "r") as f:
            return f.read()
         
    def read_qwen_embedding(self, video_id: int, direction: str = "fw"):
        """
        Read and return the Qwen embedding for a video.

        Parameters:
            video_id (int): Video identification number.
            direction (str): Video direction, default is "fw".

        Returns:
            numpy.ndarray: Qwen embedding array.
        """
        video_annotation_dir = self.get_video_annotation_dir(video_id, direction)
        filepath = (
            video_annotation_dir
            / "qwen_embedding"
            / f"{video_id:04d}_{direction}_embedding.json"
        )
        with open(filepath, "r") as f:
            data = json.load(f)
        embedding = data["data"][0]["embedding"]
        return np.array(embedding)


    def read_sbert_embeddings(self, video_id: int, direction: str = "fw"):
        """
        Read and return SBERT embeddings for a video.

        Parameters:
            video_id (int): Video identification number.
            direction (str): Video direction, default is "fw".

        Returns:
            numpy.ndarray: Loaded SBERT embeddings.
        """
        video_annotation_dir = self.get_video_annotation_dir(video_id, direction)
        filepath = (
            video_annotation_dir
            / "sbert_embeddings"
            / f"{video_id:04d}_{direction}.npy"
        )
        return np.load(filepath)

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
            "/research/FGB-CognitivePsychology-Knapen/shared/2024/visual/AOT/derivatives/DLoutputs/sbert_all-mpnet-base-v2/pca_embeddings"
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
            "/research/FGB-CognitivePsychology-Knapen/shared/2024/visual/AOT/derivatives/DLoutputs/sbert_all-mpnet-base-v2/sae_embeddings"
        )
        temp_file = temp_root_dir / f"{video_id:04d}_{direction}.npy"
        return np.load(temp_file)

    # ------------------------------------------------------------------
    # motion-energy features
    # ------------------------------------------------------------------
    #
    # Storage transition: per-(video, direction, rate) the features now
    # live in an HDF5 file ``{video:04d}_{direction}.h5`` next to the
    # legacy ``.npy``. The HDF5 carries two datasets at root level:
    #
    #   /motion_energy          — per-frame, shape (n_frames, n_filters)
    #                             dtype float32; already log-compressed
    #                             (pymoten ``pointwise_nonlinearity="log"``
    #                             style — values can be slightly negative
    #                             when |z|² < 1).
    #   /motion_energy_summary  — per-video, shape (n_filters,)
    #                             dtype float32; temporal mean of the
    #                             per-frame array (Nishimoto / Gallant-lab
    #                             canonical pooling: compress once, then
    #                             average).
    #
    # File-level attrs: ``git_hash`` (conversion provenance) and
    # ``highest_freq`` (16 or 32).
    #
    # The 32-Hz HDF5 conversion is still in progress at the time of
    # writing — :meth:`read_motion_energy_features` prefers ``.h5`` and
    # falls back to the legacy ``.npy`` with a one-time
    # :class:`DeprecationWarning` so existing analyses keep running.
    # :meth:`read_motion_energy_summary` is HDF5-only (no legacy form
    # exists) and raises :class:`DataNotFoundError` until the file (or its
    # ``/motion_energy_summary`` dataset) appears.

    # ---- bank registry ---------------------------------------------------
    #
    # A "bank" is one filter bank + geometry version. The directory under
    # ``motion_energy/`` names it:
    #
    #   source_32hz / source_16hz : legacy, features computed on the SOURCE
    #       video frame (1536x1080, aspect 16:9). Physically anisotropic.
    #   display : physically corrected, computed on the displayed geometry
    #       (1075.2x756 display px, aspect 64/45). Currently fw only.
    #
    # The historical directory names ``32hz`` / ``16hz`` are still accepted
    # while the rename rolls out, and the historical ids remain valid via
    # aliases (with a DeprecationWarning).
    _ME_BANKS = ("display", "source_32hz", "source_16hz")
    _ME_BANK_ALIASES = {"32hz": "source_32hz", "16hz": "source_16hz"}
    _ME_BANK_PRE_RENAME_DIRS = {"source_32hz": "32hz", "source_16hz": "16hz"}

    #: Bank returned when the caller does not ask for one.
    #: ``display`` is the physically-correct bank and the project default.
    _ME_DEFAULT_BANK = "display"
    #: rv has not been migrated to ``display``; forward reads fall back to the
    #: legacy 16-Hz source bank (the only complete rv set) with a warning.
    _ME_RV_FALLBACK_BANK = "source_16hz"

    def resolve_motion_energy_bank(self, bank=None, highest_freq=None,
                                   direction="fw") -> str:
        """Return the canonical bank id.

        Default behaviour (``bank=None``):

        * ``direction="fw"`` -> the **display** bank, i.e. the physically
          corrected features. This is the project default since 2026-11-11.
        * ``direction="rv"`` -> falls back to ``source_16hz`` with a warning,
          because rv has not been migrated yet.
        * passing ``highest_freq=16/32`` keeps the historical legacy bank for
          that ladder (with a warning) - the explicit escape hatch for
          reproducing pre-migration numbers.
        """
        if bank is None:
            if highest_freq is not None:
                if highest_freq not in (16, 32):
                    raise ValueError(
                        f"highest_freq must be 16 or 32; got {highest_freq!r}"
                    )
                canonical = f"source_{highest_freq}hz"
                warnings.warn(
                    f"highest_freq={highest_freq} selects the legacy source-frame "
                    f"bank ({canonical!r}). This is only needed to reproduce "
                    "pre-migration results; pass bank='display' for the "
                    "physically corrected features.",
                    DeprecationWarning,
                    stacklevel=3,
                )
                return canonical
            if direction != "fw":
                warnings.warn(
                    f"the display motion-energy bank has no {direction!r} features "
                    f"yet; falling back to the legacy {self._ME_RV_FALLBACK_BANK!r}.",
                    DeprecationWarning,
                    stacklevel=3,
                )
                return self._ME_RV_FALLBACK_BANK
            return self._ME_DEFAULT_BANK
        if bank in self._ME_BANK_ALIASES:
            canonical = self._ME_BANK_ALIASES[bank]
            warnings.warn(
                f"motion-energy bank {bank!r} is deprecated; use {canonical!r}.",
                DeprecationWarning,
                stacklevel=3,
            )
            return canonical
        if bank not in self._ME_BANKS:
            raise ValueError(
                f"unknown motion-energy bank {bank!r}; expected one of "
                f"{list(self._ME_BANKS)} (aliases: {sorted(self._ME_BANK_ALIASES)})"
            )
        return bank

    def _motion_energy_bank_dir(
        self, video_id: int, direction: str, canonical: str
    ) -> Path:
        """Directory holding one bank's features, honouring the rename rollout."""
        base = self.get_video_annotation_dir(video_id, direction) / "motion_energy"
        path = base / canonical
        if path.is_dir():
            return path
        pre = self._ME_BANK_PRE_RENAME_DIRS.get(canonical)
        if pre is not None and (base / pre).is_dir():
            warnings.warn(
                f"{canonical} is still stored under the pre-rename directory "
                f"name {pre!r}; this transitional fallback will be removed.",
                DeprecationWarning,
                stacklevel=4,
            )
            return base / pre
        return path

    def _motion_energy_h5_path(
        self, video_id: int, direction: str, highest_freq=None,
        bank=None
    ) -> Path:
        """Path to the per-(video, direction, bank) HDF5."""
        canonical = self.resolve_motion_energy_bank(bank=bank,
                                                    highest_freq=highest_freq,
                                                    direction=direction)
        return (self._motion_energy_bank_dir(video_id, direction, canonical)
                / f"{video_id:04d}_{direction}.h5")

    def _motion_energy_npy_path(
        self, video_id: int, direction: str, highest_freq=None,
        bank=None
    ) -> Path:
        """Path to the legacy per-frame NPY (source banks only)."""
        canonical = self.resolve_motion_energy_bank(bank=bank,
                                                   highest_freq=highest_freq,
                                                   direction=direction)
        return (self._motion_energy_bank_dir(video_id, direction, canonical)
                / f"{video_id:04d}_{direction}.npy")

    def read_motion_energy_features(
        self,
        video_id: int,
        direction: str = "fw",
        highest_freq=None,
        bank=None,
    ) -> np.ndarray:
        """Per-frame motion-energy features for one (video, direction, bank).

        Shape ``(n_frames, n_filters)``, dtype ``float32`` — the
        log-compressed pymoten output, one channel per filter in the bank
        described by :meth:`read_moten_filter_info`. ``n_frames`` is 60 or
        61 (depends on the source clip duration); ``n_filters`` matches
        ``read_moten_filter_info(...)["meta"]["n_filters"]``.

        Banks:
            ``"display"``
                physically corrected features on the displayed geometry
                (9085 channels). Currently ``fw`` only — ``rv`` raises.
                **Preferred for new analyses.**
            ``"source_32hz"`` / ``"source_16hz"``
                legacy features on the source video frame (11845 / 2530
                channels, physically anisotropic). Kept for compatibility.
            ``None``
                historical behaviour: the legacy bank picked by
                ``highest_freq``; emits a :class:`DeprecationWarning`.

        Reads the HDF5 ``/motion_energy`` dataset when present and falls back
        to the legacy ``.npy`` for the source banks only.

        Parameters:
            video_id (int): Video identification number.
            direction (str): ``"fw"`` or ``"rv"``.
            highest_freq (int): Legacy bank selector, 16 or 32 (ignored when
                ``bank`` is given).
            bank (str | None): ``"display"``, ``"source_32hz"``,
                ``"source_16hz"``, or a deprecated alias ``"32hz"``/``"16hz"``.

        Raises:
            DataNotFoundError: The requested bank has no features for this
                video (including ``display`` + ``rv``, which is not migrated).
        """
        canonical = self.resolve_motion_energy_bank(bank=bank,
                                                    highest_freq=highest_freq,
                                                    direction=direction)
        if canonical == "display" and direction != "fw":
            raise DataNotFoundError(
                f"motion-energy bank 'display' has no {direction!r} features yet "
                f"(the display bank is fw-only in this version). Use "
                f"bank='source_16hz' for legacy {direction!r} data."
            )
        h5_path = self._motion_energy_h5_path(video_id, direction, highest_freq,
                                              bank=canonical)
        if h5_path.exists():
            with h5py.File(h5_path, "r") as f:
                if "motion_energy" not in f:
                    raise DataNotFoundError(
                        f"Motion-energy HDF5 missing /motion_energy dataset: "
                        f"{h5_path}"
                    )
                return f["motion_energy"][...]
        npy_path = self._motion_energy_npy_path(video_id, direction, highest_freq,
                                                bank=canonical)
        if npy_path.exists() and canonical != "display":
            warnings.warn(
                f"Reading legacy .npy motion-energy at {npy_path}; will be "
                f"removed once the HDF5 conversion completes.",
                DeprecationWarning,
                stacklevel=2,
            )
            return np.load(npy_path)
        hint = ""
        if canonical != "display":
            if self._motion_energy_bank_dir(
                video_id, direction, "display").is_dir():
                hint = " (display-bank data exists for this video — try bank='display')"
        raise DataNotFoundError(
            f"Motion-energy file not found for video={video_id}, "
            f"direction={direction!r}, bank={canonical!r}: "
            f"tried {h5_path} and {npy_path}{hint}"
        )

    def read_motion_energy_summary(
        self, video_id: int, direction: str = "fw", highest_freq=None,
        bank=None,
    ) -> np.ndarray:
        """Per-video motion-energy summary for one (video, direction, bank).

        Shape ``(n_filters,)``, dtype ``float32`` — the temporal mean of
        the (already log-compressed) per-frame array. This is the
        Nishimoto / Gallant-lab canonical aggregation: compress once
        (already done upstream by pymoten), then average over time.

        Reads ``/motion_energy_summary`` from the per-(video, direction,
        bank) HDF5. No legacy ``.npy`` form exists — this method is the
        HDF5-only entry point.

        Parameters:
            video_id (int): Video identification number.
            direction (str): ``"fw"`` or ``"rv"``.
            highest_freq (int): Legacy bank selector, 16 or 32 (ignored when
                ``bank`` is given).
            bank (str | None): see :meth:`read_motion_energy_features`.

        Raises:
            DataNotFoundError: Either the HDF5 file is missing or the
                ``/motion_energy_summary`` dataset has not been written yet
                (the conversion may still be in progress).
        """
        canonical = self.resolve_motion_energy_bank(bank=bank,
                                                    highest_freq=highest_freq,
                                                    direction=direction)
        if canonical == "display" and direction != "fw":
            raise DataNotFoundError(
                f"motion-energy bank 'display' has no {direction!r} features yet."
            )
        h5_path = self._motion_energy_h5_path(video_id, direction, highest_freq,
                                              bank=canonical)
        if not h5_path.exists():
            raise DataNotFoundError(
                f"Motion-energy HDF5 not found for video={video_id}, "
                f"direction={direction!r}, bank={canonical!r}: "
                f"{h5_path}"
            )
        with h5py.File(h5_path, "r") as f:
            if "motion_energy_summary" not in f:
                raise DataNotFoundError(
                    f"/motion_energy_summary dataset not present in {h5_path} "
                    f"(per-video summary is part of the in-progress HDF5 "
                    f"conversion)."
                )
            return f["motion_energy_summary"][...]

    def _temp_load_vae_latent(self, latent_file: Path, kind: str = "VAE"):
        import torch

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
        import torch

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
        import torch

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
        # temp : /research/FGB-CognitivePsychology-Knapen/shared/2024/visual/AOT/derivatives/stimuli/annotations/0001_fw.mp4/semantic_segmentation/FCN_ResNet101/0001_fw_FCN_ResNet101.hdf5
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
        # temp : /research/FGB-CognitivePsychology-Knapen/shared/2024/visual/AOT/derivatives/stimuli/annotations/0001_fw.mp4/action_detection/slowfast_r50_detection/0001_fw_slowfast_r50_detection.hdf5
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
        # temp : /research/FGB-CognitivePsychology-Knapen/shared/2024/visual/AOT/derivatives/stimuli/annotations/0003_rv.mp4/action_classification/X3D/0003_rv.mp4_X3D.csv
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
        # temp : /research/FGB-CognitivePsychology-Knapen/shared/2024/visual/AOT/derivatives/stimuli/annotations/0011_fw.mp4/captioning/GIT/0011_fw.mp4_GIT.csv
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
        # temp : /research/FGB-CognitivePsychology-Knapen/shared/2024/visual/AOT/derivatives/stimuli/annotations/0011_fw.mp4/depth_estimation/MiDaS/0011_fw.mp4_MiDaS.hdf5
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
        # temp : /research/FGB-CognitivePsychology-Knapen/shared/2024/visual/AOT/derivatives/stimuli/annotations/0001_fw.mp4/keypoints/KeypointRCNN_ResNet50/0001_fw_KeypointRCNN_ResNet50.hdf5
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
        # temp : /research/FGB-CognitivePsychology-Knapen/shared/2024/visual/AOT/derivatives/stimuli/annotations/0001_fw.mp4/instance_segmentation/MaskRCNN_ResNet50_FPN/0001_fw_MaskRCNN_ResNet50_FPN.hdf5
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
        # temp : /research/FGB-CognitivePsychology-Knapen/shared/2024/visual/AOT/derivatives/stimuli/annotations/0001_fw.mp4/object_detection/fasterrcnn_resnet50_fpn_v2/0001_fw_fasterrcnn_resnet50_fpn_v2.hdf5
        video_annotation_dir = self.get_video_annotation_dir(video_id, direction)
        filepath = (
            video_annotation_dir
            / "object_detection/fasterrcnn_resnet50_fpn_v2"
            / f"{video_id:04d}_{direction}_fasterrcnn_resnet50_fpn_v2.hdf5"
        )
        # read hdf5 file
        with h5py.File(filepath, "r") as f:
            return f["data"][:]
