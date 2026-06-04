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

## Gray-matter mask — a tighter working set

For encoding-model work it's often more natural to fit on cortex gray
matter rather than the GLMsingle-derived brain mask. The FreeSurfer
cortex GM masks live in `anat-3T/<sub>/fiducial/res-<XpXmm>/` and share
the EPI grid affine — they drop in as a voxel selector with no
resampling.

```python
gm = sub.get_gray_matter_mask()                    # bool, ~60 k voxels at 2 mm
dil = sub.get_gray_matter_mask("cortex_dil")       # bool, ~100 k (dilated)
soft = sub.get_gray_matter_mask("cortex_sm")       # float in [0, 1], ~160 k > 0
```

Three variants; the return type follows the variant:

| variant | dtype | voxels (sub-001, 2p0mm) | notes |
|---|---|---|---|
| `"cortex"` (default) | `bool` | ~61 k | canonical FreeSurfer cortex GM |
| `"cortex_dil"` | `bool` | ~98 k | dilated — broader, includes some non-GM |
| `"cortex_sm"` | `float` in [0, 1] | ~163 k > 0 | smoothed soft mask |

Use it as a custom `mask=` on any voxel-valued method. The selector is
intersected with the brain mask, so any non-brain voxels in the GM mask
are dropped automatically:

```python
betas_gm = sub.get_betas(ses=1, mask=sub.get_gray_matter_mask())
betas_gm.shape    # (n_trials, n_gm ∩ brain_voxels)

# For the soft mask, threshold yourself before passing:
betas_soft = sub.get_betas(ses=1, mask=(sub.get_gray_matter_mask("cortex_sm") > 0.5))
```

Each `(variant)` is cached on the `AOTSubject` instance.

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
