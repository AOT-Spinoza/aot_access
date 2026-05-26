"""
Online behavior — identifiability table
========================================

The condensed online-behavior table holds one row per (video, direction):
n raters, identifiability score with 95% CI, raw and quality-weighted
direction accuracy, mean confidence and RT, and an identifiability
decile. The detailed per-video YAMLs hold one entry per online subject.
"""

# %%
# The full table.

from AOTaccess.stimulus_info_access import StimuliInfoAccess

stim = StimuliInfoAccess()
df = stim.read_online_behavior_table()
print(df.shape, "rows × cols")
print(df.head(4).to_string(index=False))

# %%
# Distribution of identifiability across all videos.

import matplotlib.pyplot as plt
import numpy as np

fig, ax = plt.subplots(figsize=(6, 3))
ax.hist(df.identifiability_score, bins=40, edgecolor="white")
ax.axvline(0, color="k", linewidth=0.5)
ax.set_xlabel("identifiability score")
ax.set_ylabel("# (video, direction)")
ax.set_title(f"Online identifiability distribution (N = {len(df)})")
fig.tight_layout()

# %%
# Forward vs reversed identifiability — paired view.

fw = df[df.direction == "forward"].set_index("source_id").identifiability_score
rv = df[df.direction == "backward"].set_index("source_id").identifiability_score
both = fw.to_frame("fw").join(rv.rename("rv"), how="inner")

fig, ax = plt.subplots(figsize=(4, 4))
ax.scatter(both.fw, both.rv, s=4, alpha=0.3)
ax.plot([-1, 1], [-1, 1], "k--", linewidth=0.5)
ax.axhline(0, color="k", linewidth=0.3); ax.axvline(0, color="k", linewidth=0.3)
ax.set_xlabel("forward identifiability")
ax.set_ylabel("reversed identifiability")
ax.set_title("Forward vs reversed — paired videos")
ax.set_aspect("equal")
fig.tight_layout()

# %%
# The most-identifiable and least-identifiable videos.

top = df.sort_values("identifiability_score", ascending=False).head(5)
bot = df.sort_values("identifiability_score").head(5)
print("\nTop-5 identifiable:")
print(top[["name", "identifiability_score", "direction_accuracy_weighted", "n_views"]]
      .to_string(index=False))
print("\nBottom-5:")
print(bot[["name", "identifiability_score", "direction_accuracy_weighted", "n_views"]]
      .to_string(index=False))

# %%
# Pull the per-subject responses for one top video.

top_video = top.iloc[0]
detail = stim.read_video_behavior(int(top_video.source_id),
                                  "fw" if top_video.direction == "forward" else "rv")
print(f"\n{top_video['name']} — per-subject responses:")
for r in detail["responses"][:6]:
    flag = "✓" if r["correct"] else "✗"
    print(f"  {r['subject']}: {flag} confidence={r['confidence']}, "
          f"RT={r['direction_rt_ms']} ms")
