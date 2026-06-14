"""Brain-mask conventions and volume <-> flat-voxel utilities.

The "brain mask" is a per-subject boolean 3-D array — the set of voxels we
ever consider. Working data (betas, BOLD samples, ROI selections) is stored
as a 1-D vector over the True positions of a mask, and :func:`to_nifti`
inverts that flattening back into a 3-D NIfTI image.

This module exposes one **dispatcher** and three **primitives**.
:func:`compute_brain_mask` is the canonical entry point — it picks the
recipe by ``kind=``. The default ``kind="cortex_dil"`` is the dilated
FreeSurfer cortex mask (~100 k voxels at 2 mm), so low-R² regions like
the DMN stay in the working set. The other kinds and the underlying
primitives:

* ``kind="cortex"`` / ``"cortex_dil"`` / ``"cortex_sm"`` — read the
  FreeSurfer cortex GM mask via
  :meth:`AnatomyAccess.read_gray_matter_mask`. ``"cortex_sm"`` is
  thresholded at 0.5 internally to a boolean.
* ``kind="ncsnr"`` (alias ``"r2"``) — call
  :func:`compute_ncsnr_brain_mask`, the session-averaged NCSNR-monotonic
  noise-ceiling mask (the preferred data-driven choice).
* :func:`compute_r2_brain_mask` — legacy single-session R² > 0, kept
  reachable for diagnostics. Not exposed via the dispatcher (would
  conflict with the ``"r2"`` alias).

:class:`AOTSubject` calls the dispatcher under the hood (with its own
per-instance caches), so the recommended user-facing path is
``AOTSubject(sub, default_mask=...).get_brain_mask()``.
"""

import numpy as np
import nibabel as nib

from AOTaccess.errors import DataNotFoundError
from AOTaccess.glmsingle_access import GLMSingleAccess


# Recipes the dispatcher accepts and how they're categorised.
_BRAIN_MASK_KINDS = {
    "cortex":     "anatomical",
    "cortex_dil": "anatomical",
    "cortex_sm":  "anatomical_soft",   # thresholded at 0.5 internally
    "ncsnr":      "signal",
    "r2":         "signal",            # alias of "ncsnr"
}


def compute_brain_mask(
    sub,
    kind="cortex_dil",
    resolution="2p0mm",
    *,
    # signal-mask (ncsnr / r2) knobs
    sessions=None,
    directions=("fw", "rv"),
    threshold=0.0,
    # shared knobs
    glmtype="TYPED_FITHRF_GLMDENOISE_RR",
    glmsingle=None,
    anatomy=None,
    config=None,
):
    """Boolean 3-D brain mask — the canonical entry point.

    Dispatches to one of the underlying primitives based on ``kind``:

    * ``"cortex_dil"`` (default) — dilated FreeSurfer cortex GM, ~100 k
      voxels at 2 mm. Anatomical, DMN-safe.
    * ``"cortex"`` — canonical FreeSurfer cortex GM, ~60 k.
    * ``"cortex_sm"`` — smoothed soft cortex mask, thresholded at 0.5.
    * ``"ncsnr"`` — session-averaged GLMsingle noise ceiling
      (NCSNR-monotonic) > ``threshold``; see
      :func:`compute_ncsnr_brain_mask` for the underlying primitive.
    * ``"r2"`` — alias for ``"ncsnr"``. Kept as a meaningful label for
      the "GLMsingle-derived signal mask" idea; the underlying metric
      is **not** type-D R² any more (NCSNR averages better across
      sessions and doesn't reward overfit voxels). The legacy
      single-session R² > 0 mask is still reachable as the separate
      :func:`compute_r2_brain_mask` primitive.

    Pass ``anatomy=`` / ``glmsingle=`` if you have prebuilt accessors
    (e.g. from :class:`AOTSubject`) to avoid rebuilding the Config.

    Raises:
        ValueError: ``kind`` not in ``_BRAIN_MASK_KINDS``.
        DataNotFoundError: the on-disk file the chosen kind needs is
            missing.
    """
    if kind not in _BRAIN_MASK_KINDS:
        raise ValueError(
            f"Unknown brain-mask kind {kind!r}; "
            f"expected one of {sorted(_BRAIN_MASK_KINDS)}."
        )
    if kind in ("cortex", "cortex_dil", "cortex_sm"):
        # Anatomical path. Lazy-import AnatomyAccess to avoid a hard
        # dependency from brain.py on the anatomy module (and the cyclic
        # import risk if AnatomyAccess ever wants brain utilities).
        from AOTaccess.anatomy_access import AnatomyAccess

        ana = anatomy if anatomy is not None else AnatomyAccess(config=config)
        variant = "cortex_sm" if kind == "cortex_sm" else kind
        mask = ana.read_gray_matter_mask(
            sub, resolution=resolution, variant=variant,
        )
        if kind == "cortex_sm":
            mask = mask > 0.5
        return mask
    # Signal-mask path ("ncsnr" / "r2").
    return compute_ncsnr_brain_mask(
        sub,
        sessions=sessions,
        directions=directions,
        threshold=threshold,
        glmtype=glmtype,
        resolution=resolution,
        glmsingle=glmsingle,
        config=config,
    )


def compute_r2_brain_mask(sub, ses=1, resolution="2p0mm",
                          glmtype="TYPED_FITHRF_GLMDENOISE_RR",
                          glmsingle=None, config=None):
    """Boolean 3-D brain mask from a single session's GLMsingle R² > 0.

    Legacy primitive kept for diagnostics — not the package default any
    more. Prefer :func:`compute_brain_mask` (the dispatcher; default
    ``kind="cortex_dil"``) for new code. The data-driven sibling
    :func:`compute_ncsnr_brain_mask` is the better choice when you want
    a signal-based mask.

    Voxels are kept where R² is finite and positive in ``ses``. Anatomy is
    constant across sessions, so the choice of reference session only
    affects which voxels GLMsingle marked as informative — the default
    ``ses=1`` is fine for every full subject.
    """
    glm = glmsingle if glmsingle is not None else GLMSingleAccess(config=config)
    r2 = glm.read_R2(sub, ses, glmtype=glmtype, resolution=resolution)
    with np.errstate(invalid="ignore"):
        return np.isfinite(r2) & (r2 > 0)


def compute_ncsnr_brain_mask(
    sub,
    sessions=None,
    directions=("fw", "rv"),
    threshold=0.0,
    glmtype="TYPED_FITHRF_GLMDENOISE_RR",
    resolution="2p0mm",
    glmsingle=None,
    config=None,
):
    """Boolean 3-D brain mask from session-averaged GLMsingle noise ceiling.

    NCSNR (noise-ceiling SNR) is GLMsingle's per-voxel reliability
    metric — high where the signal can be consistently estimated across
    repetitions. The on-disk ``noiseceiling_dir-{fw,rv}`` map is a
    monotone function of NCSNR (per direction), so averaging it across
    sessions and directions and thresholding gives the same qualitative
    answer as averaging NCSNR itself: *voxels that show reliable signal
    across most of the subject's main-task data*.

    Voxels where the NC map is NaN in some sessions (skull, air,
    drop-out) are treated as 0 for averaging — they contribute toward
    the threshold check only via the sessions where they have a value.

    Parameters
    ----------
    sub : int | str
        Subject id.
    sessions : list[int] | None
        Main-task sessions to average over. ``None`` → discover every
        integer session present in the GLMsingle store. Non-integer
        labels (``"pRF"`` / ``"fLOC"``) are ignored.
    directions : tuple[str, ...]
        Directions to combine; default both ``"fw"`` and ``"rv"`` to
        match the standard "any reliable signal" semantics.
    threshold : float
        Inclusion threshold on the averaged NC value (default ``0.0`` —
        any reliable signal; raise to e.g. ``0.05`` for a tighter mask).
    glmtype, resolution
        Forwarded to :class:`GLMSingleAccess`. Only ``TYPED`` carries
        the per-direction noise-ceiling maps.

    Raises
    ------
    DataNotFoundError
        No NC files were readable for any (session, direction).
    """
    from AOTaccess.discovery import sessions as _discover_sessions

    glm = glmsingle if glmsingle is not None else GLMSingleAccess(config=config)
    if sessions is None:
        sessions = [
            s for s in _discover_sessions(sub, config=config)
            if isinstance(s, int)
        ]
    if not sessions:
        raise DataNotFoundError(
            f"No main-task sessions found for sub={sub} in the GLMsingle store."
        )

    acc = None
    n = 0
    for ses in sessions:
        for direction in directions:
            try:
                nc = glm.read_noiseceiling(
                    sub, ses, glmtype=glmtype,
                    resolution=resolution, direction=direction,
                )
            except DataNotFoundError:
                continue
            # NaNs (skull, air) → 0 for averaging.
            nc = np.where(np.isfinite(nc), nc, 0.0).astype(np.float64)
            acc = nc if acc is None else acc + nc
            n += 1
    if acc is None or n == 0:
        raise DataNotFoundError(
            f"No noise-ceiling maps found for sub={sub}, "
            f"sessions={sessions}, directions={list(directions)}."
        )
    avg = acc / n
    return avg > threshold


def get_voxel_coordinates(mask_3d, affine):
    """Anatomical coordinates for the True positions of a 3-D mask.

    Returns ``(n_true_voxels, 3)`` of x/y/z in the affine's frame (T1w/MNI),
    in row-major (np.argwhere) order.
    """
    idx = np.argwhere(mask_3d).astype(float)              # (n, 3) of i,j,k
    homog = np.column_stack([idx, np.ones(idx.shape[0])])  # (n, 4)
    return (homog @ affine.T)[:, :3]


def to_nifti(flat_values, mask_3d, affine, output_path=None, header=None):
    """Inverse of mask flattening: build a 3-D NIfTI from a 1-D vector.

    ``flat_values`` lives over the True positions of ``mask_3d``. Voxels
    outside the mask are filled with zero. Writes the image to
    ``output_path`` when given; always returns the ``Nifti1Image``.
    """
    values = np.asarray(flat_values)
    n_true = int(mask_3d.sum())
    if values.shape != (n_true,):
        raise ValueError(
            f"flat_values shape {values.shape} does not match mask "
            f"({n_true} True voxels)."
        )
    out = np.zeros(mask_3d.shape, dtype=values.dtype)
    out[mask_3d] = values
    img = nib.Nifti1Image(out, affine, header=header)
    if output_path is not None:
        nib.save(img, str(output_path))
    return img
