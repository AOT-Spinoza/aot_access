# Dataset at a glance

```{admonition} Authoring TODO
:class: note
Lab-authored content. Add: subject count, session structure, trial counts,
unique-video count, scan parameters at a glance, dataset version / DOI,
acknowledgements.
```

## Main task — AOT

The Arrow-of-Time task. Each trial presents a short video clip either
forward (`fw`) or reversed (`rv`); subjects make a behavioural judgement
about which direction the clip was played.

- **Subjects:** 7 (1, 2, 3, 4, 5, 7, 8)
- **Sessions per subject:** 10
- **Runs per session:** 10
- **Movie events per run:** 84 (72 stimulus + 12 blank)
- **Unique videos per subject:** 1,800 (each presented twice across sessions,
  in either `fw` or `rv`)

## Auxiliary localizer sessions

Each subject also has localizer sessions — see {doc}`../user_guide/localizers`.

- `ses-pRF` — population receptive field mapping (current).
- `ses-fLOC` — category-selective fLOC localizer (planned).
- `ses-time` — Harvey-style duration / time mapper (planned).

## Spaces

See {doc}`../user_guide/naming_conventions` for the full convention.

| representation | subject-native | standard / group |
|---|---|---|
| volume | `space-T1w` | `space-MNI` |
| surface | `space-fsnative` | `space-fsaverage` |
| grayordinate | — | `space-fsLR` (CIFTI) |

Volumetric resolutions: `res-2p0mm` and `res-1p25mm`.

## Citation

```{admonition} Authoring TODO
:class: note
Add the dataset citation (DOI / paper) once available.
```
