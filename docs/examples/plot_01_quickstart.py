"""
Quickstart — one subject, one ROI, one ``get_betas`` call
==========================================================

The minimum trip through the API: bind a subject, ask for betas in V1v,
plot a few trials, round-trip a per-voxel summary back to a NIfTI.
"""

# %%
# Bind a subject. Defaults are 2 mm resolution and the full
# ``TYPED_FITHRF_GLMDENOISE_RR`` GLMsingle model.

from AOTaccess.subject import AOTSubject

sub = AOTSubject(1)
print("brain voxels:", sub.get_n_voxels())
print("sessions    :", sub.sessions())

# %%
# Get session 1's betas restricted to V1v. Result shape is
# ``(n_trials, n_voxels)`` — the laion-fMRI / NSD convention.

betas = sub.get_betas(ses=1, roi="V1v")
print("betas shape :", betas.shape)

# %%
# Plot the first few trials as voxels × trials.

import matplotlib.pyplot as plt
import numpy as np

fig, ax = plt.subplots(figsize=(6, 3))
im = ax.imshow(betas[:30].T, aspect="auto", cmap="RdBu_r",
               vmin=-np.abs(betas[:30]).max(), vmax=np.abs(betas[:30]).max())
ax.set_xlabel("trial")
ax.set_ylabel("V1v voxel")
ax.set_title("Session 1 — V1v betas, first 30 trials")
fig.colorbar(im, ax=ax, fraction=0.04)
fig.tight_layout()

# %%
# Round-trip a per-voxel summary back to a 3-D NIfTI on the subject grid.

mean_response = betas.mean(axis=0)             # (n_v1_voxels,)
img = sub.to_nifti(mean_response, roi="V1v")   # nib.Nifti1Image
print("nifti shape :", img.shape, " sum:", float(img.get_fdata().sum()))
