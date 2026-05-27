# Quickstart

Five-line orientation. Bind to a subject, ask for betas restricted to V1v,
get an `(n_trials, n_voxels)` flat array, write a prediction back as a NIfTI.

```python
from AOTaccess.subject import AOTSubject

sub = AOTSubject(1)                            # bind subject 1
betas = sub.get_betas(ses=1, roi="V1v")        # (720 trials, ~570 voxels)
nc    = sub.get_noise_ceiling(ses=1, roi="V1v")
sub.to_nifti(betas.mean(0), "v1v_mean.nii.gz", roi="V1v")
```

The same call with extra filtering — voxels above an R²-based brain mask
**and** above a noise-ceiling threshold:

```python
betas = sub.get_betas(ses=1, roi="V1v", nc_threshold=0.2)
```

A run's worth of trials, composed by reading the per-video files in event
order (the per-video file has two timepoints — one per repetition — and
{meth}`~AOTaccess.subject.AOTSubject.get_run_betas` picks the right one for
each trial automatically):

```python
run_betas = sub.get_run_betas(ses=1, run=1, roi="V1v")  # (72 trials, n_vox)
```

Discovery — without guessing identifiers:

```python
from AOTaccess import discovery

discovery.subjects()                  # [1, 2, 3, 4, 5, 7, 8]
discovery.sessions(1)                 # [1, ..., 10]
discovery.videos(1, direction="fw")   # 1800 unique video ids
discovery.atlases()                   # ['manual', 'wang_2015', 'glasser_2016', ...]
discovery.localizers()                # ['prf', ...]
```

ROIs without inventing names — `"all"`, single name, list, atlas:

```python
sub.get_roi_mask("V1v")                            # one ROI
sub.get_roi_mask("all")                            # every available ROI, unioned
sub.get_roi_mask(["V1v", "V1d", "V2v", "V2d"])     # custom union
sub.get_available_rois()                           # what this subject has
```

Next:

- [Subject API walkthrough](../user_guide/subject_api.md)
- [Brain mask + flat-voxel convention](../user_guide/brain_mask_and_flat_voxels.md)
- [ROIs & groupings](../user_guide/rois_and_groupings.md)
- [Examples gallery](../auto_examples/index.rst)
