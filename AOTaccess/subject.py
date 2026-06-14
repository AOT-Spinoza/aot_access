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
from AOTaccess.anatomy_access import AnatomyAccess
from AOTaccess.bids_access import BidsAccess
from AOTaccess.brain import (
    compute_brain_mask,
    compute_ncsnr_brain_mask,
    get_voxel_coordinates,
    to_nifti,
)
from AOTaccess.config import Config
from AOTaccess.errors import DataNotFoundError
from AOTaccess.expdesign_access import ExpDesignAccess
from AOTaccess.glmsingle_access import GLMSingleAccess
from AOTaccess.preproced_access import PreprocedAccess
from AOTaccess.roi_access import ROIAccess


# matches the trailing "NNNN_fw.mp4" or "NNNN_rv.mp4" in an events-tsv movie_file
_MOVIE_RE = re.compile(r"(\d{4})_(fw|rv)\.mp4$")

# Allowed values for `default_mask` and how each maps to a working-set
# computation. The cortex_* variants delegate to ``read_gray_matter_mask``
# (anatomical, EPI grid); ``"ncsnr"`` / ``"r2"`` both delegate to the
# session-averaged NCSNR-monotonic mask. (``"r2"`` is kept as a synonym
# for "the GLMsingle-derived signal mask" — the underlying metric is now
# noise-ceiling, not type-D R², because NCSNR averages better across
# sessions and doesn't reward overfit voxels.)
_DEFAULT_MASK_CHOICES = {
    "cortex": "anatomical",
    "cortex_dil": "anatomical",
    "cortex_sm": "anatomical_soft",   # thresholded internally at 0.5
    "ncsnr": "signal",
    "r2": "signal",                   # alias for ncsnr-based signal mask
}


class AOTSubject:
    """Per-subject access object for the AOT dataset."""

    def __init__(self, sub, config=None, resolution="2p0mm",
                 glmtype="TYPED_FITHRF_GLMDENOISE_RR",
                 default_mask="cortex_dil"):
        """
        Parameters:
            sub (int | str): Subject identifier (e.g. ``1`` or ``"sub-001"``).
            config (Config): An explicit Config; otherwise default settings.
            resolution (str): EPI/T1w grid resolution, default ``"2p0mm"``.
            glmtype (str): GLMsingle model entity, default the full RR model.
            default_mask (str): The mask returned by
                :meth:`get_brain_mask` and used as the working set by every
                voxel-valued method when no ``roi``/``mask`` is passed.
                One of:

                * ``"cortex_dil"`` (**default**) — dilated FreeSurfer cortex
                  GM, ~100 k voxels at 2 mm. Keeps low-R² regions like the
                  DMN.
                * ``"cortex"`` — canonical FreeSurfer cortex GM, ~60 k.
                * ``"cortex_sm"`` — smoothed soft cortex mask, thresholded
                  at 0.5 to a boolean working set.
                * ``"ncsnr"`` — session-averaged GLMsingle noise ceiling
                  (NCSNR-monotonic) > 0 — see
                  :meth:`get_glmsingle_ncsnr_mask`.
                * ``"r2"`` — alias for ``"ncsnr"`` (kept for backward
                  intent; the underlying metric is now NCSNR-averaged-
                  across-sessions, not type-D R²).
        """
        if default_mask not in _DEFAULT_MASK_CHOICES:
            raise ValueError(
                f"Unknown default_mask={default_mask!r}; "
                f"expected one of {sorted(_DEFAULT_MASK_CHOICES)}."
            )
        self.sub = sub
        self.resolution = resolution
        self.glmtype = glmtype
        self.default_mask = default_mask
        self.config = config if config is not None else Config()
        # Sub-accessors share the same Config.
        self.glmsingle = GLMSingleAccess(config=self.config)
        self.bids = BidsAccess(config=self.config)
        self.roi = ROIAccess(config=self.config)
        self.expdesign = ExpDesignAccess(config=self.config)
        self.preproced = PreprocedAccess(config=self.config)
        self.anatomy = AnatomyAccess(config=self.config)
        # Lazy caches.
        self._brain_mask = None
        self._affine = None
        self._header = None
        self._trial_table = None
        self._gm_mask_cache = {}                # keyed by variant
        self._ncsnr_mask_cache = {}             # keyed by threshold
        self._r2_mask_cache = {}                # keyed by ses

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
        """Boolean 3-D brain mask for this subject (cached).

        Returns the mask implied by ``default_mask`` (chosen at
        construction). The default is ``"cortex_dil"`` — the dilated
        FreeSurfer cortex GM mask — so the standard working set is
        anatomical cortex including DMN regions.

        ``default_mask`` choices and what they return here:

        * ``"cortex"`` / ``"cortex_dil"`` → that GM variant (bool).
        * ``"cortex_sm"`` → the soft mask thresholded at 0.5 (bool).
        * ``"ncsnr"`` / ``"r2"`` → :meth:`get_glmsingle_ncsnr_mask` at
          its default threshold (session-averaged NCSNR-monotonic > 0).

        :meth:`get_glmsingle_r2_mask` and
        :meth:`get_glmsingle_ncsnr_mask` are always reachable as
        siblings for diagnostic comparisons, regardless of which mask is
        the configured default.
        """
        if self._brain_mask is None:
            self._brain_mask = self._compute_default_mask()
        return self._brain_mask

    def _compute_default_mask(self):
        """Resolve ``self.default_mask`` to a 3-D boolean array."""
        if self.default_mask in ("cortex", "cortex_dil"):
            return self.get_gray_matter_mask(variant=self.default_mask)
        if self.default_mask == "cortex_sm":
            return self.get_gray_matter_mask(variant="cortex_sm") > 0.5
        if self.default_mask in ("ncsnr", "r2"):
            return self.get_glmsingle_ncsnr_mask()
        # _DEFAULT_MASK_CHOICES is validated in __init__; this is unreachable.
        raise ValueError(  # pragma: no cover
            f"Unknown default_mask={self.default_mask!r}"
        )

    def get_n_voxels(self):
        """Number of voxels in the brain mask."""
        return int(self.get_brain_mask().sum())

    def get_gray_matter_mask(self, variant="cortex"):
        """Cortex gray-matter mask on the subject's EPI grid.

        Reads the FreeSurfer cortex GM mask from
        ``anat-3T/<sub>/fiducial/res-{self.resolution}/...``. Return type
        follows the variant — boolean for the binary masks
        (``"cortex"``, ~60 k voxels; ``"cortex_dil"``, ~100 k) and float
        in ``[0, 1]`` for the smoothed soft mask (``"cortex_sm"``;
        threshold yourself before passing to a ``mask=`` selector).
        Cached per variant.

        The mask shares the EPI grid affine, so it drops in as a custom
        ``mask=`` on the voxel-valued methods:

        >>> betas = sub.get_betas(ses=1, mask=sub.get_gray_matter_mask())
        """
        if variant not in self._gm_mask_cache:
            self._gm_mask_cache[variant] = self.anatomy.read_gray_matter_mask(
                self.sub, resolution=self.resolution, variant=variant,
            )
        return self._gm_mask_cache[variant]

    def get_glmsingle_ncsnr_mask(self, threshold=0.0):
        """Session-averaged GLMsingle noise-ceiling mask (NCSNR-monotonic).

        Reads ``noiseceiling_dir-fw`` and ``noiseceiling_dir-rv`` for
        every main-task session present for this subject, averages
        across (session × direction), and thresholds. The result is the
        "voxels with reliable signal across most of the subject's data"
        mask — the data-driven brain mask used when ``default_mask`` is
        ``"ncsnr"`` (or its synonym ``"r2"``).

        Cached per ``threshold``. See :func:`brain.compute_ncsnr_brain_mask`
        for the underlying derivation.

        Parameters:
            threshold (float): inclusion threshold on the averaged value.
                Default ``0`` — "any reliable signal at all" — selects
                ~200 k voxels at 2 mm for a full subject. Raise (e.g.,
                ``0.05``) for a tighter mask.
        """
        if threshold not in self._ncsnr_mask_cache:
            self._ncsnr_mask_cache[threshold] = compute_ncsnr_brain_mask(
                self.sub,
                threshold=threshold,
                glmtype=self.glmtype,
                resolution=self.resolution,
                glmsingle=self.glmsingle,
                config=self.config,
            )
        return self._ncsnr_mask_cache[threshold]

    def get_glmsingle_r2_mask(self, ses=1):
        """Legacy single-session R² > 0 mask (diagnostic).

        Returns the boolean mask of voxels where GLMsingle's type-D R²
        is finite and positive in ``ses``. Kept reachable for
        backward-compatibility checks and for diagnostic plots against
        :meth:`get_glmsingle_ncsnr_mask`; **not** what the package uses
        as a default any more — NCSNR-based session averaging is more
        stable and doesn't reward overfit voxels.

        Cached per session.
        """
        if ses not in self._r2_mask_cache:
            self._r2_mask_cache[ses] = compute_brain_mask(
                self.sub, ses=ses, resolution=self.resolution,
                glmtype=self.glmtype, glmsingle=self.glmsingle,
            )
        return self._r2_mask_cache[ses]

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
    # generic per-session GLMsingle output reader (any `desc` tag)
    # ------------------------------------------------------------------
    def read_glmsingle_output(self, ses, desc, roi=None, mask=None):
        """Read any per-session GLMsingle map by its BIDS ``desc`` tag.

        Use this for the many maps that don't have a dedicated method —
        ``HRFindex``, ``HRFindexrun``, ``FRACvalue``, ``glmbadness``,
        ``noisepool``, ``pcvoxels``, ``rrbadness``, ``scaleoffset``,
        ``xvaltrend``, ``FitHRFR2`` / ``FitHRFR2run``. The result is flat
        over ``brain ∩ (roi | mask)`` if the map has the same 3-D shape
        as the brain mask; otherwise the raw ndarray is returned (some
        maps are 4-D — e.g. ``betasmd`` itself).
        """
        data = self.glmsingle.read_session_map(
            self.sub, ses, desc, glmtype=self.glmtype, resolution=self.resolution,
        )
        bm = self.get_brain_mask()
        if data.shape == bm.shape:
            return data[self._resolve_mask(roi, mask)]
        # 4-D (per-trial) or other shape — return as-is.
        return data

    def available_glmsingle_outputs(self, ses):
        """List GLMsingle ``desc`` tags available for one session."""
        return self.glmsingle.list_session_descs(
            self.sub, ses, glmtype=self.glmtype, resolution=self.resolution,
        )

    # ------------------------------------------------------------------
    # subject-level discovery — videos and their sessions
    # ------------------------------------------------------------------
    def sessions_for_video(self, video, direction=None):
        """Sessions where this video appears in the subject's main-task design.

        Returns a sorted list of session ints. With ``direction``
        (``"fw"`` / ``"rv"``), restricts to that direction. AOT videos
        appear twice per subject — usually in different runs, sometimes
        in different sessions.
        """
        t = self.trial_table()
        t = t[~t.is_blank & (t.video == int(video))]
        if direction is not None:
            t = t[t.direction == direction]
        return sorted(set(int(s) for s in t.ses.tolist()))

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
    # PyTorch dataset wrapper
    # ------------------------------------------------------------------
    def to_torch_dataset(self, direction="fw", roi=None, mask=None,
                         average_repeats=True, videos=None, feature_fn=None,
                         dtype="float32"):
        """A ``torch.utils.data.Dataset`` over this subject's per-video betas.

        Each item is a dict with ``video`` (int), ``direction``, ``rep``
        (0/1 — or ``None`` if ``average_repeats=True``), and ``betas``
        (a ``torch`` tensor of shape ``(n_voxels,)``). Pass
        ``feature_fn=callable(video, direction)`` to attach per-video
        stimulus features alongside the betas (useful for paired
        ``(stimulus, response)`` training).

        Parameters:
            direction (str): ``"fw"`` or ``"rv"``.
            roi / mask: voxel selector (same as the other ``get_*`` methods).
            average_repeats (bool): If True, one item per video (mean of
                both repetitions); else two items per video (rep 0 / rep 1).
            videos (list[int] | None): Restrict to a subset (default: all
                videos with per-video betas for this subject + direction).
            feature_fn: Optional callable returning the stimulus payload.
            dtype (str): NumPy dtype the betas are cast to before tensoring.

        Returns:
            torch.utils.data.Dataset: lazy — each ``__getitem__`` reads
            one per-video file.
        """
        try:
            import torch
            from torch.utils.data import Dataset
        except ImportError as exc:  # pragma: no cover - import-time only
            raise ImportError(
                "to_torch_dataset requires PyTorch; install with `pip install torch`."
            ) from exc

        if videos is None:
            videos = self.videos(direction=direction)
        voxel_mask = self._resolve_mask(roi, mask)
        subject = self

        class _AOTPerVideoDataset(Dataset):
            def __len__(self):
                return len(videos) if average_repeats else len(videos) * 2

            def __getitem__(self, idx):
                if average_repeats:
                    v = videos[idx]
                    rep = None
                    beta = subject.get_video_betas(
                        v, direction=direction, mask=voxel_mask,
                        average_repeats=True,
                    )
                else:
                    v = videos[idx // 2]
                    rep = idx % 2
                    both = subject.get_video_betas(
                        v, direction=direction, mask=voxel_mask,
                    )
                    beta = both[rep]
                sample = {
                    "video": int(v),
                    "direction": direction,
                    "rep": rep,
                    "betas": torch.from_numpy(beta.astype(dtype)),
                }
                if feature_fn is not None:
                    sample["features"] = feature_fn(v, direction)
                return sample

        return _AOTPerVideoDataset()

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
