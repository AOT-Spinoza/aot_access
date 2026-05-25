"""``AOTSubject`` — the primary user-facing access object for one subject.

Binds a single subject id once and exposes a flat-voxel API anchored by a
per-subject brain mask. Composes the per-domain access classes (GLMsingle,
BIDS, ROI, ExpDesign, Preproc) plus the brain/discovery helpers, so callers
stop threading ``sub=...`` through every call:

    sub = AOTSubject(1)
    betas = sub.get_betas(ses=1, roi="V1v", nc_threshold=0.2)     # (n_trials, n_vox)
    run   = sub.get_run_betas(ses=1, run=1, roi="V1v")            # (72, n_vox)
    sub.to_nifti(prediction, "pred.nii.gz", roi="V1v")
"""

import re

import numpy as np
import pandas as pd

from AOTaccess import discovery
from AOTaccess.bids_access import BidsAccess
from AOTaccess.brain import compute_brain_mask, get_voxel_coordinates, to_nifti
from AOTaccess.config import Config
from AOTaccess.errors import DataNotFoundError
from AOTaccess.expdesign_access import ExpDesignAccess
from AOTaccess.glmsingle_access import GLMSingleAccess
from AOTaccess.preproced_access import PreprocedAccess
from AOTaccess.roi_access import ROIAccess


# matches the trailing "NNNN_fw.mp4" or "NNNN_rv.mp4" in an events-tsv movie_file
_MOVIE_RE = re.compile(r"(\d{4})_(fw|rv)\.mp4$")


class AOTSubject:
    """Per-subject access object for the AOT dataset."""

    def __init__(self, sub, config=None, resolution="2p0mm",
                 glmtype="TYPED_FITHRF_GLMDENOISE_RR"):
        """
        Parameters:
            sub (int | str): Subject identifier (e.g. ``1`` or ``"sub-001"``).
            config (Config): An explicit Config; otherwise default settings.
            resolution (str): EPI/T1w grid resolution, default ``"2p0mm"``.
            glmtype (str): GLMsingle model entity, default the full RR model.
        """
        self.sub = sub
        self.resolution = resolution
        self.glmtype = glmtype
        self.config = config if config is not None else Config()
        # Sub-accessors share the same Config.
        self.glmsingle = GLMSingleAccess(config=self.config)
        self.bids = BidsAccess(config=self.config)
        self.roi = ROIAccess(config=self.config)
        self.expdesign = ExpDesignAccess(config=self.config)
        self.preproced = PreprocedAccess(config=self.config)
        # Lazy caches.
        self._brain_mask = None
        self._affine = None
        self._header = None
        self._trial_table = None

    # ------------------------------------------------------------------
    # discovery (subject-scoped)
    # ------------------------------------------------------------------
    def sessions(self):
        """Sessions with main-task GLMsingle outputs (sorted)."""
        return discovery.sessions(self.sub, config=self.config)

    def runs(self, ses):
        """Runs present for one session."""
        return discovery.runs(self.sub, ses, config=self.config)

    def videos(self, direction="fw"):
        """Unique video ids with per-video betas for this subject."""
        return discovery.videos(
            self.sub, direction=direction,
            resolution=self.resolution, config=self.config,
        )

    # ------------------------------------------------------------------
    # brain geometry
    # ------------------------------------------------------------------
    def get_brain_mask(self):
        """Boolean 3-D brain mask for this subject (cached)."""
        if self._brain_mask is None:
            self._brain_mask = compute_brain_mask(
                self.sub, resolution=self.resolution, glmtype=self.glmtype,
                glmsingle=self.glmsingle,
            )
        return self._brain_mask

    def get_n_voxels(self):
        """Number of voxels in the brain mask."""
        return int(self.get_brain_mask().sum())

    @property
    def affine(self):
        """The subject-native (T1w) affine at this subject's resolution, cached."""
        if self._affine is None:
            self._affine = self.glmsingle.read_affine(
                self.sub, resolution=self.resolution,
            )
        return self._affine

    @property
    def header(self):
        """NIfTI header from the anatomical reference at this resolution, cached."""
        if self._header is None:
            self._header = self.glmsingle.read_header(
                self.sub, resolution=self.resolution,
            )
        return self._header

    def get_voxel_coordinates(self, roi=None, mask=None):
        """Anatomical coords for voxels in ``brain ∩ (roi | mask | all)``."""
        return get_voxel_coordinates(self._resolve_mask(roi, mask), self.affine)

    # ------------------------------------------------------------------
    # ROI selection
    # ------------------------------------------------------------------
    def get_available_rois(self):
        """ROIs available for this subject in the ROI manifest."""
        return self.roi.rois(subject=self.sub)

    def get_roi_mask(self, query, atlas="wang_2015", space="T1w",
                     res=None, cons="balanced", hemi=None):
        """A boolean 3-D mask from an ROI ``query``, restricted to the brain mask.

        ``query`` may be:

        * a single ROI name (``"V1v"``);
        * ``"all"`` — every ROI available for the subject;
        * a list of names / ``"all"`` — returns the **union** of all matches.

        ``space="T1w"`` and ``res=self.resolution`` index the subject-native
        volume (same grid as the GLMsingle betas).
        """
        res = res or self.resolution
        names = self._resolve_roi_query(query)
        out = None
        for name in names:
            m = self.roi.read_mask(
                self.sub, name, atlas=atlas, space=space,
                res=res, cons=cons, hemi=hemi,
            )
            out = m if out is None else (out | m)
        if out is None:
            raise DataNotFoundError(f"No ROIs matched query {query!r}")
        return out & self.get_brain_mask()

    # ------------------------------------------------------------------
    # betas
    # ------------------------------------------------------------------
    def get_betas(self, ses, roi=None, mask=None, nc_threshold=None,
                  nc_direction="fw"):
        """Per-session GLMsingle betas as ``(n_trials, n_voxels)``.

        Trials are returned in the per-session GLMsingle order (same as the
        underlying ``read_betas``). ``roi`` or ``mask`` restricts voxels;
        ``nc_threshold`` further restricts by the per-session noise ceiling
        (in ``nc_direction``).
        """
        betas = self.glmsingle.read_betas(
            self.sub, ses, glmtype=self.glmtype, resolution=self.resolution,
        )  # (X, Y, Z, n_trials)
        m = self._resolve_mask(roi, mask)
        if nc_threshold is not None:
            nc = self.glmsingle.read_noiseceiling(
                self.sub, ses, glmtype=self.glmtype,
                resolution=self.resolution, direction=nc_direction,
            )
            m = m & (nc >= nc_threshold)
        return betas[m].T  # (n_voxels, n_trials) -> (n_trials, n_voxels)

    def get_video_betas(self, video, direction="fw", roi=None, mask=None,
                        average_repeats=False):
        """Per-video GLMsingle betas.

        Per-video files store two timepoints — the two repetitions of this
        video across the subject's sessions. Shape is ``(2, n_voxels)``, or
        ``(n_voxels,)`` if ``average_repeats=True``.
        """
        beta = self.glmsingle.read_video_betas(
            self.sub, video, direction=direction,
            glmtype=self.glmtype, resolution=self.resolution,
            zscore=True, average_repeat=average_repeats,
        )
        m = self._resolve_mask(roi, mask)
        if average_repeats:
            return beta[m]                # (n_vox,)
        return beta[:, m]                 # (2, n_vox)

    def get_run_betas(self, ses, run, roi=None, mask=None):
        """Compose a run's betas from per-video files, in trial order.

        Walks ``events.tsv`` for trial order, then for each non-blank trial
        slices the matching repetition (0 or 1) from the per-video file's
        two timepoints — the repetition index is the trial's position in
        the subject's full chronological sequence of (video, direction)
        appearances.

        Returns ``(n_stim_trials, n_voxels)``; blank trials are dropped.
        """
        rows = self.trial_info(ses=ses, run=run)
        rows = rows[~rows.is_blank].reset_index(drop=True)
        if rows.empty:
            raise DataNotFoundError(
                f"No stim trials found for sub={self.sub} ses={ses} run={run}."
            )
        m = self._resolve_mask(roi, mask)
        out = np.empty((len(rows), int(m.sum())), dtype=np.float32)
        for i, r in enumerate(rows.itertuples(index=False)):
            both = self.glmsingle.read_video_betas(
                self.sub, int(r.video), direction=r.direction,
                glmtype=self.glmtype, resolution=self.resolution, zscore=True,
            )  # (2, X, Y, Z)
            out[i] = both[int(r.rep)][m]
        return out

    def get_noise_ceiling(self, ses, direction="fw", roi=None, mask=None):
        """Per-session noise ceiling restricted to ``brain ∩ (roi | mask)``."""
        nc = self.glmsingle.read_noiseceiling(
            self.sub, ses, glmtype=self.glmtype,
            resolution=self.resolution, direction=direction,
        )
        return nc[self._resolve_mask(roi, mask)]

    # ------------------------------------------------------------------
    # trial table
    # ------------------------------------------------------------------
    def trial_table(self):
        """A DataFrame of every trial across this subject's main-task data.

        Columns: ``ses``, ``run``, ``trial`` (within-run index of the
        ``movie`` event), ``video`` (int) / ``direction`` (``"fw"``/``"rv"``)
        / ``rep`` (0 or 1, repetition index in the per-video file) for stim
        trials, all ``None`` for blank trials, plus ``is_blank``.

        Cached. The ``rep`` field is computed by counting (video, direction)
        appearances in chronological order across all (ses, run) — so the
        first chronological appearance gets ``rep=0`` and the second gets
        ``rep=1``, matching the two timepoints of the per-video NIfTI.
        """
        if self._trial_table is None:
            self._trial_table = self._build_trial_table()
        return self._trial_table

    def trial_info(self, ses=None, run=None):
        """A view of ``trial_table`` filtered by session and/or run."""
        t = self.trial_table()
        if ses is not None:
            t = t[t.ses == ses]
        if run is not None:
            t = t[t.run == run]
        return t.reset_index(drop=True)

    def _build_trial_table(self):
        counts = {}
        rows = []
        for ses in self.sessions():
            if not isinstance(ses, int):
                continue  # main-task table only — skip localizer sessions
            for run in self.runs(ses):
                events = self.bids.read_events_tsv(self.sub, ses, run)
                movies = [e for e in events if e.get("event_type") == "movie"]
                for trial_idx, e in enumerate(movies):
                    mf = (e.get("movie_file") or "").strip()
                    if mf == "blank":
                        rows.append({
                            "ses": ses, "run": run, "trial": trial_idx,
                            "video": None, "direction": None,
                            "rep": None, "is_blank": True,
                        })
                        continue
                    m = _MOVIE_RE.search(mf)
                    if not m:
                        continue
                    video, direction = int(m.group(1)), m.group(2)
                    rep = counts.get((video, direction), 0)
                    counts[(video, direction)] = rep + 1
                    rows.append({
                        "ses": ses, "run": run, "trial": trial_idx,
                        "video": video, "direction": direction,
                        "rep": rep, "is_blank": False,
                    })
        return pd.DataFrame(rows)

    # ------------------------------------------------------------------
    # round-trip back to volume
    # ------------------------------------------------------------------
    def to_nifti(self, flat_values, output_path=None, roi=None, mask=None):
        """Write a 1-D voxel vector back as a 3-D NIfTI on the subject grid.

        ``flat_values`` must live over the same mask the data was selected
        with (the brain mask by default, or the resolved ``roi``/``mask``).
        """
        m = self._resolve_mask(roi, mask)
        return to_nifti(
            flat_values, m, self.affine,
            output_path=output_path, header=self.header,
        )

    # ------------------------------------------------------------------
    # helpers
    # ------------------------------------------------------------------
    def _resolve_roi_query(self, query):
        """Flatten an ROI query into a list of distinct ROI names."""
        if isinstance(query, str):
            if query == "all":
                return list(self.get_available_rois())
            return [query]
        if isinstance(query, (list, tuple, set)):
            seen, out = set(), []
            for q in query:
                for name in self._resolve_roi_query(q):
                    if name not in seen:
                        seen.add(name)
                        out.append(name)
            return out
        raise TypeError(
            f"ROI query must be str or list/tuple/set, got {type(query).__name__}"
        )

    def _resolve_mask(self, roi, mask):
        """Resolve ``roi``/``mask`` to a 3-D bool array restricted to the brain."""
        bm = self.get_brain_mask()
        if roi is None and mask is None:
            return bm
        if roi is not None and mask is not None:
            raise ValueError("Pass either `roi` or `mask`, not both.")
        if roi is not None:
            return self.get_roi_mask(roi)            # already intersected with bm
        mask = np.asarray(mask, dtype=bool)
        if mask.shape == bm.shape:
            return mask & bm
        if mask.ndim == 1 and mask.shape[0] == int(bm.sum()):
            # flat mask over brain — expand back to a 3-D mask
            expanded = np.zeros_like(bm)
            expanded[bm] = mask
            return expanded
        raise ValueError(
            f"mask shape {mask.shape} doesn't match the brain grid {bm.shape} "
            f"or a flat-within-brain ({int(bm.sum())},)."
        )
