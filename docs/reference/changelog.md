# Changelog

```{admonition} Authoring TODO
:class: note
Maintained per release. Currently pre-release; see the git log on the
`api-improvements` branch for granular history.
```

## Unreleased

- Motion-energy features migrated to per-(video, direction, rate) HDF5.
  :meth:`~AOTaccess.stimulus_info_access.StimuliInfoAccess.read_motion_energy_features`
  now prefers ``.../motion_energy/{16,32}hz/NNNN_{fw,rv}.h5``
  (dataset ``/motion_energy``, shape ``(n_frames, n_filters)``, already
  log-compressed by pymoten) and transparently falls back to the legacy
  ``.npy`` with a one-time :class:`DeprecationWarning` while the conversion
  is in progress. New
  :meth:`~AOTaccess.stimulus_info_access.StimuliInfoAccess.read_motion_energy_summary`
  reads ``/motion_energy_summary`` (shape ``(n_filters,)``) — the per-video
  temporal mean of the per-frame array (Nishimoto / Gallant-lab canonical
  pooling: compress once, average over time). Raises
  :class:`~AOTaccess.errors.DataNotFoundError` until the summary dataset
  is written.
- FreeSurfer cortex gray-matter masks via
  {meth}`~AOTaccess.anatomy_access.AnatomyAccess.read_gray_matter_mask` and
  {meth}`~AOTaccess.subject.AOTSubject.get_gray_matter_mask`. Three
  variants (`"cortex"`, `"cortex_dil"`, `"cortex_sm"`); return type follows
  the variant (bool for binary, float for soft). Shares the affine with
  `space-T1w_res-XpXmm` derivatives, so it slots into `mask=` on every
  voxel-valued method without resampling.
- BIDS-compliant filename conventions adopted across the dataset:
  `space-T1w` / `space-MNI` for volumes (paired with `res-1p25mm` /
  `res-2p0mm`), `space-fsnative` / `space-fsaverage` reserved for
  surfaces. The API enforces surface vs volume labels with clear errors
  on misuse.
- Manifest-driven access for ROIs ({class}`~AOTaccess.roi_access.ROIAccess`)
  and localizers ({class}`~AOTaccess.localizer_access.LocalizerAccess`).
- {class}`~AOTaccess.subject.AOTSubject` — primary per-subject access
  object; flat-voxel ``(n_trials, n_voxels)`` API anchored by a per-subject
  brain mask; round-trip {meth}`~AOTaccess.subject.AOTSubject.to_nifti`.
- {meth}`~AOTaccess.subject.AOTSubject.get_run_betas` composes a run from
  per-video files in trial order, picking the right repetition (0 or 1)
  per trial.
- Discovery module ({mod}`AOTaccess.discovery`).
- Unified {class}`~AOTaccess.config.Config` layer; `AOT_SETTINGS` env var
  + `root_dir` mode for relocated datasets.
- Consistent error hierarchy
  ({class}`~AOTaccess.errors.AOTAccessError` family).
- `pytest` test suite (cluster-marked tests for real-data, pure-unit tests
  for path / manifest logic).
- Documentation site (this one).
