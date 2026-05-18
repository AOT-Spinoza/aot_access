# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

`AOTaccess` is a read-only Python API for the AOT ("Arrow of Time") 7T fMRI dataset. Every
module locates files on a shared neuroimaging filesystem, builds a BIDS-style filename from
subject/session/run/video identifiers, and loads it (NIfTI via `nibabel`, HDF5 via `h5py`,
CSV/TSV via `csv`, YAML, `.npy`, or torch `.pt`). There is no data-writing or processing code
here — it is purely an accessor layer over derivatives produced elsewhere.

## Setup, lint, test

```bash
pip install -e ".[dev]"            # editable install + black/flake8/pytest
black AOTaccess/ tests/            # formatter (the project's style)
flake8 AOTaccess/ tests/           # linter
pytest                             # run the test suite
pytest -m "not cluster"            # only tests that need no real data
pytest tests/test_config.py        # a single test file
```

`tests/` holds the pytest suite. Tests marked `@pytest.mark.cluster` read the real AOT
dataset and are auto-skipped when it is unreachable (`tests/conftest.py`); the rest run
anywhere against synthetic fixtures. The `AOTaccess/notebooks/test_*.ipynb` notebooks
predate the suite — exploratory usage references, not maintained tests.

`torch` is an optional dependency, imported lazily inside the `_temp_*` methods of
`stimulus_info_access.py` so the rest of the API loads without it.

## Architecture

- `aot_access.py` — `AOTAccess(root_path=None)` is the facade. It instantiates and delegates to
  the per-domain access classes. It wires up **7 of the 11** access classes:
  `GLMSingleAccess`, `ExpDesignAccess`, `StimuliInfoAccess`, `BidsAccess`, `MemoryScoreAccess`,
  `PreprocedAccess`, `ROIAccess`. `PrfAccess`, `LocalizerAccess`, `ExpLogAccess`, and
  `AnatomyAccess` are standalone — use them directly, not through the facade.
- Each `*_access.py` defines exactly one `*Access` class scoped to one data domain
  (glmsingle betas, preprocessed BOLD, raw BIDS, experiment design YAMLs, behavioral memory
  scores, pRF fits, stimulus annotations, experiment logs, anatomy, ROIs, localizers).

### ROIAccess is manifest-driven

`roi_access.py` does not hard-code any path layout. It loads `MANIFEST.yaml` from the ROI
derivatives folder and resolves the `path_templates` section (each template names its own
`{sub}/{atlas}/{hemi}/{roi}/{res}/{cons}` placeholders). `resolve(template_key, **params)`
is the generic resolver; `mask_path`/`read_mask`, `dseg_path`/`read_dseg`,
`surface_label_path`/`read_surface_label`, and `group_probseg_path`/`read_group_probseg`
are ergonomic wrappers. Discovery methods (`atlases`, `rois`, `subjects`, `spaces`,
`conservativeness_levels`, `resolutions`) read straight from the manifest. When the ROI
toolchain regenerates the manifest, this module follows it with no code change.

The ROI `fsnative` volumetric space is the **same voxel grid as the EPI space** used by
GLMsingle and aot_prep. So an `fsnative` ROI mask at a matching resolution indexes a betas
or BOLD array directly — `AOTAccess.extract_betas_in_roi` relies on this.

### Localizer derivatives

A "localizer" is an auxiliary functional-mapping experiment (pRF retinotopy, an fLOC
category localizer, a Harvey-style duration mapper). Localizer sessions are preprocessed and
modelled through the *shared* pipelines (`aot_prep`, `glmsingle`, keyed by session name like
`ses-pRF`/`ses-fLOC`); only the final analysis products are localizer-specific and live
under `derivatives/localizers/<name>/`. `LocalizerAccess` (`localizer_access.py`) is
manifest-driven exactly like `ROIAccess`: each localizer carries its own `manifest.yaml`
(localizers are diverse — manifests are kept separate) declaring subjects, result maps,
defaults, and `path_templates`. `read_map(localizer, sub, map, **params)` resolves any of
them. `schemas/localizer-manifest.example.yaml` documents the manifest schema.

pRF is the first localizer: it lives at `derivatives/localizers/prf/` with a `manifest.yaml`.
`prf_access.py` (`PrfAccess`) is now a thin pRF-specific convenience wrapper over
`LocalizerAccess` — `read_param` / `read_noiseceiling` with optional R2 masking. New code can
use `LocalizerAccess` directly with `localizer="prf"`.

### Configuration and path resolution

`config.py` centralises path resolution. A `Config` resolves every derivative store either
from `AOTaccess/settings.yml` (the default — absolute cluster paths) or, when built with
`root_dir=<dataset root>`, relative to that root via the canonical `_RELATIVE_LAYOUT`.
`settings.yml` can be overridden with the `AOT_SETTINGS` env var or an explicit
`settings_path`.

Every access class takes `(root_dir=None, config=None)` and holds a `Config`; the facade
builds one `Config` and shares it with all sub-accessors. Add a derivative by editing
`settings.yml` (and `_RELATIVE_LAYOUT`), not each module. `run_number` (10 runs/session)
lives in the settings `parameters` section, read via `Config.param`.

### Dual-cluster fallback

Code runs on two clusters with different mount points: VU
(`/research/FGB-CognitivePsychology-Knapen/...`) and Snellius (`/projects/prjs1914/...`).
`Config.anatomy_root()` probes a list of candidate anatomy roots and returns the first that
`.exists()`; many `_temp_*` methods do the same inline. When adding cross-cluster file
access, follow this "try each candidate, pick first existing" pattern.

### `_temp_*` methods

Methods prefixed `_temp_` (heavily in `stimulus_info_access.py`, also `anatomy_access.py`)
are experimental accessors with **hardcoded absolute paths** to in-progress derivatives (VAE
latents, Hunyuan/LaVIT embeddings, motion energy, etc.). The non-`_temp_` counterparts read
from the stable BIDS-derivatives layout under the `video_annotations` directory. Prefer the
stable methods; treat `_temp_*` paths as volatile.

### GLMsingle BIDS naming

`glmsingle_access.py` holds the filename builders: `MODEL_ENTITY_MAP` maps GLM type names
(e.g. `TYPED_FITHRF_GLMDENOISE_RR`) to short BIDS entities (`TYPED`), and
`build_per_session_bids_nii` / `build_per_video_bids_nii` / `build_figure_bids_png` assemble
filenames. Any change to the on-disk naming scheme goes through these helpers.

## Conventions and gotchas

- **Resolutions on disk are `2p0mm` and `1p25mm` only — there is no 1.7 mm data.** The
  default everywhere is `2p0mm`. The string is encoded `2p0mm` in `glmsingle_access.py`,
  `preproced_access.py`, and `roi_access.py`, but `2.0mm` (literal dot) in `prf_access.py` —
  match the convention of the module you are editing. Do not reintroduce `1p7mm`/`1.7mm`.
- Identifier formatting lives in `naming.py` (`fmt_sub`/`fmt_ses`/`fmt_run`/`fmt_video`).
  Subjects/runs/videos zero-pad; `fmt_ses` zero-pads integer sessions but passes string
  sessions (`pRF`, `fLOC`) through unchanged — use these helpers, never inline `f"{ses:02d}"`.
- `read_*` methods raise `DataNotFoundError` with the resolved path when a file is missing —
  they do not return `None`. `DataNotFoundError` subclasses both `AOTAccessError` (the base
  for every API error, in `errors.py`) and the builtin `FileNotFoundError`.
- `direction` is `"fw"` (forward) or `"rv"` (reversed) — the arrow-of-time manipulation.
- Some methods are unimplemented stubs that `pass`: `ExpDesignAccess.get_session_id_from_video_id`
  (also missing `self`, yet called by `AOTAccess.read_session_from_video`),
  `MemoryScoreAccess.memorability_list_from_all_sessions`/`read_memory_edf`, and
  `ExpLogAccess.get_eyetrack_edf`. Treat these as not-yet-working.
