"""
Qwen embeddings — semantic similarity between videos
=====================================================

Each forward-direction video has a one-sentence Qwen-VL description and a
matching 2048-d text-embedding-v4 vector. Loading a handful, computing
pairwise similarity, and showing the nearest neighbours for one seed.
"""

# %%
# Pipeline metadata (model, embedding dimensionality, format).

from AOTaccess.stimulus_info_access import StimuliInfoAccess

stim = StimuliInfoAccess()
desc_meta = stim.read_qwen_description_meta()
emb_meta = stim.read_qwen_embedding_meta()

print("description model :", desc_meta["model"]["name"])
print("embedding model   :", emb_meta["model"]["name"])
print("embedding dim     :", emb_meta["generation"]["embedding_dimensions"])
print("direction scope   :", desc_meta["generation"]["direction_scope"])

# %%
# Load embeddings + descriptions for 50 videos (fw only — that's the scope).

import numpy as np

videos = list(range(1, 51))
embeddings = np.stack([stim.read_qwen_embedding(v, "fw") for v in videos])
descriptions = [stim.read_qwen_description(v, "fw") for v in videos]
print("embeddings matrix :", embeddings.shape)

# %%
# Cosine-similarity matrix.

emb_n = embeddings / np.linalg.norm(embeddings, axis=1, keepdims=True)
sim = emb_n @ emb_n.T  # (n_videos, n_videos)

import matplotlib.pyplot as plt

fig, ax = plt.subplots(figsize=(4, 3.5))
im = ax.imshow(sim, cmap="magma", vmin=0, vmax=1)
ax.set_xlabel("video idx")
ax.set_ylabel("video idx")
ax.set_title("Qwen embedding cosine similarity (50 fw videos)")
fig.colorbar(im, ax=ax, fraction=0.04)
fig.tight_layout()

# %%
# Nearest neighbours of the seed (excluding itself).

seed = 0
order = np.argsort(-sim[seed])
print(f"\nSeed video {videos[seed]:04d}_fw:")
print(f"  {descriptions[seed].strip()[:90]}")
print("\nNearest neighbours:")
for j in order[1:6]:
    print(f"  {videos[j]:04d}_fw (cos={sim[seed, j]:.3f}): {descriptions[j].strip()[:90]}")
