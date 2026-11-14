# FreeSurfer reconstructions

{class}`~AOTaccess.freesurfer_access.FreeSurferAccess` resolves the
per-subject FreeSurfer tree in `derivatives/freesurfer_AOT/<sub>/` — the
`mri/` volumes, `surf/` geometry and reconstruction variants such as
`sub-004_old_problematic`.

```python
from AOTaccess.freesurfer_access import FreeSurferAccess

fs = FreeSurferAccess()
fs.subjects()                    # ['sub-001', ..., 'sub-008']
fs.t1_mgz_path(4)                # .../freesurfer_AOT/sub-004/mri/T1.mgz
fs.ribbon_path(4)                # .../sub-004/mri/ribbon.mgz
fs.brainmask_path(4)             # .../sub-004/mri/brainmask.mgz
fs.surf_path(4, "lh", "pial")    # .../sub-004/surf/lh.pial
fs.has_surfaces(4)               # pial + white for both hemispheres?
fs.read_ribbon(4)                # nibabel image (or DataNotFoundError)
```

## Reconstruction variants

A reconstruction directory may carry a suffix (for example the preserved
problematic reconstruction `sub-004_old_problematic`). Pass it either as
`variant=` or as a full directory name:

```python
fs.subject_path(4, variant="old_problematic")
fs.subject_path("sub-004_old_problematic")
```

## T2w fiducial target

The registration display videos outline the cropped fiducial T2w target;
its path comes from the anatomy store:

```python
from AOTaccess.anatomy_access import AnatomyAccess
anat = AnatomyAccess()
anat.t2w_fiducial_path(4, resolution="1p25mm")
anat.fiducial_mask_path(4, resolution="1p25mm")
```

`Config.path("freesurfer")` and `Config.path("transforms")` resolve the two
stores in both settings mode and `root_dir` mode.
