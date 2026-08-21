# ROIs and groupings

The ROI library is manifest-driven. Every path is resolved from
`derivatives/roi/MANIFEST.yaml` — never hand-coded — so the API automatically
follows the structure the {mod}`aot_rois` toolchain emits.

## What's in the manifest

- **Atlases** — `manual_*`, `wang_2015`, `glasser_2016`, `rosenke_2021`,
  `fs_aparc_*`, `fs_aseg`, plus any future atlases. Each carries its citation,
  source files, license, version, and (planned) per-atlas `groupings:`.
- **ROIs** — every label defined in the library, with `full_name` and `source`.
- **Subjects** — per-subject ROI lists and `missing_rois`.
- **Spaces** — `T1w` (subject native volume), `MNI` (group volume),
  `fsnative` / `fsaverage` (surfaces), `fsLR` (CIFTI).
- **Conservativeness levels** — `strict`, `balanced`, `liberal`, `thick`,
  the four pycortex samplers (`pyc_nearest`, `pyc_trilinear`,
  `pyc_line_nearest`, `pyc_line_trilinear`), and `labels` (`fs_aseg` only).
- **Resolutions** — per space: `T1w: [1p25mm, 2p0mm]` but `MNI: [1p25mm]`.
- **`path_templates`** — the BIDS-canonical filename templates the toolchain
  emits; the access layer resolves any path through them.
- **`build_status`** — the toolchain's own report on the last build
  (`completed`, `failed_outputs`, `warnings`), surfaced by
  {meth}`~AOTaccess.roi_access.ROIAccess.build_status` and friends.

## Reading a single ROI

```python
from AOTaccess.subject import AOTSubject
sub = AOTSubject(1)

mask = sub.get_roi_mask("V1v")         # 3-D bool, on the T1w 2p0mm grid by default
```

Defaults: `atlas="wang_2015"`, `space="T1w"`, `hemi=None` (bilateral), with
`res` and `cons` resolved against what the store actually holds. Override any
of them:

```python
sub.get_roi_mask("FFA1", atlas="rosenke_2021", cons="strict", hemi="R")
sub.get_roi_mask("V1v", res="1p25mm")               # different EPI grid
```

Spaces and atlases are not built uniformly, so a single global default cannot
be right everywhere: MNI volumes exist only at `1p25mm`, and `fs_aseg` ships
only `cons="labels"` where the surface-sampled atlases ship the other eight.
Leaving `res`/`cons` unset picks the built variant; ask the store directly
when you want to know what that is:

```python
roi.available_resolutions(6, atlas="wang_2015")     # ['1p25mm', '2p0mm']
roi.available_cons(6, atlas="fs_aseg")              # ['labels']
roi.cons_info("labels")["description"]              # why that level exists
```

## Flexible queries — name / list / "all"

```python
sub.get_roi_mask("V1v")                              # single name
sub.get_roi_mask("all")                              # every ROI of `atlas`, unioned
sub.get_roi_mask("all", atlas="glasser_2016")        # ... of a different atlas
sub.get_roi_mask(["V1v", "V1d", "V2v", "V2d"])       # custom union
```

`"all"` means every ROI **of the requested atlas** available for the subject.
{meth}`~AOTaccess.roi_access.ROIAccess.rois` pools names across all atlases, so
use {meth}`~AOTaccess.roi_access.ROIAccess.atlas_rois` when you need the
per-atlas partition.

The result is always a single 3-D bool mask — the union of every match,
intersected with the subject's brain mask. Use it directly with
{meth}`~AOTaccess.subject.AOTSubject.get_betas` etc., or with
{meth}`~AOTaccess.subject.AOTSubject.to_nifti` to round-trip predictions.

## Per-atlas `groupings` (planned)

`get_roi_mask` will accept `(atlas, group)` tuples once the `aot_rois`
toolchain emits the `groupings:` block per atlas — see
{doc}`../reference/manifest_schemas`. The query API then becomes:

```python
sub.get_roi_mask(("rosenke_2021", "face"))
sub.get_roi_mask([("rosenke_2021", "face"), ("rosenke_2021", "place")])
```

By construction, groupings in different atlases never collide — a "face"
group from `rosenke_2021` and a "face" group from a hand-drawn atlas are
distinct, and the resolver never unions across atlases silently.

## Direct ROIAccess

The lower-level {class}`~AOTaccess.roi_access.ROIAccess` is what
{class}`~AOTaccess.subject.AOTSubject` composes; reach for it when you want
the path itself, or surface labels, or group-level files:

```python
from AOTaccess.roi_access import ROIAccess
roi = ROIAccess()

roi.atlases()
roi.rois(subject="sub-001")
roi.atlas_rois("wang_2015")                         # just this atlas's ROIs
roi.conservativeness_levels()
roi.template_keys()                                 # all path templates in the manifest

roi.provenance()                                    # toolchain, schema version, build date
roi.is_complete()                                   # did the last build finish?
roi.build_warnings()                                # what the toolchain flagged
roi.failed_outputs()                                # products it could not write

roi.mask_path(1, "V1v", atlas="wang_2015")          # the resolved Path
roi.read_mask(1, "V1v")                             # the boolean ndarray

roi.read_surface_label(1, "V1v", hemi="L")          # gifti label data
roi.read_group_probseg("V1v", hemi="L")             # MNI probabilistic seg
roi.resolve("cifti_32k_dlabel", atlas="wang_2015")  # any template by name
```
