# Changelog

```{admonition} Authoring TODO
:class: note
Maintained per release. Currently pre-release; see the git log on the
`api-improvements` branch for granular history.
```

## Unreleased

- Adapted to the July/August 2026 dataset arrivals: sub-006 joined the
  cohort across bids / aot_prep / glmsingle (13 sessions), subjects
  003–008 gained ``ses-fLocDur`` localizer sessions plus completion
  sessions 11/12, and the pRF localizer store migrated to a
  ``sub-*/space-{space}/res-{resolution}`` layout with a new
  ``res-1p25mm`` grid rolling out. The hardcoded discovery test now
  expects subjects 1–8, and pRF cluster tests target subjects with
  data (skipping the fit-map reads while the fitting pipeline
  repopulates ``fits/`` — currently every fit lives in a
  ``fits_old*`` rename that no manifest template reaches).
- New condition-level localizer betas in the GLMsingle per_video store
  (``Dur`` and ``fLoc`` subdirectories next to ``fw``/``rv``) are
  readable via
  {meth}`~AOTaccess.glmsingle_access.GLMSingleAccess.read_condition_betas`,
  with {meth}`~AOTaccess.glmsingle_access.GLMSingleAccess.list_conditions`
  enumerating the verbatim desc prefixes.
- R² masking in {class}`~AOTaccess.prf_access.PrfAccess` is now NaN-fill
  in both {meth}`~AOTaccess.prf_access.PrfAccess.read_param` and
  {meth}`~AOTaccess.prf_access.PrfAccess.read_noiseceiling` (upstream had
  changed only ``read_param``, leaving docstring, tests and the
  noise-ceiling path on the old zero-fill contract). NaN keeps masked
  voxels out of downstream statistics where 0 is a valid parameter value.
- Named pRF readers ``read_srf_amplitude`` / ``read_srf_size`` cover the
  DoG (and on-disk norm) surround-ratio maps;
  {meth}`~AOTaccess.prf_access.PrfAccess.get_method_list` now reports
  them. The manifest example drops phantom ``sub-002`` and declares
  ``srf_amplitude``/``srf_size`` for ``norm`` too, matching disk.
- {class}`~AOTaccess.roi_access.ROIAccess` raises
  {class}`~AOTaccess.errors.DataNotFoundError` (instead of ``KeyError``)
  for subjects missing from the ROI library manifest — e.g. sub-006
  until the library is regenerated. Volume-mask docstrings now use the
  canonical ``T1w``/``MNI`` space labels.
- Removed ``AnatomyAccess._temp_read_crop_resampled_T1``: the 1.7 mm
  fiducial grid no longer exists on disk for any subject (anat-3T holds
  ``res-2p0mm`` and ``res-1p25mm`` for all eight subjects); use
  {meth}`~AOTaccess.anatomy_access.AnatomyAccess.read_t1w`.
- ``Config`` relative layout entries may list candidate paths;
  ``AOTdesignsettings`` now resolves on both the VU share and Snellius
  (folding in the ``snellius`` branch fix).
- {func}`~AOTaccess.brain.compute_brain_mask` is now the canonical
  brain-mask dispatcher — it picks the recipe by ``kind=``
  (``"cortex_dil"`` default, plus ``"cortex"`` / ``"cortex_sm"`` /
  ``"ncsnr"`` / ``"r2"``). The legacy single-session R² > 0 primitive
  was renamed {func}`~AOTaccess.brain.compute_r2_brain_mask` so its
  name matches what it does; the dispatcher and the renamed primitive
  read consistently when you scan ``brain.py``. Existing callers of the
  old single-session ``compute_brain_mask(sub, ses=1, ...)`` call
  signature need to swap to ``compute_r2_brain_mask`` (one rename, no
  signature change). :class:`~AOTaccess.subject.AOTSubject` delegates
  through the same name-set internally; nothing changes at the
  subject level.
- Default brain mask flipped to the dilated FreeSurfer cortex GM
  (``"cortex_dil"``, ~98 k voxels at 2 mm).
  {class}`~AOTaccess.subject.AOTSubject` now takes a ``default_mask``
  constructor argument selecting the working set:
  ``"cortex_dil"`` (default) / ``"cortex"`` / ``"cortex_sm"`` for
  anatomical masks; ``"ncsnr"`` (or ``"r2"`` as an alias) for the new
  data-driven mask. The anatomical default keeps low-R² cortex (DMN)
  in the working set without needing a custom ``mask=`` argument.
  Existing ``mask=``/``roi=`` selectors are unchanged.
- New session-averaged signal mask:
  {func}`~AOTaccess.brain.compute_ncsnr_brain_mask` reads
  ``noiseceiling_dir-{fw,rv}`` for every main-task session, averages
  across (session × direction), and thresholds. Exposed on
  {class}`~AOTaccess.subject.AOTSubject` as
  {meth}`~AOTaccess.subject.AOTSubject.get_glmsingle_ncsnr_mask`
  (cached per ``threshold``). The legacy single-session R² > 0 mask is
  still reachable as
  {meth}`~AOTaccess.subject.AOTSubject.get_glmsingle_r2_mask` (and the
  underlying {func}`~AOTaccess.brain.compute_r2_brain_mask`) for
  diagnostics.
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
