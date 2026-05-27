# FAQ

## Where is the data?

On the lab's cluster filesystem; absolute paths are in
`AOTaccess/settings.yml`. Set `AOT_SETTINGS=/path/to/custom.yml` to point
elsewhere, or build `Config(root_dir=…)` for a relocated copy. See
{doc}`../user_guide/config_and_paths`.

## Why `space-T1w` and not `space-fsnative` for the subject-native volume?

Because `fsnative` is a *surface* space in the rest of the field (and in
this dataset). Volumes use `space-T1w` (BIDS / fMRIPrep convention),
always paired with a separate `res-` entity. See
{doc}`../user_guide/naming_conventions`.

## Why do per-video files have two timepoints?

Each unique video is shown twice across a subject's sessions — once in
some ses/run, once in another. The per-video file (`derivatives/glmsingle/
per_video/...desc-NNNNbetaszscore.nii.gz`) stacks both repetitions on axis 0,
shape `(2, X, Y, Z)`. {meth}`~AOTaccess.subject.AOTSubject.get_run_betas`
picks the right repetition per trial by counting `(video, direction)`
appearances chronologically across the subject's `events.tsv`s.

## What about the 1.7 mm data?

There is none for functional derivatives — the project re-processed
everything at `1p25mm` and `2p0mm`. The anatomy fiducial folder retains a
`res-1p7mm` reference grid (sampling target only). The previously-named
`1p7mm` defaults in the API were a bug fixed early in the cleanup.

## Why do `read_*` not return `None` when data is missing?

Because silent `None` is the opposite of graceful. Every `read_*` raises
{class}`~AOTaccess.errors.DataNotFoundError` with the resolved path and
the identifiers that produced it. `DataNotFoundError` is also a subclass
of the builtin `FileNotFoundError`, so legacy `except FileNotFoundError`
handlers keep catching it. See {doc}`../user_guide/error_handling`.

## How do I know what subjects / sessions / videos exist?

Don't guess — use {mod}`AOTaccess.discovery`:
`discovery.subjects()`, `sessions(sub)`, `runs(sub, ses)`,
`videos(sub, direction=…)`, `atlases()`, `rois(subject=…)`,
`localizers()`.

## Where do the on-disk filename conventions come from?

BIDS Derivatives — see {doc}`../user_guide/naming_conventions` and the
BIDS spec at <https://bids-specification.readthedocs.io/>.

## How do I add a new localizer / atlas?

Drop a manifest. For localizers: `derivatives/localizers/<name>/manifest.yaml`
following the localizer schema. For atlases: add to the ROI manifest's
`atlases:` section in the `aot_rois` toolchain. No AOTaccess code change in
either case — both layers are manifest-driven.

## What does the `_temp_*` prefix mean in `StimuliInfoAccess`?

Experimental accessors with hard-coded absolute paths to in-progress
derivatives (Hunyuan / LaVIT / VAE latents and friends). Treat them as
volatile; the non-`_temp_*` counterparts use the stable annotations layout
under `derivatives/stimuli/annotations/`.
