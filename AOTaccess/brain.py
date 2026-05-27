"""Brain-mask conventions and volume <-> flat-voxel utilities.

The "brain mask" is a per-subject boolean 3-D array — the set of voxels we
ever consider. Working data (betas, BOLD samples, ROI selections) is stored
as a 1-D vector over the True positions of a mask, and :func:`to_nifti`
inverts that flattening back into a 3-D NIfTI image.

By default the brain mask is derived from GLMsingle's R² output: voxels
where R² is finite and positive in a reference session.
"""

import numpy as np
import nibabel as nib

from AOTaccess.glmsingle_access import GLMSingleAccess


def compute_brain_mask(sub, ses=1, resolution="2p0mm",
                       glmtype="TYPED_FITHRF_GLMDENOISE_RR",
                       glmsingle=None, config=None):
    """Boolean 3-D brain mask for one subject, derived from GLMsingle R².

    Voxels are kept where R² is finite and positive in ``ses`` (anatomy is
    constant across sessions, so the choice of reference session only
    affects which voxels GLMsingle marked as informative — the default
    ``ses=1`` is fine for every full subject).
    """
    glm = glmsingle if glmsingle is not None else GLMSingleAccess(config=config)
    r2 = glm.read_R2(sub, ses, glmtype=glmtype, resolution=resolution)
    with np.errstate(invalid="ignore"):
        return np.isfinite(r2) & (r2 > 0)


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
