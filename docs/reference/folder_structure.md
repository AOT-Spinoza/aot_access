# Folder structure

The canonical layout under `derivatives/`. All filenames follow the BIDS
conventions described in {doc}`../user_guide/naming_conventions`.

## `derivatives/aot_prep/` — preprocessed BOLD

```text
sub-XXX/ses-NN/
  func/
    sub-XXX_ses-NN_task-AOT_rec-nordicstc_run-NN_part-mag_bold_space-T1w_res-{1p25mm,2p0mm}.nii.gz
  qa/         # quality-control products
  fmap/       # field-map derivatives
  anat/       # session anatomy
```

## `derivatives/glmsingle/` — single-trial GLMs

Two stores in parallel:

```text
per_session/sub-XXX/ses-NN/space-T1w_res-XpXmm/
  sub-XXX_ses-NN_space-T1w_res-XpXmm_model-{TYPEA,TYPEB,TYPEC,TYPED}_desc-{betasmd,betasmdzscore,R2,meanvol,noiseceiling_dir-fw,noiseceiling_dir-rv,...}.nii.gz

per_video/sub-XXX/space-T1w_res-XpXmm/{fw,rv}/
  sub-XXX_space-T1w_res-XpXmm_model-TYPED_desc-NNNNbetaszscore.nii.gz   # shape (2, X, Y, Z) — two repetitions
```

## `derivatives/roi/` — ROI library (manifest-driven)

```text
MANIFEST.yaml

sub-XXX/
  space-T1w/atlas-NAME/res-XpXmm/cons-LEVEL/
    sub-XXX_[hemi-L_]space-T1w_atlas-NAME_res-XpXmm_[label-ROI_]cons-LEVEL_{mask,dseg}.nii.gz
  space-MNI/atlas-NAME/res-XpXmm/cons-LEVEL/
    sub-XXX_[hemi-L_]space-MNI_atlas-NAME_res-XpXmm_[label-ROI_]cons-LEVEL_{mask,dseg}.nii.gz
  space-fsnative/atlas-NAME/
    labels/sub-XXX_hemi-L_space-fsnative_atlas-NAME_label-ROI.label.gii
    annot/sub-XXX_hemi-L_space-fsnative_atlas-NAME.annot

group/
  space-MNI/atlas-NAME/res-XpXmm/cons-LEVEL/
    group_hemi-L_space-MNI_atlas-NAME_res-XpXmm_label-ROI_cons-LEVEL_desc-{prob_probseg,majority_mask}.nii.gz
  space-fsaverage/atlas-NAME/
    group_hemi-L_space-fsaverage_atlas-NAME_label-ROI_desc-prob.func.gii
    group_hemi-L_space-fsaverage_atlas-NAME_mpm.annot
  space-fsLR/atlas-NAME/
    group_space-fsLR_den-{32k,170k}_atlas-NAME_dlabel.nii
```

Every path is resolved through `MANIFEST.yaml`'s `path_templates`; the
access layer never hard-codes any of these strings.

## `derivatives/localizers/` — auxiliary functional-mapping outputs

```text
<localizer>/
  manifest.yaml
  sub-XXX/<localizer-specific subdirs>/
    sub-XXX_ses-<...>_..._space-T1w_res-XpXmm_..._<map>.nii.gz
```

Current: `prf/`. Planned: `fLOC/`, `time/`.

## `derivatives/stimuli/` — stimulus + annotation assets

```text
rescaled_final/NNNN_{fw,rv}.mp4              # videos
pictures/NNNN_{fw,rv}.png                    # static frames

annotations/NNNN_{fw,rv}.mp4/
  action_classification/X3D/...csv
  action_detection/slowfast_r50_detection/...{hdf5,mp4}
  captioning/GIT/...csv
  depth_estimation/MiDaS/...{hdf5,mp4}
  instance_segmentation/MaskRCNN_ResNet50_FPN/...{hdf5,mp4}
  keypoints/KeypointRCNN_ResNet50/...{hdf5,mp4}
  motion_energy/{16hz,32hz}/...npy
  object_detection/fasterrcnn_resnet50_fpn_v2/...{hdf5,mp4}
  qwen_description/...txt
  qwen_embedding/..._embedding.json
  sbert_embeddings/...npy
  semantic_segmentation/FCN_ResNet101/...{hdf5,mp4}
```

## `derivatives/anat-3T/` — anatomical reference

```text
sub-XXX/fiducial/res-XpXmm/
  sub-XXX_ses-3Tanat_T1w_FS_T2BM_crop_resampled.nii.gz   # canonical T1w reference at this EPI grid
  sub-XXX_ses-3Tanat_T2w_brain_T2BM_crop_resampled.nii.gz
  sub-XXX_FScortexGM_T2BM_crop_resampled.nii.gz          # FreeSurfer cortex GM mask (binary)
  sub-XXX_FScortexGM_dil_T2BM_crop_resampled.nii.gz      # dilated (binary)
  sub-XXX_FScortexGM_sm_T2BM_crop_resampled.nii.gz       # smoothed soft mask (float [0,1])
  ...
```

The GM masks share the affine of `space-T1w_res-XpXmm` derivatives, so
they can be used directly as voxel selectors; access via
{meth}`~AOTaccess.subject.AOTSubject.get_gray_matter_mask` or
{meth}`~AOTaccess.anatomy_access.AnatomyAccess.read_gray_matter_mask`.
