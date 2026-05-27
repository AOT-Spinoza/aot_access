"""
Discovery — what's in the dataset
==================================

The {mod}`AOTaccess.discovery` module answers "what's actually present?"
without the caller having to guess subject / session / video / atlas /
localizer identifiers.
"""

# %%
# Top-level discovery — every call hits the filesystem (or a manifest)
# and returns sorted identifiers.

from AOTaccess import discovery

print("subjects   :", discovery.subjects())
print("atlases    :", discovery.atlases())
print("localizers :", discovery.localizers())

# %%
# Per-subject discovery.

sub = 1
print(f"sessions for sub-{sub:03d}      :", discovery.sessions(sub))
print(f"runs in (sub-{sub:03d}, ses-01) :", discovery.runs(sub, 1))

fw_videos = discovery.videos(sub, direction="fw")
rv_videos = discovery.videos(sub, direction="rv")
print(f"fw videos for sub-{sub:03d}     : {len(fw_videos)} (min={fw_videos[0]}, max={fw_videos[-1]})")
print(f"rv videos for sub-{sub:03d}     : {len(rv_videos)}")

# %%
# ROI discovery via the manifest.

print(f"ROIs in manifest               : {len(discovery.rois())}")
print(f"ROIs available for sub-{sub:03d}   : {len(discovery.rois(subject=f'sub-{sub:03d}'))}")
print("first 10 ROIs                  :", discovery.rois()[:10])
