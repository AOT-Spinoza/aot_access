"""
Composing a run — per-video files in trial order
==================================================

{meth}`~AOTaccess.subject.AOTSubject.get_run_betas` walks the run's
``events.tsv`` for trial order and, for each non-blank trial, slices the
right repetition from the per-video file's two timepoints — picking
``rep=0`` for the first chronological appearance of ``(video, direction)``
and ``rep=1`` for the second.
"""

# %%
# Look at the trial table powering this. One row per movie event.

from AOTaccess.subject import AOTSubject

sub = AOTSubject(1)
trials = sub.trial_info(ses=1, run=1)
print("rows (trials in this run) :", len(trials))
print(trials.head(8).to_string(index=False))

# %%
# Stim vs blank counts per run.

import pandas as pd
counts = (
    sub.trial_table()
    .groupby(["ses", "run"])
    .is_blank.value_counts()
    .unstack(fill_value=0)
    .head()
)
counts.columns = ["stim_trials", "blank_trials"]
print(counts.to_string())

# %%
# Compose the run's V1v betas.

run = sub.get_run_betas(ses=1, run=1, roi="V1v")
print("shape         :", run.shape, " (n_stim_trials, n_v1v_voxels)")

# %%
# Plot trials × voxels.

import matplotlib.pyplot as plt
import numpy as np

vmax = float(np.abs(run).max())
fig, ax = plt.subplots(figsize=(8, 3))
im = ax.imshow(run.T, aspect="auto", cmap="RdBu_r", vmin=-vmax, vmax=vmax)
ax.set_xlabel("trial (run-01)")
ax.set_ylabel("V1v voxel")
ax.set_title("sub-001 ses-01 run-01 — V1v betas composed from per-video files")
fig.colorbar(im, ax=ax, fraction=0.04)
fig.tight_layout()
