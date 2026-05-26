# Brain mask and the flat-voxel convention

`AOTaccess` works in a per-subject **flat-voxel** representation: every voxel
the API ever returns lives in a 1-D vector over the True positions of a
per-subject **brain mask**. This matches the laion-fMRI / NSD convention
and is what encoding / decoding models want.

## The brain mask

A 3-D boolean array, computed by
{func}`~AOTaccess.brain.compute_brain_mask` and cached on
{class}`~AOTaccess.subject.AOTSubject`:

```python
sub = AOTSubject(1)
bm = sub.get_brain_mask()       # shape (X, Y, Z), dtype=bool
sub.get_n_voxels()              # int — bm.sum()
```

Default derivation: voxels where the GLMsingle R² map is **finite and > 0**
in `ses=1`. Anatomy is constant across sessions; the reference session only
affects which voxels GLMsingle flagged as informative.

## Flat voxels

The brain mask defines the working voxel set. Every `get_*` call that
returns voxel-valued data returns a flat array indexed over the mask's
True positions:

```python
betas = sub.get_betas(ses=1)         # (n_trials, n_brain_voxels)
nc    = sub.get_noise_ceiling(ses=1) # (n_brain_voxels,)
```

`roi=` or `mask=` further restricts to a sub-mask (always intersected with
the brain mask):

```python
betas_v1 = sub.get_betas(ses=1, roi="V1v")   # (n_trials, n_v1_voxels)
```

## Round-trip back to a 3-D NIfTI

{meth}`~AOTaccess.subject.AOTSubject.to_nifti` inverts the flattening:

```python
import numpy as np
prediction = np.random.randn(sub.get_n_voxels())     # over the brain mask
img = sub.to_nifti(prediction, "pred.nii.gz")
```

If the flat vector lives over a sub-mask (e.g. an ROI), pass the same
selector so `to_nifti` knows which voxels to fill:

```python
roi_pred = np.random.randn(sub.get_roi_mask("V1v").sum())
sub.to_nifti(roi_pred, "pred_v1v.nii.gz", roi="V1v")
```

Voxels outside the supplied mask are filled with zero. The image carries
the subject-native (T1w) affine + header at the current resolution.

## Anatomical coordinates

{meth}`~AOTaccess.subject.AOTSubject.get_voxel_coordinates` returns the
anatomical-space coordinates (mm) for the True positions of `brain ∩ (roi |
mask)`, in {func}`numpy.argwhere` order — so the *i*-th row of the
coordinates array corresponds to the *i*-th column of `get_betas`:

```python
coords = sub.get_voxel_coordinates(roi="V1v")   # (n_v1_voxels, 3)
```
