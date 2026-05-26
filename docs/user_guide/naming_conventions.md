# Naming conventions

The AOT dataset follows a BIDS-compliant filename convention. The API
enforces these names in the paths it builds and accepts.

## Spaces

| representation | subject-native | standard / group |
|---|---|---|
| **volume**  | `space-T1w`         | `space-MNI` (`MNI152NLin2009cAsym`) |
| **surface** | `space-fsnative`    | `space-fsaverage` |
| **grayordinate** | —              | `space-fsLR` (CIFTI, with `den-32k` / `den-170k`) |

- `space-T1w` and `space-MNI` are always paired with a separate `res-` entity
  (`res-1p25mm` / `res-2p0mm`).
- `fsnative` and `fsaverage` are *surface* labels only. The API rejects them
  in volume methods and vice-versa, with a hint to use the right method.
- `MNI` is the short, unambiguous label for the standard volume frame; the
  BIDS-canonical `MNI152NLin2009cAsym` is also accepted as a transitional
  alias.

## Resolution

Always a separate `res-` entity, never bundled into `space-`:

```text
sub-001_..._space-T1w_res-2p0mm_..._mask.nii.gz   ✓
sub-001_..._space-T1w2p0mm_..._mask.nii.gz        ✗
```

The on-disk encoding is `2p0mm` / `1p25mm` (no underscore, `p` for the
decimal). Functional data exists at `2p0mm` and `1p25mm`; there is no
1.7 mm functional data — the anatomy fiducial folder still carries a
`res-1p7mm` reference grid (sampling target).

## Entity ordering — BIDS-canonical

The BIDS Derivatives spec defines this order for atlas-based files:

```text
<source-entities>_space-X_atlas-Y_res-Z_label-W_desc-D_<suffix>
```

Source entities (`sub-`, `ses-`, `hemi-`, …) come first; `hemi-` immediately
precedes `space-`. Putting the pieces together:

```text
sub-001_hemi-L_space-T1w_atlas-wang_2015_res-2p0mm_label-V1v_cons-balanced_mask.nii.gz
sub-001_space-MNI_atlas-rosenke_2021_res-1p25mm_label-FFA1_cons-balanced_mask.nii.gz
sub-001_hemi-L_space-fsnative_atlas-wang_2015_label-V1v.label.gii
group_hemi-L_space-fsaverage_atlas-wang_2015_mpm.annot
group_space-fsLR_den-32k_atlas-wang_2015_dlabel.nii
```

`cons-` is a custom (non-BIDS) entity defined by the ROI library. It sits
right before `desc-` / `<suffix>`.

## Direction

Stimulus direction is encoded as `fw` (forward) or `rv` (reversed) — the
arrow-of-time manipulation. Lives in stimulus filenames (`0001_fw.mp4`,
`0001_rv.mp4`) and in directory names under `glmsingle/per_video/.../fw/`
and `/rv/`.

## Models

GLMsingle's four model types map to short BIDS entity values:

```text
TYPEA_ONOFF                  ->  model-TYPEA
TYPEB_FITHRF                 ->  model-TYPEB
TYPEC_FITHRF_GLMDENOISE      ->  model-TYPEC
TYPED_FITHRF_GLMDENOISE_RR   ->  model-TYPED
```

The mapping is in {data}`AOTaccess.glmsingle_access.MODEL_ENTITY_MAP`.

## See also

- {doc}`../reference/folder_structure` — the full canonical layout under
  `derivatives/`.
- {doc}`../reference/manifest_schemas` — ROI and localizer manifest schemas.
