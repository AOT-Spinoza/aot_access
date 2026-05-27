"""
Per-video betas — both repetitions
====================================

GLMsingle writes a per-video file with two timepoints — one beta per
repetition of that video across the subject's sessions. Pulling them
out, comparing the two reps, and averaging.
"""

# %%
# Per-video betas as ``(2, n_voxels)`` for one ROI.

import numpy as np
from AOTaccess.subject import AOTSubject

sub = AOTSubject(1)

bv = sub.get_video_betas(video=1, direction="fw", roi="V1v")
print("shape          :", bv.shape, " (2 repetitions, n_v1v_voxels)")
print("rep-0 mean / rep-1 mean :", round(float(bv[0].mean()), 3), "/", round(float(bv[1].mean()), 3))

# %%
# Repetition reliability — across-voxel correlation between the two reps,
# computed for the first 30 videos.

videos = sub.videos(direction="fw")[:30]
rep_corr = []
for v in videos:
    b = sub.get_video_betas(v, direction="fw", roi="V1v")
    rep_corr.append(np.corrcoef(b[0], b[1])[0, 1])

print(f"V1v rep-1↔rep-2 correlation, mean over {len(videos)} videos:",
      round(float(np.mean(rep_corr)), 3))

# %%
# Plot the reliability distribution.

import matplotlib.pyplot as plt

fig, ax = plt.subplots(figsize=(5, 3))
ax.hist(rep_corr, bins=15, edgecolor="white")
ax.axvline(0, color="k", linewidth=0.5)
ax.set_xlabel("rep1 ↔ rep2 correlation across V1v voxels")
ax.set_ylabel("# videos")
ax.set_title(f"sub-001 V1v repetition reliability (n={len(videos)} fw videos)")
fig.tight_layout()

# %%
# Averaging across reps is one line.

avg = sub.get_video_betas(1, direction="fw", roi="V1v", average_repeats=True)
print("average shape :", avg.shape)
