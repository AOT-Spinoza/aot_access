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
pip install -e ".[dev]"      # editable install + black/flake8/pytest
black AOTaccess/             # formatter (the project's style)
flake8 AOTaccess/            # linter
```

There is **no pytest suite** despite `pytest` being a declared dev dependency. The
`AOTaccess/notebooks/test_*.ipynb` notebooks are the de-facto tests — one per access class.
To "run a test", open the relevant `test_<module>_access.ipynb` and execute it; it exercises
that class against real data on the cluster. `all_function_usage_display.ipynb` is a usage
reference. Note these notebooks import modules directly (`sys.path.append('..')` then
`from glmsingle_access import GLMSingleAccess`), not through the installed package.

Two runtime dependencies are used but **not declared** in `pyproject.toml`: `torch`
(`stimulus_info_access.py`, imported lazily inside the `_temp_*` methods that need it) and
`hedfpy` (`explog_access.py`, currently commented out).

## Architecture

- `aot_access.py` — `AOTAccess(root_path)` is the facade. It instantiates and delegates to
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
them. `schemas/localizer-manifest.example.yaml` is the worked pRF example / schema spec.

**Transition state:** the pRF data still lives at `derivatives/prf/` and `prf_access.py`
(`PrfAccess`) reads it there. It will move to `derivatives/localizers/pRF/`; after the move
`PrfAccess` is superseded by `LocalizerAccess` and can be retired. `LocalizerAccess` already
targets the post-move layout — it will not resolve real files until the move happens.

Note: `GLMSingleAccess`/`PreprocedAccess` format sessions as `ses-{ses:02d}`, which breaks
on string sessions like `ses-fLOC`. They need string-session support before localizer betas
can be read through them (`BidsAccess` already branches on `type(ses) is int`).

### Path resolution — two modes

Every access class constructor takes `root_dir: Path = None` and branches on it:

- `root_dir=None` → reads absolute cluster paths from `AOTaccess/settings.yml`
  (`/research/FGB-CognitivePsychology-Knapen/shared/2024/visual/AOT/...`).
- `root_dir=<Path>` → builds all paths as subdirectories of that root (e.g.
  `root_dir / "per_session"`, `root_dir / "bids"`).

`settings.yml` is the single source of truth for default paths and `run_number` (10 runs per
session). When data moves on the cluster, edit `settings.yml`, not the modules.
`BidsAccess.__init__` keeps a legacy first positional arg `bids_dir` (kept for backward
compatibility) before `root_dir`; both default to `None` and fall back to `settings.yml`.

### Dual-cluster fallback

Code runs on two clusters with different mount points: VU
(`/research/FGB-CognitivePsychology-Knapen/...`) and Snellius (`/projects/prjs1914/...`).
`_resolve_anatomy_root()` (defined separately, with *different* candidate lists, in both
`anatomy_access.py` and `glmsingle_access.py`) and many `_temp_*` methods probe a list of
candidate paths and pick the first that `.exists()`. When adding cross-cluster file access,
follow this "try each candidate, pick first existing" pattern.

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
- Identifiers are integers and get zero-padded into filenames: `sub-{sub:03d}`,
  `ses-{ses:02d}`, `run-{run:02d}`, video `{video_id:04d}`. Several methods also accept a
  string `ses` (e.g. `"3Tanat"`, `"pRF"`) and branch on `type(ses) is int`.
- `read_*` methods that load a volume return `None` (not raise) when the file is missing —
  except `read_shape`/`read_R2_mask`, which raise `FileNotFoundError`. Callers must
  null-check.
- `direction` is `"fw"` (forward) or `"rv"` (reversed) — the arrow-of-time manipulation.
- Some methods are unimplemented stubs that `pass`: `ExpDesignAccess.get_session_id_from_video_id`
  (also missing `self`, yet called by `AOTAccess.read_session_from_video`),
  `MemoryScoreAccess.memorability_list_from_all_sessions`, `read_memory_edf`,
  `ExpLogAccess.get_eyetrack_edf`. Treat these as not-yet-working.
