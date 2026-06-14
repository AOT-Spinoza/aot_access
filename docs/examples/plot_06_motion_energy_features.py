"""
Motion-energy features — pymoten filter bank
=============================================

Load the per-video motion-energy features and inspect the filter-bank
metadata (centres in degrees of visual angle, spatial / temporal
frequencies, directions). Two filter banks are available — max SF 16
and max SF 32; the larger one has many more filters.

The features live in per-(video, direction, rate) HDF5 files
(``.../motion_energy/{16,32}hz/NNNN_{fw,rv}.h5``) with two datasets:

* ``/motion_energy`` — per-frame, shape ``(n_frames, n_filters)``
  (the log-compressed pymoten output); read with
  :meth:`StimuliInfoAccess.read_motion_energy_features`.
* ``/motion_energy_summary`` — per-video, shape ``(n_filters,)`` —
  the temporal mean of the per-frame array (Nishimoto / Gallant-lab
  canonical pooling); read with
  :meth:`StimuliInfoAccess.read_motion_energy_summary`.

The reader prefers the HDF5 and transparently falls back to the legacy
``.npy`` while the conversion is in progress (one-time
``DeprecationWarning``).
"""

# %%
# Load the per-frame features for one video at both bank sizes.

from AOTaccess.stimulus_info_access import StimuliInfoAccess

stim = StimuliInfoAccess()

feat16 = stim.read_motion_energy_features(1, direction="fw", highest_freq=16)
feat32 = stim.read_motion_energy_features(1, direction="fw", highest_freq=32)
print("16-Hz features shape :", feat16.shape, " (time, channels)")
print("32-Hz features shape :", feat32.shape)

# %%
# Per-video summary — one (n_filters,) vector per video, equal to the
# temporal mean of the (already log-compressed) per-frame array. Useful as a
# fixed-length descriptor for cross-video similarity / encoding-model
# baselines. Raises ``DataNotFoundError`` while the conversion is still
# writing the ``/motion_energy_summary`` dataset.

from AOTaccess.errors import DataNotFoundError
try:
    summ16 = stim.read_motion_energy_summary(1, direction="fw", highest_freq=16)
    print("16-Hz summary shape  :", summ16.shape, "(matches n_filters)")
except DataNotFoundError as e:
    print("16-Hz summary not yet written:", str(e).splitlines()[0])

# %%
# Filter-bank metadata — what each channel "is".

info16 = stim.read_moten_filter_info(16)
print("16-Hz bank — n filters :", info16["meta"]["n_filters"])
print("            spatial fr :", info16["meta"]["spatial_frequencies"])
print("            fps        :", info16["meta"]["fps"])
print("            dva extent : ±{x_dva}° h × ±{y_dva}° v".format(
    x_dva=info16["dva_alignment"]["dva_x_half"],
    y_dva=info16["dva_alignment"]["dva_y_half"],
))

# %%
# Where each filter sits in the visual field.

import matplotlib.pyplot as plt
import numpy as np

filters = info16["filters"]
xs = np.array([f["x_dva"] for f in filters])
ys = np.array([f["y_dva"] for f in filters])
sfs = np.array([f["spatial_freq"] for f in filters])

fig, ax = plt.subplots(figsize=(5, 3.5))
sc = ax.scatter(xs, ys, c=sfs, s=4, cmap="viridis", alpha=0.6)
ax.set_xlabel("x (dva)")
ax.set_ylabel("y (dva)")
ax.set_aspect("equal")
ax.set_title("Pymoten 16-Hz filter centres in the visual field")
cb = fig.colorbar(sc, ax=ax, fraction=0.04)
cb.set_label("spatial freq (cyc/img)")
fig.tight_layout()

# %%
# Channel time-courses for one video — first 8 channels of the 16-Hz bank.

fig, ax = plt.subplots(figsize=(7, 3))
t = np.arange(feat16.shape[0]) / info16["meta"]["fps"]
ax.plot(t, feat16[:, :8])
ax.set_xlabel("time (s)")
ax.set_ylabel("activation")
ax.set_title("16-Hz motion-energy — channels 0–7 of video 0001_fw")
fig.tight_layout()
