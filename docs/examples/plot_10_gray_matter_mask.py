"""
Gray-matter mask — the default working set, and its variants
=============================================================

As of the latest release, ``AOTSubject(sub).get_brain_mask()`` returns
the **dilated FreeSurfer cortex GM mask** (``"cortex_dil"``) by
default — anatomical cortex including DMN regions, ~98 k voxels at
2 mm. The other two GM variants and the legacy data-driven masks are
reachable as siblings:

* ``"cortex"`` — canonical (undilated) FreeSurfer cortex GM, ~61 k.
* ``"cortex_sm"`` — smoothed soft cortex mask, float in [0, 1].
* ``"ncsnr"`` — session-averaged GLMsingle noise-ceiling mask,
  ~210 k voxels (use ``AOTSubject(sub, default_mask="ncsnr")`` to
  pick it as the default).

This example walks the four anatomical-mask options and the
data-driven NCSNR sibling, then compares betas shapes.
"""

# %%
# The default subject — its brain mask is now ``cortex_dil``.

import numpy as np
from AOTaccess.subject import AOTSubject

sub = AOTSubject(1)
default_bm = sub.get_brain_mask()                  # bool, default = cortex_dil
cortex = sub.get_gray_matter_mask("cortex")        # bool
dilated = sub.get_gray_matter_mask("cortex_dil")   # bool — same as default_bm
soft = sub.get_gray_matter_mask("cortex_sm")       # float in [0, 1]
ncsnr = sub.get_glmsingle_ncsnr_mask()             # bool, session-averaged signal mask

print("default brain mask (cortex_dil):", int(default_bm.sum()))
print("cortex                          :", int(cortex.sum()))
print("cortex_dil                      :", int(dilated.sum()))
print("cortex_sm > 0                   :", int((soft > 0).sum()))
print("cortex_sm > 0.5                 :", int((soft > 0.5).sum()))
print("ncsnr (session-averaged signal) :", int(ncsnr.sum()))

# %%
# Any selector passed to ``get_betas`` is intersected with the default
# brain mask — so a mask query through ``mask=`` only ever shrinks the
# default working set.

print("cortex ∩ default     :", int((cortex & default_bm).sum()))
print("ncsnr ∩ default      :", int((ncsnr & default_bm).sum()))

# %%
# Same flat-voxel API, with the working set restricted by ``mask=``.
# The default call (no selector) now lands on ~98 k cortical voxels;
# explicitly selecting the canonical (undilated) cortex tightens to ~61 k;
# the soft mask thresholded at 0.5 sits between.

betas_default = sub.get_betas(ses=1)                     # over cortex_dil
betas_gm = sub.get_betas(ses=1, mask=cortex)             # over cortex ∩ cortex_dil
betas_soft = sub.get_betas(ses=1, mask=(soft > 0.5))     # over (soft > 0.5) ∩ cortex_dil
betas_ncsnr = sub.get_betas(ses=1, mask=ncsnr)           # over ncsnr ∩ cortex_dil

print("\nshape (default = cortex_dil) :", betas_default.shape)
print("shape (cortex)                :", betas_gm.shape)
print("shape (cortex_sm > 0.5)       :", betas_soft.shape)
print("shape (ncsnr)                 :", betas_ncsnr.shape)

# %%
# Where do the variants differ in the slice? Plot one axial slice with
# the dilated cortex (default brain mask) in gray, canonical cortex
# (red), and the dilation halo (cortex_dil − cortex, blue).

import matplotlib.pyplot as plt

z = default_bm.shape[2] // 2
fig, ax = plt.subplots(figsize=(4, 4))
ax.imshow(default_bm[:, :, z].T, cmap="gray_r", origin="lower", alpha=0.25)
ax.imshow(
    np.where(cortex[:, :, z], 1.0, np.nan).T,
    cmap="Reds", origin="lower", vmin=0, vmax=1,
)
ax.imshow(
    np.where(dilated[:, :, z] & ~cortex[:, :, z], 1.0, np.nan).T,
    cmap="Blues", origin="lower", vmin=0, vmax=1,
)
ax.set_title(f"axial z={z}: cortex_dil (gray), cortex (red), halo (blue)")
ax.set_xticks([]); ax.set_yticks([])
fig.tight_layout()

# %%
# How does the noise ceiling compare across the anatomical default and
# the data-driven NCSNR mask? The NCSNR mask is wider (~210 k) but
# selects on reliability; the cortex_dil default is anatomy-based but
# keeps DMN voxels with low NC.

nc_default = sub.get_noise_ceiling(ses=1)                  # default = cortex_dil
sub_ncsnr = AOTSubject(1, default_mask="ncsnr")
nc_signal = sub_ncsnr.get_noise_ceiling(ses=1)

fig, ax = plt.subplots(figsize=(5, 3))
ax.hist(nc_default, bins=60, alpha=0.5, label=f"cortex_dil (n={nc_default.size})", density=True)
ax.hist(nc_signal, bins=60, alpha=0.5, label=f"ncsnr (n={nc_signal.size})", density=True)
ax.set_xlabel("noise ceiling (ses-1, dir-fw)")
ax.set_ylabel("density")
ax.legend()
ax.set_title("Noise-ceiling distribution: cortex_dil vs NCSNR mask")
fig.tight_layout()
