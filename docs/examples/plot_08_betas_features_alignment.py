"""
Betas × motion-energy × Qwen — aligning brain, low-level and semantic
======================================================================

The headline encoding-flavoured example. Build three matrices over the
same set of videos —

* ROI betas (subject's V1v response, averaged across the 2 repetitions),
* motion-energy features (mean over the 60 timepoints — a quick summary),
* Qwen text embeddings (already one vector per video),

then visualise three representational-similarity matrices side by side.
A glance at how brain similarity, low-level visual similarity, and
semantic similarity compare for the same stimuli.
"""

# %%
# Setup — pick a subject and a set of fw videos.

import numpy as np
from AOTaccess.subject import AOTSubject
from AOTaccess.stimulus_info_access import StimuliInfoAccess

sub = AOTSubject(1)
stim = StimuliInfoAccess()

videos = sorted(sub.videos(direction="fw"))[:40]
print(f"Using {len(videos)} fw videos.")

# %%
# Three matrices, one row per video.

betas_v1v = np.stack([
    sub.get_video_betas(v, direction="fw", roi="V1v", average_repeats=True)
    for v in videos
])  # (n_videos, n_v1v_voxels)

moten = np.stack([
    stim.read_motion_energy_features(v, direction="fw", highest_freq=16).mean(axis=0)
    for v in videos
])  # (n_videos, n_moten_channels)

qwen = np.stack([stim.read_qwen_embedding(v, direction="fw") for v in videos])
# (n_videos, 2048)

print("V1v betas  :", betas_v1v.shape)
print("moten mean :", moten.shape)
print("qwen       :", qwen.shape)

# %%
# Representational similarity per modality (Pearson correlation, video × video).

def rsm(X):
    Z = (X - X.mean(axis=1, keepdims=True)) / X.std(axis=1, keepdims=True)
    return (Z @ Z.T) / X.shape[1]

S_brain = rsm(betas_v1v)
S_moten = rsm(moten)
S_qwen = rsm(qwen)

# %%
# Side-by-side plot.

import matplotlib.pyplot as plt

fig, axes = plt.subplots(1, 3, figsize=(11, 3.4))
for ax, S, title in zip(
    axes,
    [S_brain, S_moten, S_qwen],
    ["sub-001 V1v betas", "motion-energy 16-Hz (time-mean)", "Qwen embedding"],
):
    vmax = max(abs(S.min()), abs(S.max()))
    im = ax.imshow(S, cmap="RdBu_r", vmin=-vmax, vmax=vmax)
    ax.set_title(title)
    ax.set_xticks([]); ax.set_yticks([])
    fig.colorbar(im, ax=ax, fraction=0.045)
fig.suptitle(f"Representational similarity over {len(videos)} fw videos")
fig.tight_layout()

# %%
# How well does each feature space explain the others' video-similarity
# pattern? Correlation of the upper-triangles.

iu = np.triu_indices(len(videos), k=1)
b = S_brain[iu]; m = S_moten[iu]; q = S_qwen[iu]

print(f"\nUpper-triangle correlations (n pairs = {len(b)}):")
print(f"  V1v betas   ↔ moten 16-Hz  : r = {np.corrcoef(b, m)[0,1]:.3f}")
print(f"  V1v betas   ↔ Qwen embed   : r = {np.corrcoef(b, q)[0,1]:.3f}")
print(f"  moten 16-Hz ↔ Qwen embed   : r = {np.corrcoef(m, q)[0,1]:.3f}")
