"""
Brain mask + ROIs — voxel selection geometry
=============================================

Inspect the per-subject brain mask, look at a few ROIs, and confirm
the voxel-count arithmetic that ``get_betas(roi=...)`` uses.
"""

# %%
# Bind a subject and look at the brain mask.

from AOTaccess.subject import AOTSubject

sub = AOTSubject(1)
brain_mask = sub.get_brain_mask()
print("brain mask shape :", brain_mask.shape)
print("brain voxels     :", sub.get_n_voxels())
print("total voxels in volume :", int(brain_mask.size))

# %%
# Pick a handful of ROIs and see how they relate.

rois = ["V1v", "V1d", "V2v", "V2d", "hV4"]
for name in rois:
    m = sub.get_roi_mask(name)
    print(f"  {name:>4s}: {int(m.sum()):>5d} voxels")

union = sub.get_roi_mask(rois)
print(f"  union: {int(union.sum()):>5d} voxels")

# %%
# Coordinates of every voxel in V1v (mm in T1w / anatomical frame).

coords = sub.get_voxel_coordinates(roi="V1v")
print("V1v coords shape :", coords.shape)
print("x range:", round(coords[:, 0].min(), 1), "...", round(coords[:, 0].max(), 1))
print("y range:", round(coords[:, 1].min(), 1), "...", round(coords[:, 1].max(), 1))
print("z range:", round(coords[:, 2].min(), 1), "...", round(coords[:, 2].max(), 1))

# %%
# Show a middle-slice projection of the brain mask with V1v highlighted.

import matplotlib.pyplot as plt
import numpy as np

z = brain_mask.shape[2] // 2  # axial slice
brain_slice = brain_mask[:, :, z]
v1v_slice = sub.get_roi_mask("V1v")[:, :, z]
v1d_slice = sub.get_roi_mask("V1d")[:, :, z]

fig, ax = plt.subplots(figsize=(4, 4))
ax.imshow(brain_slice.T, cmap="gray_r", origin="lower", alpha=0.3)
ax.imshow(np.where(v1v_slice, 1.0, np.nan).T, cmap="Reds", origin="lower", vmin=0, vmax=1)
ax.imshow(np.where(v1d_slice, 1.0, np.nan).T, cmap="Blues", origin="lower", vmin=0, vmax=1)
ax.set_title(f"axial z={z}: brain (gray), V1v (red), V1d (blue)")
ax.set_xticks([])
ax.set_yticks([])
fig.tight_layout()
