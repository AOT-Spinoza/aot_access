# Preprocessing

```{admonition} Authoring TODO
:class: note
Lab-authored. Describe the `aot_prep` pipeline that produces the
preprocessed BOLD volumes consumed by GLMsingle and the localizer fits.
```

## Pipeline overview

- NORDIC denoising (`rec-nordicstc`).
- Motion correction, slice-timing correction (`stc`).
- Field-map / topup distortion correction.
- Co-registration to the subject's T1w native space.
- Resampling to the EPI grids (`space-T1w_res-1p25mm`, `space-T1w_res-2p0mm`).
- QC outputs (`qa/`).

## Outputs in `derivatives/aot_prep/`

```text
sub-XXX/ses-NN/func/
  sub-XXX_ses-NN_task-AOT_rec-nordicstc_run-NN_part-mag_bold_space-T1w_res-1p25mm.nii.gz
  sub-XXX_ses-NN_task-AOT_rec-nordicstc_run-NN_part-mag_bold_space-T1w_res-2p0mm.nii.gz
sub-XXX/ses-NN/qa/      # quality-control products
sub-XXX/ses-NN/fmap/    # field-map derivatives
sub-XXX/ses-NN/anat/    # session anatomy
```

## Quality control

```{admonition} Authoring TODO
:class: note
Document the QC products under `qa/`, the thresholds used, and any
subject-level QC decisions (e.g. excluded runs).
```
