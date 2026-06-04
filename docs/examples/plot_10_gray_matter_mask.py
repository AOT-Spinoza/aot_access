"""
Gray-matter mask — fitting on cortex only
==========================================

The default working set is the GLMsingle-derived brain mask (R² > 0).
For encoding-model work it's usually more natural to fit on cortex gray
matter. The FreeSurfer cortex GM masks live in
``anat-3T/<sub>/fiducial/res-<XpXmm>/`` and share the EPI affine, so
they drop in as a custom ``mask=`` with no resampling.
"""

# %%
# Three variants.

import numpy as np
from AOTaccess.subject import AOTSubject

sub = AOTSubject(1)
brain = sub.get_brain_mask()
cortex = sub.get_gray_matter_mask()                # bool
dilated = sub.get_gray_matter_mask("cortex_dil")   # bool
soft = sub.get_gray_matter_mask("cortex_sm")       # float in [0, 1]

print("brain        :", int(brain.sum()))
print("cortex       :", int(cortex.sum()))
print("cortex_dil   :", int(dilated.sum()))
print("cortex_sm>0  :", int((soft > 0).sum()))
print("cortex_sm>0.5:", int((soft > 0.5).sum()))

# %%
# Each variant is intersected with the brain mask when passed as a
# selector to ``get_betas`` — so the GM voxel count reported above
# may shrink when overlapped with what GLMsingle saw.

print("cortex ∩ brain      :", int((cortex & brain).sum()))
print("cortex_dil ∩ brain  :", int((dilated & brain).sum()))

# %%
# Same flat-voxel API, with the working set restricted to GM.

betas_default = sub.get_betas(ses=1)                     # over the brain mask
betas_gm = sub.get_betas(ses=1, mask=cortex)             # over cortex ∩ brain
betas_dil = sub.get_betas(ses=1, mask=dilated)           # over cortex_dil ∩ brain
betas_soft = sub.get_betas(ses=1, mask=(soft > 0.5))     # threshold soft mask yourself

print("\nshape (default brain mask) :", betas_default.shape)
print("shape (cortex)              :", betas_gm.shape)
print("shape (cortex_dil)          :", betas_dil.shape)
print("shape (cortex_sm > 0.5)     :", betas_soft.shape)

# %%
# Where do the variants differ in the slice? Plot one axial slice with
# the brain mask in gray, cortex (red), and the cortex_dil − cortex
# differential (blue) on top.

import matplotlib.pyplot as plt

z = brain.shape[2] // 2
fig, ax = plt.subplots(figsize=(4, 4))
ax.imshow(brain[:, :, z].T, cmap="gray_r", origin="lower", alpha=0.25)
ax.imshow(
    np.where(cortex[:, :, z], 1.0, np.nan).T,
    cmap="Reds", origin="lower", vmin=0, vmax=1,
)
ax.imshow(
    np.where(dilated[:, :, z] & ~cortex[:, :, z], 1.0, np.nan).T,
    cmap="Blues", origin="lower", vmin=0, vmax=1,
)
ax.set_title(f"axial z={z}: brain (gray), cortex (red), dilation halo (blue)")
ax.set_xticks([]); ax.set_yticks([])
fig.tight_layout()

# %%
# How does the noise ceiling compare across the two working sets?

nc_brain = sub.get_noise_ceiling(ses=1)                  # default mask
nc_gm = sub.get_noise_ceiling(ses=1, mask=cortex)

fig, ax = plt.subplots(figsize=(5, 3))
ax.hist(nc_brain, bins=60, alpha=0.5, label=f"brain (n={nc_brain.size})", density=True)
ax.hist(nc_gm, bins=60, alpha=0.5, label=f"cortex GM (n={nc_gm.size})", density=True)
ax.set_xlabel("noise ceiling")
ax.set_ylabel("density")
ax.legend()
ax.set_title("Noise-ceiling distribution: brain mask vs cortex GM")
fig.tight_layout()
