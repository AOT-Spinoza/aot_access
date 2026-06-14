# `AOTSubject` — the primary access object

{class}`~AOTaccess.subject.AOTSubject` binds one subject and exposes a
flat-voxel API anchored by a per-subject brain mask. It composes the
per-domain access classes (GLMsingle, BIDS, ROI, ExpDesign, Preproc) plus
the {mod}`~AOTaccess.brain` and {mod}`~AOTaccess.discovery` helpers — so
callers stop threading `sub=…` through every call.

## Construction

```python
from AOTaccess.subject import AOTSubject
sub = AOTSubject(1)                          # default 2 mm, TYPED_FITHRF_GLMDENOISE_RR
sub = AOTSubject(1, resolution="1p25mm")
sub = AOTSubject("sub-001", resolution="2p0mm")

# Pick the working set explicitly (see brain_mask_and_flat_voxels):
sub = AOTSubject(1, default_mask="ncsnr")    # data-driven signal mask
sub = AOTSubject(1, default_mask="cortex")   # canonical (undilated) GM
```

The default working set is the dilated FreeSurfer cortex GM mask
(`default_mask="cortex_dil"`); see
{doc}`brain_mask_and_flat_voxels` for the other choices and when to pick
each. Pass `config=Config(...)` to override the data root or the
settings file.

## What's on the subject

```{list-table}
:header-rows: 1

* - method
  - returns
  - notes
* - {meth}`~AOTaccess.subject.AOTSubject.sessions`
  - `list[int]`
  - main-task sessions present for this subject
* - {meth}`~AOTaccess.subject.AOTSubject.runs`
  - `list[int]`
  - runs for one session
* - {meth}`~AOTaccess.subject.AOTSubject.videos`
  - `list[int]`
  - unique video ids with per-video betas
* - {meth}`~AOTaccess.subject.AOTSubject.get_brain_mask`
  - `np.ndarray[bool]`
  - 3-D mask implied by `default_mask`; the default is the dilated
    FreeSurfer cortex GM (`"cortex_dil"`)
* - {meth}`~AOTaccess.subject.AOTSubject.get_n_voxels`
  - `int`
  - voxels in the brain mask
* - {meth}`~AOTaccess.subject.AOTSubject.get_gray_matter_mask`
  - `np.ndarray[bool | float]`
  - FreeSurfer cortex GM mask at the subject's resolution — bool for
    `"cortex"` / `"cortex_dil"`, float for `"cortex_sm"` (soft mask)
* - {meth}`~AOTaccess.subject.AOTSubject.get_glmsingle_ncsnr_mask`
  - `np.ndarray[bool]`
  - session-averaged GLMsingle noise-ceiling mask (NCSNR-monotonic),
    cached per `threshold` — what `default_mask="ncsnr"` returns
* - {meth}`~AOTaccess.subject.AOTSubject.get_glmsingle_r2_mask`
  - `np.ndarray[bool]`
  - legacy single-session R² > 0 mask, cached per `ses` — diagnostic
    sibling
* - `affine` / `header`
  - `np.ndarray` / `nib.Nifti1Header`
  - subject-native (T1w) at `resolution`
* - {meth}`~AOTaccess.subject.AOTSubject.get_voxel_coordinates`
  - `(n_vox, 3)`
  - anatomical coords for `brain ∩ roi`
* - {meth}`~AOTaccess.subject.AOTSubject.get_available_rois`
  - `list[str]`
  - ROIs the manifest reports for this subject
* - {meth}`~AOTaccess.subject.AOTSubject.get_roi_mask`
  - `np.ndarray[bool]`
  - flexible query — name / "all" / list, returns the union
* - {meth}`~AOTaccess.subject.AOTSubject.get_betas`
  - `(n_trials, n_vox)`
  - per-session GLMsingle betas; optional `roi=`, `mask=`, `nc_threshold=`
* - {meth}`~AOTaccess.subject.AOTSubject.get_video_betas`
  - `(2, n_vox)` or `(n_vox,)`
  - both repetitions of one video, or the average
* - {meth}`~AOTaccess.subject.AOTSubject.get_run_betas`
  - `(n_stim_trials, n_vox)`
  - composed from per-video files, in trial order, with the correct
    repetition picked per trial
* - {meth}`~AOTaccess.subject.AOTSubject.get_noise_ceiling`
  - `(n_vox,)`
  - per-session noise ceiling, masked
* - {meth}`~AOTaccess.subject.AOTSubject.trial_table`
  - `pd.DataFrame`
  - one row per movie event across all (ses, run)
* - {meth}`~AOTaccess.subject.AOTSubject.trial_info`
  - `pd.DataFrame`
  - a session/run slice of `trial_table`
* - {meth}`~AOTaccess.subject.AOTSubject.to_nifti`
  - `nib.Nifti1Image`
  - 1-D voxel vector → 3-D NIfTI on the subject grid
```

## Selecting voxels — the `roi` / `mask` contract

`get_betas`, `get_video_betas`, `get_run_betas`, `get_noise_ceiling`,
`get_voxel_coordinates` and `to_nifti` all accept the same voxel selector:

- **No selector** → the full brain mask (all voxels where R² is finite > 0).
- **`roi=…`** → a string / list / `"all"` resolved through the ROI manifest;
  always intersected with the brain mask.
- **`mask=…`** → a custom boolean array, either 3-D (`brain_mask.shape`) or
  1-D-within-brain (`n_brain_voxels,`); also intersected with the brain mask.

Use one or the other, never both. See
{doc}`brain_mask_and_flat_voxels` for the round-trip rules.

## Composing a run from per-video files

AOT's per-video betas store two timepoints — the two repetitions of that
video across the subject's sessions, indexed `[0]` and `[1]` on axis 0.
{meth}`~AOTaccess.subject.AOTSubject.get_run_betas` walks `events.tsv` for
the run's trial order and, for each non-blank trial, picks the right
repetition by counting `(video, direction)` appearances chronologically.

```python
run = sub.get_run_betas(ses=1, run=1, roi="V1v")  # (72 trials, n_vox)
```

The trial table powering this is also exposed:

```python
sub.trial_table()              # full DataFrame, 8400 rows for a 10×10 subject
sub.trial_info(ses=1, run=1)   # one run's slice
```

## Reusing one Config

If you build several subjects, share a {class}`~AOTaccess.config.Config`
so you parse `settings.yml` once:

```python
from AOTaccess.config import Config
cfg = Config()
subs = [AOTSubject(i, config=cfg) for i in (1, 2, 3, 4, 5, 7, 8)]
```

For cross-subject convenience, see {doc}`localizers` and the planned
`AOTGroup` (analogous to `Subject` but dispatching over a cohort).
