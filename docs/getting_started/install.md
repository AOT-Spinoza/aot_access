# Installation

`AOTaccess` is a Python package; install from a working copy of the repository
with `pip`:

```bash
git clone <repo-url>
cd aot_access
pip install -e .
```

For tests, linters and the test fixtures:

```bash
pip install -e ".[dev]"
```

For building this documentation site locally:

```bash
pip install -e ".[docs]"
cd docs && sphinx-build -b html . _build/html
```

## Where data lives

The package reads the AOT dataset from the lab's shared filesystem. By default
it resolves every store from {download}`AOTaccess/settings.yml`, which holds
absolute paths to:

- `glmsingle` — single-trial GLM outputs
- `preproced` — preprocessed BOLD volumes
- `bids` — raw BIDS dataset
- `videos`, `pictures`, `video_annotations` — stimulus assets + annotations
- `roi` — ROI library (`MANIFEST.yaml`-driven)
- `localizers` — auxiliary functional-mapping outputs (pRF and friends)

Two ways to override:

1. **Environment variable.** Set `AOT_SETTINGS=/path/to/custom_settings.yml`
   to point the package at a different settings file.
2. **Programmatic.** Build a {class}`~AOTaccess.config.Config` with
   `root_dir=<dataset_root>`; every store is then resolved relative to that
   one root using the canonical layout
   ({mod}`AOTaccess.config._RELATIVE_LAYOUT`).

## Requirements

- Python ≥ 3.9
- `numpy`, `nibabel`, `pandas`, `pyyaml`, `h5py`, `scipy`
- `torch` is an *optional* dependency, used lazily inside the experimental
  `_temp_*` methods of {class}`~AOTaccess.stimulus_info_access.StimuliInfoAccess`;
  the rest of the API loads without it.
