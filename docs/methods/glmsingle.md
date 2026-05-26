# GLMsingle modelling

```{admonition} Authoring TODO
:class: note
Lab-authored. Describe how the single-trial GLM is fit and what each
output type means.
```

## What is in `derivatives/glmsingle/`

Two parallel stores per subject:

- **`per_session/`** — one fit per (subject, session, resolution), under
  `sub-XXX/ses-NN/space-T1w_res-XpXmm/`. Outputs include `betasmd`,
  `betasmdzscore`, `R2`, `meanvol`, the per-direction `noiseceiling_dir-fw` /
  `noiseceiling_dir-rv`, and the supplementary maps (`HRFindex`, `FRACvalue`,
  `noisepool`, `pcvoxels`, `rrbadness`, …).
- **`per_video/`** — one file per (subject, resolution, direction, video) under
  `sub-XXX/space-T1w_res-XpXmm/{fw,rv}/`. Each file has **two timepoints**
  (axis 0) — the two repetitions of that video across the subject's sessions.

## Models

```text
TYPEA_ONOFF                    -> model-TYPEA
TYPEB_FITHRF                   -> model-TYPEB
TYPEC_FITHRF_GLMDENOISE        -> model-TYPEC
TYPED_FITHRF_GLMDENOISE_RR     -> model-TYPED   # the default for downstream use
```

The mapping is in {data}`AOTaccess.glmsingle_access.MODEL_ENTITY_MAP`.

## Parameters

```{admonition} Authoring TODO
:class: note
Document the GLMsingle parameters that were used: HRF library, denoising
PC count selection, ridge fraction grid, etc. Whatever non-default knobs
were turned.
```
