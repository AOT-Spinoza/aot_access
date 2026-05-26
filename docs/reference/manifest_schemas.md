# Manifest schemas

Two manifest formats power the discovery / path resolution layer.

## ROI manifest — `derivatives/roi/MANIFEST.yaml`

Authored by the {mod}`aot_rois` toolchain. AOTaccess never modifies it;
{class}`~AOTaccess.roi_access.ROIAccess` reads it and resolves paths via
its `path_templates` section.

### Top-level keys

```yaml
manifest_schema_version: 1.x.x
toolchain_version: ...
generated_at: ...
generated_by: aot_rois X.Y.Z
dataset:
  name: ...
  description: ...
subjects:
  sub-XXX:
    rois: [V1v, V1d, ...]
    missing_rois: {}
atlases:
  <name>:
    full_name: ...
    citation: ...
    version: ...
    region_type: ...
    license: ...
    source_files: [...]
    source_hash: ...
    groupings: {}      # planned — see below
rois:
  <roi_name>:
    full_name: ...
    source: ...        # atlas | manual
conservativeness_levels:
  strict: {...}
  balanced: {...}
  liberal: {...}
  thick: {...}
  pyc_nearest: {...}
  pyc_trilinear: {...}
  pyc_line_nearest: {...}
  pyc_line_trilinear: {...}
resolutions:
  T1w: [1p25mm, 2p0mm]
  MNI: [1p25mm]
spaces: [T1w, MNI, fsnative, fsaverage, fsLR]
path_templates:
  <template_key>:
    template: "<relative-path-with-{placeholders}>"
    parameters: [sub, atlas, hemi, roi, res, cons]
    suffix: ...
file_index: {...}
build_status: {completed: true, ...}
```

### Per-atlas `groupings` (proposed extension)

```yaml
atlases:
  wang_2015:
    full_name: Wang Retinotopic Atlas (2015 release)
    citation: ...
    groupings:
      early_visual: [V1v, V1d, V2v, V2d, V3v, V3d]
      ventral_visual: [hV4, VO1, VO2, PHC1, PHC2]
      ...
  rosenke_2021:
    full_name: Rosenke Functional Atlas
    citation: ...
    groupings:
      face:  [OFA, FFA1, FFA2]
      place: [PPA, OPA, MPA]
      ...
  manual_categories:
    full_name: Hand-drawn category-selective ROIs (per-subject)
    native_space: manual_svg
    region_type: cortical
    groupings:
      face:  [pFus_faces, mFus_faces, IOG_faces]
      place: [CoS_places, TOS_places]
      ...
```

Groupings are **namespaced under their atlas**. The same string (`face`)
across two atlases declares *unrelated* groupings; the access layer never
unions across atlases silently. See
{doc}`../user_guide/rois_and_groupings`.

## Localizer manifest — `derivatives/localizers/<name>/manifest.yaml`

One per localizer; authored by the localizer's own pipeline. The pRF
manifest is the canonical worked example, mirrored in the repo at
`schemas/localizer-manifest.example.yaml`.

```yaml
manifest_schema_version: 1.0.0
localizer: prf
kind: parametric              # 'parametric' (model-fit maps) | 'contrast' (GLM stat maps)
description: ...
session: ses-pRF

subjects: [sub-001, ...]

defaults:                     # default values for free template parameters
  model: gauss
  resolution: 2p0mm
  runpart: all
  rec: nordicstc

models:                       # parametric localizers only
  gauss: {full_name: 2D Gaussian pRF}
  norm:  {full_name: Divisive-normalization pRF}

maps:                         # the named result maps
  r2:           {full_name: ..., models: [gauss, norm], template: param_map}
  ecc:          {full_name: ..., models: [gauss, norm], template: param_map}
  ...
  noiseceiling: {full_name: ..., models: [],            template: noiseceiling}

path_templates:
  param_map:
    template: sub-{sub}/prf_fits/params/sub-{sub}_ses-pRF_task-pRF_rec-{rec}_run-{runpart}_model-{model}_stage-iter_space-T1w_res-{resolution}_desc-prf_params_{map}.nii.gz
    parameters: [sub, map, model, resolution, runpart, rec]
  noiseceiling:
    template: sub-{sub}/prep/sub-{sub}_ses-pRF_task-pRF_rec-{rec}_run-noiseceiling_part-mag_bold_space-T1w_res-{resolution}.nii.gz
    parameters: [sub, resolution, rec]
```

Adding a new localizer is *one* file drop — `LocalizerAccess` picks it up
automatically; no code change in AOTaccess.
