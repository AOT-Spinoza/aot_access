"""Brain-mask conventions and volume <-> flat-voxel utilities.

The "brain mask" is a per-subject boolean 3-D array — the set of voxels we
ever consider. Working data (betas, BOLD samples, ROI selections) is stored
as a 1-D vector over the True positions of a mask, and :func:`to_nifti`
inverts that flattening back into a 3-D NIfTI image.

Three derivations are available. The default working set is
**anatomical cortex gray matter** — :class:`AOTSubject` uses
``cortex_dil`` (the dilated FreeSurfer cortex mask, ~100 k voxels) by
default, so that low-R² regions like the DMN are kept. The two
data-driven masks below are sibling reachable for analyses that want
to threshold on signal reliability:

* :func:`compute_ncsnr_brain_mask` — session-averaged NCSNR-monotonic
  noise-ceiling. The preferred data-driven mask: averages
  ``noiseceiling_dir-{fw,rv}`` across every available main-task
  session and thresholds.
* :func:`compute_brain_mask` — legacy single-session R² > 0. Kept for
  diagnostics; not used as a default anywhere.
"""

import numpy as np
import nibabel as nib

from AOTaccess.errors import DataNotFoundError
from AOTaccess.glmsingle_access import GLMSingleAccess


def compute_brain_mask(sub, ses=1, resolution="2p0mm",
                       glmtype="TYPED_FITHRF_GLMDENOISE_RR",
                       glmsingle=None, config=None):
    """Boolean 3-D brain mask from a single session's GLMsingle R² > 0.

    Legacy mask kept for diagnostics. Prefer
    :func:`compute_ncsnr_brain_mask` (the data-driven default for
    :class:`AOTSubject` when ``default_mask="ncsnr"`` / ``"r2"``) or the
    anatomical cortex GM mask via
    :meth:`AnatomyAccess.read_gray_matter_mask` (the anatomical default).

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
