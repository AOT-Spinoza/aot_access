# Discovery

Free functions that answer *"what's present?"* without the caller having to
guess subject / session / video / atlas / localizer identifiers. Everything
is read straight from the configured stores; manifests are consulted where
they exist.

```python
from AOTaccess import discovery

discovery.subjects()                  # main-task subjects with GLMsingle output
discovery.sessions(sub=1)             # ints for AOT sessions, strings for localizers
discovery.runs(sub=1, ses=1)          # runs present in preprocessed BOLD
discovery.videos(sub=1, direction="fw")   # unique video ids with per-video betas
discovery.atlases()                   # ROI atlases declared in roi/MANIFEST.yaml
discovery.rois(subject="sub-001")     # ROIs available for one subject
discovery.localizers()                # localizers present in derivatives/localizers/
```

Each call accepts an explicit `config=Config(...)` if you want to point at a
non-default settings file or a relocated dataset root.

When something is missing — e.g. you ask
`discovery.videos(sub=42, direction="rv")` on a subject without `rv` per-video
data — the result is an empty list, not an error.
