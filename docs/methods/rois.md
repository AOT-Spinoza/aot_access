# ROI library

```{admonition} Authoring TODO
:class: note
Lab-authored. Describe the `aot_rois` toolchain and the per-atlas drawing
protocols.
```

## What ships in `derivatives/roi/`

- A `MANIFEST.yaml` declaring atlases, ROIs, subjects, spaces, resolutions,
  conservativeness levels, and `path_templates` — see
  {doc}`../reference/manifest_schemas`.
- Per-subject ROI products in the canonical BIDS layout, with `space-T1w`,
  `space-MNI`, `space-fsnative` and `space-fsaverage` variants.
- Group-level products in `group/space-MNI/...`, `group/space-fsaverage/...`,
  and CIFTI dlabels under `group/space-fsLR/`.

## Atlases

- **`wang_2015`** — retinotopic atlas (Wang et al., 2015).
- **`glasser_2016`** — HCP multi-modal parcellation (Glasser et al., 2016).
- **`rosenke_2021`** — occipitotemporal functional atlas (Rosenke et al., 2021).
- **`fs_aparc_dk` / `fs_aparc_dkt` / `fs_aparc_a2009s` / `fs_aseg`** —
  FreeSurfer parcellations.
- **`manual_retinotopy`** — hand-drawn retinotopic ROIs (per subject).
- **`manual_categories`** — hand-drawn category-selective ROIs (per subject).

## Conservativeness levels

Eight levels available in the manifest: `strict`, `balanced`, `liberal`,
`thick`, and four pycortex samplers (`pyc_nearest`, `pyc_trilinear`,
`pyc_line_nearest`, `pyc_line_trilinear`). Pick by use case;
`balanced` is the default in the API.

## Drawing protocols

```{admonition} Authoring TODO
:class: note
For each hand-drawn atlas: which sessions / data were viewed during
drawing, who the annotators were, how disagreements were resolved.
```
